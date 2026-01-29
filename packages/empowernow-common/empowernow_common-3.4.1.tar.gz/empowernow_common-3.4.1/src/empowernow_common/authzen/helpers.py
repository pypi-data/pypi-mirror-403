"""
AuthZEN Helper Functions - Pattern B Authorization Filtering

This module provides helper functions for common authorization patterns,
particularly Pattern B (Service-First + Batch Evaluation) which is the
recommended approach for filtering large datasets.

Examples:
    # Filter a list of users to only those the subject can read
    from empowernow_common.authzen import SecureEnhancedPDP, SecureSubject
    from empowernow_common.authzen.helpers import filter_authorized
    
    users = await db.fetch_users(department="engineering")
    
    async with SecureEnhancedPDP.from_env() as pdp:
        authorized_users = await filter_authorized(
            pdp,
            users,
            SecureSubject.account(current_user.arn),
            "user",
            "read",
            id_getter=lambda u: u.arn,
        )

References:
    - AUTHZEN_SEARCH_POSTGRESQL_CLICKHOUSE_DESIGN.md (Pattern B)
    - AUTHZEN_SEARCH_DATABASE_EXPERT_GUIDE.md (Pattern B Guardrails)
    - AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md (Section 11)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar

from .models import SecureSubject, SecureResource, SecureAction, SecureContext, SecureAuthRequest
from .secure_client_v2 import SecureEnhancedPDP

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Maximum batch size for PDP evaluation (matches SDK defaults)
DEFAULT_BATCH_SIZE = 100

# Pattern B monitoring thresholds (per DBA Review Jan 2026)
# When these are exceeded, callers should consider switching to Pattern C
DENIED_RATIO_WARNING_THRESHOLD = 0.8  # 80% denied → warn
FILL_ROUNDS_WARNING_THRESHOLD = 4     # More than 4 rounds → warn
CANDIDATES_MULTIPLIER_THRESHOLD = 3   # scanned > 3x page_size → warn


# ═══════════════════════════════════════════════════════════════════════════════
# Pattern B Metrics (Per DBA Review Jan 2026)
# ═══════════════════════════════════════════════════════════════════════════════
# These metrics help detect when Pattern B is struggling and should be replaced
# with Pattern C (scope tokens / compiled predicates) for better performance.
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class PatternBMetrics:
    """
    Metrics from Pattern B batch evaluation.
    
    These metrics should be monitored to detect when Pattern B is struggling
    and should be replaced with Pattern C (scope tokens / compiled predicates).
    
    Per DBA Review (Jan 2026): Pattern B is a fallback, not a default.
    Escalate to Pattern C when:
    - denied_ratio consistently >80%
    - fill_rounds consistently hits max
    - candidates_scanned >> page_size * 3
    
    Example:
        authorized, metrics = await filter_authorized_with_metrics(
            pdp, resources, subject, "agent", "read"
        )
        
        if metrics.should_escalate_to_pattern_c:
            logger.warning(
                f"Pattern B struggling for resource_type='agent': "
                f"denied_ratio={metrics.denied_ratio:.2f}, "
                f"fill_rounds={metrics.fill_rounds}"
            )
        
        # Emit Prometheus metrics
        from prometheus_client import Histogram
        PATTERN_B_DENIED_RATIO.labels(resource_type="agent").observe(metrics.denied_ratio)
    """
    
    total_candidates: int
    """Total number of candidates evaluated."""
    
    authorized_count: int
    """Number of candidates that were authorized."""
    
    denied_count: int
    """Number of candidates that were denied."""
    
    fill_rounds: int = 1
    """Number of fetch rounds needed to fill the page (1 = no refill needed)."""
    
    batch_count: int = 1
    """Number of PDP batch calls made."""
    
    evaluation_time_ms: float = 0.0
    """Total time spent in PDP evaluation (milliseconds)."""
    
    resource_type: str = ""
    """Resource type being filtered."""
    
    action: str = ""
    """Action being performed."""
    
    @property
    def denied_ratio(self) -> float:
        """
        Ratio of denied candidates (0.0 to 1.0).
        
        High denied ratio (>0.8) indicates Pattern B is inefficient and
        Pattern C should be considered.
        """
        if self.total_candidates == 0:
            return 0.0
        return self.denied_count / self.total_candidates
    
    @property
    def authorization_rate(self) -> float:
        """Ratio of authorized candidates (1 - denied_ratio)."""
        return 1.0 - self.denied_ratio
    
    @property
    def should_warn(self) -> bool:
        """True if metrics indicate Pattern B is struggling."""
        return (
            self.denied_ratio > DENIED_RATIO_WARNING_THRESHOLD
            or self.fill_rounds > FILL_ROUNDS_WARNING_THRESHOLD
        )
    
    @property
    def should_escalate_to_pattern_c(self) -> bool:
        """
        True if Pattern B is so inefficient that Pattern C should be used.
        
        Per DBA Review (Jan 2026): Pattern B should escalate to Pattern C when:
        - Candidate set is large (>1000 rows before filtering)
        - Deny ratio consistently >80% → most work is wasted
        - fill_rounds consistently hits max → UX is degraded
        """
        return (
            self.denied_ratio > DENIED_RATIO_WARNING_THRESHOLD
            and self.fill_rounds > FILL_ROUNDS_WARNING_THRESHOLD
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_candidates": self.total_candidates,
            "authorized_count": self.authorized_count,
            "denied_count": self.denied_count,
            "denied_ratio": round(self.denied_ratio, 4),
            "authorization_rate": round(self.authorization_rate, 4),
            "fill_rounds": self.fill_rounds,
            "batch_count": self.batch_count,
            "evaluation_time_ms": round(self.evaluation_time_ms, 2),
            "resource_type": self.resource_type,
            "action": self.action,
            "should_warn": self.should_warn,
            "should_escalate_to_pattern_c": self.should_escalate_to_pattern_c,
        }
    
    def log_if_warning(self) -> None:
        """Log a warning if metrics indicate Pattern B is struggling."""
        if self.should_escalate_to_pattern_c:
            logger.warning(
                f"Pattern B struggling - consider Pattern C: "
                f"resource_type={self.resource_type}, action={self.action}, "
                f"denied_ratio={self.denied_ratio:.2f}, fill_rounds={self.fill_rounds}, "
                f"total_candidates={self.total_candidates}"
            )
        elif self.should_warn:
            logger.info(
                f"Pattern B showing stress: "
                f"resource_type={self.resource_type}, action={self.action}, "
                f"denied_ratio={self.denied_ratio:.2f}, fill_rounds={self.fill_rounds}"
            )


def _build_auth_request(
    subject: SecureSubject,
    resource_id: str,
    resource_type: str,
    properties: Dict[str, Any],
    action: str,
    context: Optional[SecureContext],
) -> SecureAuthRequest:
    """Build a SecureAuthRequest, handling optional context."""
    request_kwargs: Dict[str, Any] = {
        "subject": subject,
        "resource": SecureResource(
            id=resource_id,
            type=resource_type,
            properties=properties,
        ),
        "action": SecureAction(name=action),
    }
    if context is not None:
        request_kwargs["context"] = context
    return SecureAuthRequest(**request_kwargs)


async def filter_authorized(
    pdp: SecureEnhancedPDP,
    resources: List[T],
    subject: SecureSubject,
    resource_type: str,
    action: str = "read",
    id_getter: Callable[[T], str] = lambda x: getattr(x, "id", str(x)),
    properties_getter: Callable[[T], Dict[str, Any]] = lambda x: {},
    context: Optional[SecureContext] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> List[T]:
    """
    Filter a list of resources to only those the subject is authorized to access.
    
    Uses batch evaluation for efficiency (single PDP call per batch).
    This implements Pattern B (Service-First + Batch Evaluation) from the
    AuthZEN Search design document.
    
    Args:
        pdp: The PDP client instance (SecureEnhancedPDP)
        resources: List of resources to filter (any type)
        subject: The subject requesting access
        resource_type: Type of resources being filtered (e.g., "user", "agent")
        action: The action being performed (default: "read")
        id_getter: Function to extract ID from each resource (default: x.id)
        properties_getter: Function to extract properties for authorization context
        context: Optional additional context for authorization
        batch_size: Maximum items per batch (default: 100)
    
    Returns:
        List of resources the subject is authorized to access, preserving order
        
    Raises:
        PDPError: If PDP communication fails
        
    Example:
        # Filter users to those the current user can read
        users = await db.fetch_users(department="engineering")
        authorized = await filter_authorized(
            pdp_client,
            users,
            SecureSubject.account(current_user.arn),
            "user",
            "read",
            id_getter=lambda u: u.arn,
            properties_getter=lambda u: {"department": u.department},
        )
        
    Performance:
        - Single HTTP call per batch of 100 items
        - For 1000 items: ~10 PDP calls
        - Consider adding caching for repeated calls
    """
    if not resources:
        return []
    
    # Build batch requests
    all_requests = [
        _build_auth_request(
            subject, id_getter(resource), resource_type,
            properties_getter(resource), action, context
        )
        for resource in resources
    ]
    
    # Evaluate in batches
    permitted_ids: Set[str] = set()
    
    for i in range(0, len(all_requests), batch_size):
        batch = all_requests[i:i + batch_size]
        results = await pdp.evaluate_batch(batch)
        
        for result in results:
            if result.decision:
                permitted_ids.add(result.resource.id)
    
    # Filter to permitted, preserving order
    return [r for r in resources if id_getter(r) in permitted_ids]


async def filter_authorized_with_details(
    pdp: SecureEnhancedPDP,
    resources: List[T],
    subject: SecureSubject,
    resource_type: str,
    action: str = "read",
    id_getter: Callable[[T], str] = lambda x: getattr(x, "id", str(x)),
    properties_getter: Callable[[T], Dict[str, Any]] = lambda x: {},
    context: Optional[SecureContext] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Dict[str, Any]:
    """
    Filter resources with detailed authorization results.
    
    Similar to filter_authorized() but returns additional metadata about
    the authorization decisions, useful for debugging and audit.
    
    Args:
        pdp: The PDP client instance
        resources: List of resources to filter
        subject: The subject requesting access
        resource_type: Type of resources being filtered
        action: The action being performed
        id_getter: Function to extract ID from each resource
        properties_getter: Function to extract properties
        context: Optional additional context
        batch_size: Maximum items per batch
    
    Returns:
        Dict containing:
            - "authorized": List of authorized resources
            - "denied": List of denied resources  
            - "denied_reasons": Dict mapping resource_id to denial reason
            - "total": Total count of input resources
            - "authorized_count": Count of authorized resources
            - "denied_count": Count of denied resources
            
    Example:
        result = await filter_authorized_with_details(
            pdp, users, subject, "user", "read"
        )
        print(f"Authorized: {result['authorized_count']}/{result['total']}")
        for user_id, reason in result['denied_reasons'].items():
            print(f"  {user_id}: {reason}")
    """
    if not resources:
        return {
            "authorized": [],
            "denied": [],
            "denied_reasons": {},
            "total": 0,
            "authorized_count": 0,
            "denied_count": 0,
        }
    
    # Build batch requests
    all_requests = [
        _build_auth_request(
            subject, id_getter(resource), resource_type,
            properties_getter(resource), action, context
        )
        for resource in resources
    ]
    
    # Evaluate in batches
    authorized_ids: Set[str] = set()
    denied_reasons: Dict[str, str] = {}
    
    for i in range(0, len(all_requests), batch_size):
        batch = all_requests[i:i + batch_size]
        results = await pdp.evaluate_batch(batch)
        
        for result in results:
            if result.decision:
                authorized_ids.add(result.resource.id)
            else:
                denied_reasons[result.resource.id] = getattr(
                    result, "reason", "Access denied"
                )
    
    # Build result lists preserving order
    authorized = [r for r in resources if id_getter(r) in authorized_ids]
    denied = [r for r in resources if id_getter(r) not in authorized_ids]
    
    return {
        "authorized": authorized,
        "denied": denied,
        "denied_reasons": denied_reasons,
        "total": len(resources),
        "authorized_count": len(authorized),
        "denied_count": len(denied),
    }


async def filter_authorized_with_metrics(
    pdp: SecureEnhancedPDP,
    resources: List[T],
    subject: SecureSubject,
    resource_type: str,
    action: str = "read",
    id_getter: Callable[[T], str] = lambda x: getattr(x, "id", str(x)),
    properties_getter: Callable[[T], Dict[str, Any]] = lambda x: {},
    context: Optional[SecureContext] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Tuple[List[T], PatternBMetrics]:
    """
    Filter resources with Pattern B metrics for monitoring.
    
    Similar to filter_authorized() but returns metrics that help detect
    when Pattern B is struggling and should be replaced with Pattern C.
    
    Per DBA Review (Jan 2026): Pattern B is a FALLBACK, not a default.
    Monitor these metrics and escalate to Pattern C when:
    - denied_ratio consistently >80%
    - fill_rounds consistently hits max
    - candidates_scanned >> page_size * 3
    
    Args:
        pdp: The PDP client instance (SecureEnhancedPDP)
        resources: List of resources to filter (any type)
        subject: The subject requesting access
        resource_type: Type of resources being filtered (e.g., "user", "agent")
        action: The action being performed (default: "read")
        id_getter: Function to extract ID from each resource
        properties_getter: Function to extract properties for authorization context
        context: Optional additional context for authorization
        batch_size: Maximum items per batch (default: 100)
    
    Returns:
        Tuple of (authorized_resources, metrics)
        
    Example:
        authorized, metrics = await filter_authorized_with_metrics(
            pdp, agents, subject, "agent", "invoke"
        )
        
        # Log warning if Pattern B is struggling
        metrics.log_if_warning()
        
        # Emit to Prometheus
        PATTERN_B_DENIED_RATIO.labels(resource_type="agent").observe(metrics.denied_ratio)
        PATTERN_B_BATCH_COUNT.labels(resource_type="agent").observe(metrics.batch_count)
        
        if metrics.should_escalate_to_pattern_c:
            # File ticket to move this search to Pattern C
            logger.error(f"Pattern B consistently failing for resource_type='agent'")
    """
    if not resources:
        return [], PatternBMetrics(
            total_candidates=0,
            authorized_count=0,
            denied_count=0,
            resource_type=resource_type,
            action=action,
        )
    
    start_time = time.monotonic()
    
    # Build batch requests
    all_requests = [
        _build_auth_request(
            subject, id_getter(resource), resource_type,
            properties_getter(resource), action, context
        )
        for resource in resources
    ]
    
    # Evaluate in batches
    permitted_ids: Set[str] = set()
    batch_count = 0
    
    for i in range(0, len(all_requests), batch_size):
        batch = all_requests[i:i + batch_size]
        results = await pdp.evaluate_batch(batch)
        batch_count += 1
        
        for result in results:
            if result.decision:
                permitted_ids.add(result.resource.id)
    
    evaluation_time_ms = (time.monotonic() - start_time) * 1000
    
    # Filter to permitted, preserving order
    authorized = [r for r in resources if id_getter(r) in permitted_ids]
    
    # Build metrics
    metrics = PatternBMetrics(
        total_candidates=len(resources),
        authorized_count=len(authorized),
        denied_count=len(resources) - len(authorized),
        fill_rounds=1,  # Single pass, no refill in basic implementation
        batch_count=batch_count,
        evaluation_time_ms=evaluation_time_ms,
        resource_type=resource_type,
        action=action,
    )
    
    # Log warning if metrics indicate Pattern B is struggling
    metrics.log_if_warning()
    
    return authorized, metrics


async def can_access_any(
    pdp: SecureEnhancedPDP,
    subject: SecureSubject,
    resource_type: str,
    action: str = "read",
) -> bool:
    """
    Check if subject can access any resource of the given type.
    
    Useful for determining if a user should see a menu item or button
    before fetching the actual data.
    
    Args:
        pdp: The PDP client instance
        subject: The subject requesting access
        resource_type: Type of resources to check
        action: The action being performed
        
    Returns:
        True if subject can access at least one resource of this type
        
    Example:
        # Show "Users" menu only if user can read at least one user
        if await can_access_any(pdp, subject, "user", "read"):
            show_users_menu()
    """
    result = await pdp.search_resources(
        subject=subject,
        action=SecureAction(name=action),
        resource_type=resource_type,
        page_limit=1,  # Only need to know if at least one exists
    )
    
    return len(result.get("results", [])) > 0


async def get_accessible_ids(
    pdp: SecureEnhancedPDP,
    subject: SecureSubject,
    resource_type: str,
    action: str = "read",
    page_limit: int = 1000,
) -> List[str]:
    """
    Get list of resource IDs the subject can access.
    
    Implements Pattern A (PDP-First) from the design document.
    Useful when you need the ID list for a database query.
    
    Args:
        pdp: The PDP client instance
        subject: The subject requesting access
        resource_type: Type of resources to search
        action: The action being performed
        page_limit: Maximum IDs to return
        
    Returns:
        List of resource IDs the subject can access
        
    Warning:
        Pattern A has limitations with large datasets (>1000 IDs).
        Consider Pattern B (filter_authorized) for large datasets.
        
    Example:
        # Get agents user can access, then fetch from DB
        agent_ids = await get_accessible_ids(pdp, subject, "agent", "invoke")
        if agent_ids:
            agents = await db.fetch_agents(client_id__in=agent_ids)
    """
    result = await pdp.search_resources(
        subject=subject,
        action=SecureAction(name=action),
        resource_type=resource_type,
        page_limit=page_limit,
    )
    
    return [r.id for r in result.get("results", [])]
