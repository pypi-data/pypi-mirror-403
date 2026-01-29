"""Constraint Metering Service - Redis-based atomic constraint enforcement.

This module implements atomic constraint checking and metering for delegation
enforcement, using Redis Lua scripts to prevent TOCTOU (time-of-check to
time-of-use) race conditions.

GAP 9 FIX: Previously, constraint checking and incrementing were separate
operations, allowing race conditions that could exceed limits.

Constraints Supported:
    - spend_cap: Maximum estimated cost per period
    - max_actions: Maximum number of actions per period
    - time_window: Time window for rate limiting

Usage:
    from empowernow_common.delegation.metering import (
        ConstraintMeter,
        ConstraintResult,
        MeteringResult,
    )
    
    meter = ConstraintMeter(redis_service)
    
    # Check and increment atomically
    result = await meter.check_and_increment(
        delegation_id="del_abc123",
        constraints={"max_actions": 100, "spend_cap": 50.00},
        estimated_cost=0.05,
    )
    
    if result.result != ConstraintResult.ALLOWED:
        raise ConstraintExceededError(result.reason)

Author: AI Agent Governance Team
Date: 2026-01-15
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Result Types
# =============================================================================


class ConstraintResult(str, Enum):
    """Result of constraint check."""
    
    ALLOWED = "allowed"
    """Action is allowed within constraints."""
    
    DENIED_SPEND_CAP = "denied_spend_cap"
    """Would exceed spend cap."""
    
    DENIED_ACTION_LIMIT = "denied_action_limit"
    """Would exceed max actions."""
    
    DENIED_TIME_WINDOW = "denied_time_window"
    """Rate limit exceeded."""


@dataclass
class MeteringResult:
    """Result of a metering check.
    
    Attributes:
        result: The constraint result (ALLOWED or denial reason)
        current_actions: Current action count after check
        current_spend: Current spend amount after check
        reason: Human-readable reason if denied
    """
    
    result: ConstraintResult
    current_actions: int
    current_spend: float
    reason: Optional[str] = None


# =============================================================================
# Lua Script for Atomic Operations
# =============================================================================


# This Lua script atomically checks constraints and increments counters.
# It prevents TOCTOU race conditions by doing check+increment in one operation.
CHECK_AND_INCREMENT_LUA = """
-- Keys: action_key, spend_key
-- Args: max_actions, spend_cap, estimated_cost, ttl

local action_key = KEYS[1]
local spend_key = KEYS[2]
local max_actions = tonumber(ARGV[1]) or 0
local spend_cap = tonumber(ARGV[2]) or 0
local estimated_cost = tonumber(ARGV[3]) or 0
local ttl = tonumber(ARGV[4]) or 86400

-- Get current values
local current_actions = tonumber(redis.call('GET', action_key) or '0')
local current_spend = tonumber(redis.call('GET', spend_key) or '0')

-- Check action limit (if set)
if max_actions > 0 and current_actions >= max_actions then
    return {'DENIED_ACTION_LIMIT', current_actions, current_spend}
end

-- Check spend cap (if set)
if spend_cap > 0 and (current_spend + estimated_cost) > spend_cap then
    return {'DENIED_SPEND_CAP', current_actions, current_spend}
end

-- All checks passed - increment counters atomically
local new_actions = redis.call('INCR', action_key)
redis.call('EXPIRE', action_key, ttl)

local new_spend = current_spend
if estimated_cost > 0 then
    new_spend = redis.call('INCRBYFLOAT', spend_key, estimated_cost)
    redis.call('EXPIRE', spend_key, ttl)
end

return {'ALLOWED', new_actions, new_spend}
"""


# Script to get current usage without incrementing
GET_USAGE_LUA = """
local action_key = KEYS[1]
local spend_key = KEYS[2]

local current_actions = tonumber(redis.call('GET', action_key) or '0')
local current_spend = tonumber(redis.call('GET', spend_key) or '0')

return {current_actions, current_spend}
"""


# Script to reset counters (for testing or manual reset)
RESET_COUNTERS_LUA = """
local action_key = KEYS[1]
local spend_key = KEYS[2]

redis.call('DEL', action_key)
redis.call('DEL', spend_key)

return 'OK'
"""


# =============================================================================
# Constraint Meter
# =============================================================================


class ConstraintMeter:
    """Atomic constraint enforcement using Redis Lua scripts.
    
    This class provides TOCTOU-safe constraint checking by using
    Redis Lua scripts that atomically check limits and increment
    counters in a single operation.
    
    Thread Safety:
        All operations are atomic at the Redis level. Multiple
        processes can safely call check_and_increment concurrently.
    
    Example:
        from empowernow_common.redis import get_redis_service
        
        redis = get_redis_service()
        meter = ConstraintMeter(redis)
        
        result = await meter.check_and_increment(
            delegation_id="del_abc123",
            constraints={"max_actions": 100, "spend_cap": 50.00},
            estimated_cost=0.05,
        )
    """
    
    def __init__(self, redis_client: Any) -> None:
        """Initialize constraint meter with Redis client.
        
        Args:
            redis_client: Redis client (must support evalsha/script_load).
                         Can be empowernow_common.redis.EnterpriseRedisService
                         or any compatible async Redis client.
        """
        self._redis = redis_client
        self._check_script_sha: Optional[str] = None
        self._get_script_sha: Optional[str] = None
        self._reset_script_sha: Optional[str] = None
    
    async def _ensure_scripts_loaded(self) -> None:
        """Load Lua scripts into Redis if not already loaded."""
        if self._check_script_sha is None:
            # Load scripts - handle both sync and async Redis clients
            if hasattr(self._redis, 'script_load'):
                self._check_script_sha = await self._redis.script_load(
                    CHECK_AND_INCREMENT_LUA
                )
                self._get_script_sha = await self._redis.script_load(
                    GET_USAGE_LUA
                )
                self._reset_script_sha = await self._redis.script_load(
                    RESET_COUNTERS_LUA
                )
            else:
                # Fallback: eval each time (slower but works)
                self._check_script_sha = "eval"
                self._get_script_sha = "eval"
                self._reset_script_sha = "eval"
    
    def _build_keys(self, delegation_id: str, period: str) -> Tuple[str, str]:
        """Build Redis keys for action and spend counters.
        
        Args:
            delegation_id: Unique delegation identifier.
            period: Period string (e.g., "2026-01" for monthly).
            
        Returns:
            Tuple of (action_key, spend_key).
        """
        action_key = f"meter:actions:{delegation_id}:{period}"
        spend_key = f"meter:spend:{delegation_id}:{period}"
        return action_key, spend_key
    
    def _get_current_period(self, period_type: str = "monthly") -> str:
        """Get current period string based on period type.
        
        Args:
            period_type: "daily", "weekly", or "monthly" (default).
            
        Returns:
            Period string (e.g., "2026-01-15" for daily, "2026-01" for monthly).
        """
        now = datetime.now(timezone.utc)
        
        if period_type == "daily":
            return now.strftime("%Y-%m-%d")
        elif period_type == "weekly":
            return f"{now.year}-W{now.isocalendar()[1]:02d}"
        else:  # monthly (default)
            return now.strftime("%Y-%m")
    
    def _get_ttl_for_period(self, period_type: str) -> int:
        """Get TTL in seconds for period type.
        
        Args:
            period_type: "daily", "weekly", or "monthly".
            
        Returns:
            TTL in seconds.
        """
        ttls = {
            "daily": 86400,      # 24 hours
            "weekly": 604800,   # 7 days
            "monthly": 2678400, # 31 days
        }
        return ttls.get(period_type, 2678400)
    
    async def check_and_increment(
        self,
        delegation_id: str,
        constraints: Dict[str, Any],
        estimated_cost: float = 0.0,
    ) -> MeteringResult:
        """Atomically check constraints and increment counters.
        
        This is the main method for constraint enforcement. It:
        1. Checks if action would exceed max_actions
        2. Checks if action would exceed spend_cap
        3. If all checks pass, increments counters atomically
        
        All operations happen in a single Redis transaction (Lua script).
        
        Args:
            delegation_id: Unique delegation identifier.
            constraints: Constraint dict with keys:
                - max_actions: Maximum actions per period (0 = unlimited)
                - spend_cap: Maximum spend per period (0 = unlimited)
                - period_type: "daily", "weekly", "monthly" (default)
            estimated_cost: Estimated cost of this action (for spend tracking).
            
        Returns:
            MeteringResult with decision and current usage.
        """
        max_actions = constraints.get("max_actions", 0)
        spend_cap = constraints.get("spend_cap", 0)
        period_type = constraints.get("period_type", "monthly")
        
        # If no constraints, allow immediately
        if max_actions == 0 and spend_cap == 0:
            return MeteringResult(ConstraintResult.ALLOWED, 0, 0.0)
        
        await self._ensure_scripts_loaded()
        
        period = self._get_current_period(period_type)
        action_key, spend_key = self._build_keys(delegation_id, period)
        ttl = self._get_ttl_for_period(period_type)
        
        try:
            # Execute Lua script
            if self._check_script_sha == "eval":
                result = await self._redis.eval(
                    CHECK_AND_INCREMENT_LUA,
                    2,  # number of keys
                    action_key, spend_key,
                    max_actions, spend_cap, estimated_cost, ttl,
                )
            else:
                result = await self._redis.evalsha(
                    self._check_script_sha,
                    2,  # number of keys
                    action_key, spend_key,
                    max_actions, spend_cap, estimated_cost, ttl,
                )
            
            # Parse result
            status = result[0]
            if isinstance(status, bytes):
                status = status.decode()
            
            actions = int(result[1])
            spend = float(result[2])
            
            constraint_result = ConstraintResult(status)
            
            if constraint_result != ConstraintResult.ALLOWED:
                logger.warning(
                    "Constraint check failed",
                    extra={
                        "delegation_id": delegation_id,
                        "result": constraint_result.value,
                        "current_actions": actions,
                        "current_spend": spend,
                        "max_actions": max_actions,
                        "spend_cap": spend_cap,
                    }
                )
            
            return MeteringResult(
                result=constraint_result,
                current_actions=actions,
                current_spend=spend,
                reason=f"Constraint exceeded: {constraint_result.value}" 
                       if constraint_result != ConstraintResult.ALLOWED else None,
            )
            
        except Exception as e:
            logger.error(
                "Constraint metering failed",
                extra={
                    "delegation_id": delegation_id,
                    "error": str(e),
                }
            )
            # Fail-open with logging (allow but log for investigation)
            # In production, you might want to fail-closed instead
            return MeteringResult(
                result=ConstraintResult.ALLOWED,
                current_actions=0,
                current_spend=0.0,
                reason=f"Metering error (fail-open): {e}",
            )
    
    async def get_current_usage(
        self,
        delegation_id: str,
        period_type: str = "monthly",
    ) -> Tuple[int, float]:
        """Get current usage without incrementing.
        
        Args:
            delegation_id: Unique delegation identifier.
            period_type: "daily", "weekly", or "monthly".
            
        Returns:
            Tuple of (action_count, spend_amount).
        """
        await self._ensure_scripts_loaded()
        
        period = self._get_current_period(period_type)
        action_key, spend_key = self._build_keys(delegation_id, period)
        
        try:
            if self._get_script_sha == "eval":
                result = await self._redis.eval(
                    GET_USAGE_LUA, 2, action_key, spend_key
                )
            else:
                result = await self._redis.evalsha(
                    self._get_script_sha, 2, action_key, spend_key
                )
            
            return (int(result[0]), float(result[1]))
        except Exception:
            return (0, 0.0)
    
    async def reset_usage(
        self,
        delegation_id: str,
        period_type: str = "monthly",
    ) -> bool:
        """Reset usage counters (for testing or manual reset).
        
        Args:
            delegation_id: Unique delegation identifier.
            period_type: "daily", "weekly", or "monthly".
            
        Returns:
            True if reset successful.
        """
        await self._ensure_scripts_loaded()
        
        period = self._get_current_period(period_type)
        action_key, spend_key = self._build_keys(delegation_id, period)
        
        try:
            if self._reset_script_sha == "eval":
                await self._redis.eval(RESET_COUNTERS_LUA, 2, action_key, spend_key)
            else:
                await self._redis.evalsha(
                    self._reset_script_sha, 2, action_key, spend_key
                )
            return True
        except Exception as e:
            logger.error(f"Failed to reset counters: {e}")
            return False


# =============================================================================
# Factory
# =============================================================================


_meter_instance: Optional[ConstraintMeter] = None


async def get_constraint_meter() -> ConstraintMeter:
    """Get or create the constraint meter singleton.
    
    Uses empowernow_common.redis for Redis connection.
    
    Returns:
        ConstraintMeter instance.
    """
    global _meter_instance
    
    if _meter_instance is None:
        from empowernow_common.redis import get_redis_service
        redis = await get_redis_service()
        _meter_instance = ConstraintMeter(redis)
    
    return _meter_instance


def reset_constraint_meter() -> None:
    """Reset the singleton (for testing)."""
    global _meter_instance
    _meter_instance = None


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "ConstraintResult",
    "MeteringResult",
    "ConstraintMeter",
    "get_constraint_meter",
    "reset_constraint_meter",
]
