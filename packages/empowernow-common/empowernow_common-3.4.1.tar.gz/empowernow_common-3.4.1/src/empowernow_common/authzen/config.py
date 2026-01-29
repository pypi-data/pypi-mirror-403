"""
PDP Configuration for AuthZEN Client.

Pydantic Settings-based configuration for the Policy Decision Point (PDP) client.
Follows patterns from membership service and AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md.

Environment Variables:
    PDP_BASE_URL: Base URL for the PDP service (default: http://pdp:8080)
    PDP_TOKEN_URL: OAuth token endpoint URL
    PDP_CLIENT_ID: OAuth client ID
    PDP_CLIENT_SECRET: OAuth client secret
    PDP_TOKEN_SCOPE: OAuth scope (default: pdp:authorize)
    PDP_TOKEN_RESOURCE: RFC 8707 resource indicator
    PDP_TOKEN_AUTH_METHOD: Auth method (client_secret_post or private_key_jwt)
    
    PDP_ENDPOINT_EVALUATION: Single evaluation endpoint (default: /access/v1/evaluation)
    PDP_ENDPOINT_BATCH: Batch evaluation endpoint (default: /access/v1/evaluations)
    PDP_ENDPOINT_SEARCH_ACTIONS: Search actions endpoint
    PDP_ENDPOINT_SEARCH_SUBJECTS: Search subjects endpoint
    PDP_ENDPOINT_SEARCH_RESOURCES: Search resources endpoint
    
    PDP_CACHE_ENABLED: Enable caching (default: true)
    PDP_CACHE_BACKEND: Cache backend - memory or redis (default: memory)
    PDP_CACHE_TTL_ALLOW: TTL for allow decisions in seconds (default: 300)
    PDP_CACHE_TTL_DENY: TTL for deny decisions in seconds (default: 60)
    PDP_CACHE_KEY_PREFIX: Cache key prefix (default: pdp:decision:)
    
    PDP_MAX_INFLIGHT: Max concurrent requests (default: 50)
    PDP_CIRCUIT_ENABLED: Enable circuit breaker (default: true)
    PDP_CIRCUIT_FAILURE_THRESHOLD: Failures before opening (default: 5)
    PDP_CIRCUIT_RESET_TIMEOUT: Seconds before half-open (default: 30)
    PDP_CIRCUIT_WINDOW_SECONDS: Sliding window for failures (default: 60)
    
    PDP_REQUEST_TIMEOUT: Request timeout in seconds (default: 30)
    PDP_CONNECT_TIMEOUT: Connection timeout in seconds (default: 5)
    PDP_VALIDATE_SSL: Validate SSL certificates (default: true)
    
    PDP_CLIENT_ASSERTION_KEY_PATH: Path to private key for private_key_jwt
    PDP_CLIENT_ASSERTION_KID: Key ID for JWT assertions
    PDP_CLIENT_ASSERTION_ALG: Algorithm for JWT signing (default: RS256)
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class PDPEndpointsConfig(BaseModel):
    """PDP API endpoint paths - AuthZEN 1.0 compliant."""
    
    evaluation: str = Field(
        default="/access/v1/evaluation",
        description="Single evaluation endpoint (AuthZEN 1.0 Section 6.1)"
    )
    batch: str = Field(
        default="/access/v1/evaluations",
        description="Batch evaluation endpoint (AuthZEN 1.0 Section 6.2)"
    )
    search_actions: str = Field(
        default="/access/v1/search/actions",
        description="Search available actions endpoint"
    )
    search_subjects: str = Field(
        default="/access/v1/search/subjects",
        description="Search subjects endpoint"
    )
    search_resources: str = Field(
        default="/access/v1/search/resources",
        description="Search resources endpoint"
    )


class PDPConnectionConfig(BaseModel):
    """Connection settings for PDP service."""
    
    base_url: str = Field(
        default="http://pdp:8080",
        description="Base URL for the PDP service"
    )
    token_url: str = Field(
        default="",
        description="OAuth token endpoint URL"
    )
    client_id: str = Field(
        default="",
        description="OAuth client ID for PDP authentication"
    )
    client_secret: str = Field(
        default="",
        description="OAuth client secret for PDP authentication"
    )
    scope: str = Field(
        default="pdp:authorize",
        description="OAuth scope"
    )
    resource: Optional[str] = Field(
        default=None,
        description="RFC 8707 resource indicator"
    )
    token_auth_method: str = Field(
        default="client_secret_post",
        description="Token auth method: client_secret_post or private_key_jwt"
    )
    request_timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds"
    )
    connect_timeout: float = Field(
        default=5.0,
        description="Connection timeout in seconds"
    )
    validate_ssl: bool = Field(
        default=True,
        description="Validate SSL certificates"
    )
    # Connection pooling (Issue #7)
    max_connections: int = Field(
        default=100,
        description="Maximum number of connections in pool"
    )
    max_keepalive_connections: int = Field(
        default=20,
        description="Maximum keepalive connections"
    )
    keepalive_expiry: float = Field(
        default=30.0,
        description="Keepalive connection expiry in seconds"
    )
    # DPoP support (Issue #12)
    dpop_enabled: bool = Field(
        default=False,
        description="Enable DPoP for enhanced security"
    )


class PDPCacheConfig(BaseModel):
    """Cache configuration for PDP decisions."""
    
    enabled: bool = Field(
        default=True,
        description="Enable/disable PDP decision caching"
    )
    backend: str = Field(
        default="memory",
        description="Cache backend: memory or redis"
    )
    ttl_allow: int = Field(
        default=300,
        description="TTL in seconds for allow decisions (5 min)"
    )
    ttl_deny: int = Field(
        default=60,
        description="TTL in seconds for deny decisions (1 min)"
    )
    key_prefix: str = Field(
        default="pdp:decision:",
        description="Cache key prefix for PDP decisions"
    )


class PDPCircuitBreakerConfig(BaseModel):
    """Circuit breaker settings for PDP calls."""
    
    enabled: bool = Field(
        default=True,
        description="Enable circuit breaker for PDP calls"
    )
    failure_threshold: int = Field(
        default=5,
        description="Number of failures before opening circuit"
    )
    reset_timeout: float = Field(
        default=30.0,
        description="Seconds to wait before attempting reset"
    )
    window_seconds: float = Field(
        default=60.0,
        description="Sliding window for counting failures"
    )


class PDPRetryConfig(BaseModel):
    """Retry settings for PDP calls (Issue #8)."""
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries"
    )
    backoff_ms: int = Field(
        default=200,
        description="Initial backoff in milliseconds"
    )
    backoff_multiplier: float = Field(
        default=2.0,
        description="Backoff multiplier for exponential backoff"
    )
    max_backoff_ms: int = Field(
        default=5000,
        description="Maximum backoff in milliseconds"
    )


class PDPRateLimitConfig(BaseModel):
    """Rate limiting settings for PDP calls."""
    
    max_inflight: int = Field(
        default=50,
        description="Maximum concurrent PDP requests"
    )


class PDPPrivateKeyJWTConfig(BaseModel):
    """Configuration for private_key_jwt authentication."""
    
    key_path: Optional[str] = Field(
        default=None,
        description="Path to private key PEM file"
    )
    kid: Optional[str] = Field(
        default=None,
        description="Key ID for JWT header"
    )
    alg: str = Field(
        default="RS256",
        description="Signing algorithm"
    )


class PDPConstraintsConfig(BaseModel):
    """Advanced PEP constraint settings."""
    
    enabled: bool = Field(
        default=True,
        description="Enable constraint processing"
    )
    apply_automatically: bool = Field(
        default=True,
        description="Auto-apply constraints to requests"
    )
    strict_enforcement: bool = Field(
        default=True,
        description="Fail on constraint violations"
    )


class PDPObligationsConfig(BaseModel):
    """Advanced PEP obligation settings."""
    
    enabled: bool = Field(
        default=True,
        description="Enable obligation processing"
    )
    process_automatically: bool = Field(
        default=True,
        description="Auto-process obligations"
    )
    timeout: float = Field(
        default=30.0,
        description="Obligation processing timeout"
    )
    critical_retry_count: int = Field(
        default=3,
        description="Retry count for critical obligations"
    )


class PDPConfig(BaseSettings):
    """
    Complete PDP configuration with Pydantic Settings.
    
    Environment variables override defaults using PDP_ prefix.
    Nested configs use double underscore, e.g., PDP_CONNECTION__BASE_URL.
    
    Example:
        config = PDPConfig()  # Loads from environment
        config = PDPConfig(connection={"base_url": "http://localhost:8080"})
    """
    
    connection: PDPConnectionConfig = Field(default_factory=PDPConnectionConfig)
    endpoints: PDPEndpointsConfig = Field(default_factory=PDPEndpointsConfig)
    cache: PDPCacheConfig = Field(default_factory=PDPCacheConfig)
    circuit_breaker: PDPCircuitBreakerConfig = Field(default_factory=PDPCircuitBreakerConfig)
    retry: PDPRetryConfig = Field(default_factory=PDPRetryConfig)
    rate_limit: PDPRateLimitConfig = Field(default_factory=PDPRateLimitConfig)
    private_key_jwt: PDPPrivateKeyJWTConfig = Field(default_factory=PDPPrivateKeyJWTConfig)
    constraints: PDPConstraintsConfig = Field(default_factory=PDPConstraintsConfig)
    obligations: PDPObligationsConfig = Field(default_factory=PDPObligationsConfig)
    
    # Default application for policy scoping (Issue #3)
    default_application: Optional[str] = Field(
        default=None,
        description="Default pdp_application for policy scoping"
    )
    
    # Observability
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=False, description="Enable OpenTelemetry tracing")
    correlation_header: str = Field(default="X-Correlation-ID", description="Correlation ID header")
    
    class Config:
        env_prefix = "PDP_"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from flat environment variables for backward compatibility."""
        # Connection settings
        if url := os.getenv("PDP_BASE_URL") or os.getenv("PDP_URL"):
            if "/authorize" in url:
                self.connection.base_url = url.rsplit("/authorize", 1)[0]
            else:
                self.connection.base_url = url.rstrip("/")
        
        if token_url := os.getenv("PDP_TOKEN_URL"):
            self.connection.token_url = token_url
        
        if client_id := os.getenv("PDP_CLIENT_ID"):
            self.connection.client_id = client_id
        
        if client_secret := os.getenv("PDP_CLIENT_SECRET"):
            self.connection.client_secret = client_secret
        
        if scope := os.getenv("PDP_TOKEN_SCOPE"):
            self.connection.scope = scope
        
        if resource := os.getenv("PDP_TOKEN_RESOURCE") or os.getenv("PDP_TOKEN_AUDIENCE"):
            self.connection.resource = resource
        
        if auth_method := os.getenv("PDP_TOKEN_AUTH_METHOD"):
            self.connection.token_auth_method = auth_method.strip().lower()
        
        if timeout := os.getenv("PDP_REQUEST_TIMEOUT") or os.getenv("PDP_TIMEOUT"):
            self.connection.request_timeout = float(timeout)
        
        if connect_timeout := os.getenv("PDP_CONNECT_TIMEOUT"):
            self.connection.connect_timeout = float(connect_timeout)
        
        if validate_ssl := os.getenv("PDP_VALIDATE_SSL"):
            self.connection.validate_ssl = validate_ssl.lower() in ("true", "1", "yes")
        
        # Endpoint settings
        if endpoint := os.getenv("PDP_ENDPOINT_EVALUATION") or os.getenv("PDP_ENDPOINT_SINGLE"):
            self.endpoints.evaluation = endpoint
        
        if endpoint := os.getenv("PDP_ENDPOINT_BATCH") or os.getenv("PDP_ENDPOINT_EVALUATIONS"):
            self.endpoints.batch = endpoint
        
        if endpoint := os.getenv("PDP_ENDPOINT_SEARCH_ACTIONS"):
            self.endpoints.search_actions = endpoint
        
        if endpoint := os.getenv("PDP_ENDPOINT_SEARCH_SUBJECTS"):
            self.endpoints.search_subjects = endpoint
        
        if endpoint := os.getenv("PDP_ENDPOINT_SEARCH_RESOURCES"):
            self.endpoints.search_resources = endpoint
        
        # Cache settings
        if cache_enabled := os.getenv("PDP_CACHE_ENABLED"):
            self.cache.enabled = cache_enabled.lower() in ("true", "1", "yes")
        
        if cache_backend := os.getenv("PDP_CACHE_BACKEND"):
            self.cache.backend = cache_backend.lower()
        
        if ttl_allow := os.getenv("PDP_CACHE_TTL_ALLOW"):
            self.cache.ttl_allow = int(ttl_allow)
        
        if ttl_deny := os.getenv("PDP_CACHE_TTL_DENY"):
            self.cache.ttl_deny = int(ttl_deny)
        
        if prefix := os.getenv("PDP_CACHE_KEY_PREFIX"):
            self.cache.key_prefix = prefix
        
        # Rate limit settings
        if max_inflight := os.getenv("PDP_MAX_INFLIGHT"):
            self.rate_limit.max_inflight = int(max_inflight)
        
        # Circuit breaker settings
        if enabled := os.getenv("PDP_CIRCUIT_ENABLED"):
            self.circuit_breaker.enabled = enabled.lower() in ("true", "1", "yes")
        
        if threshold := os.getenv("PDP_CIRCUIT_FAILURE_THRESHOLD"):
            self.circuit_breaker.failure_threshold = int(threshold)
        
        if timeout := os.getenv("PDP_CIRCUIT_RESET_TIMEOUT"):
            self.circuit_breaker.reset_timeout = float(timeout)
        
        if window := os.getenv("PDP_CIRCUIT_WINDOW_SECONDS"):
            self.circuit_breaker.window_seconds = float(window)
        
        # Private key JWT settings
        if key_path := os.getenv("PDP_CLIENT_ASSERTION_KEY_PATH"):
            self.private_key_jwt.key_path = key_path
        
        if kid := os.getenv("PDP_CLIENT_ASSERTION_KID"):
            self.private_key_jwt.kid = kid
        
        if alg := os.getenv("PDP_CLIENT_ASSERTION_ALG"):
            self.private_key_jwt.alg = alg
        
        # Connection pooling (Issue #7)
        if max_conn := os.getenv("PDP_MAX_CONNECTIONS"):
            self.connection.max_connections = int(max_conn)
        
        if max_keepalive := os.getenv("PDP_MAX_KEEPALIVE_CONNECTIONS"):
            self.connection.max_keepalive_connections = int(max_keepalive)
        
        if keepalive_expiry := os.getenv("PDP_KEEPALIVE_EXPIRY"):
            self.connection.keepalive_expiry = float(keepalive_expiry)
        
        # DPoP (Issue #12)
        if dpop := os.getenv("PDP_DPOP_ENABLED"):
            self.connection.dpop_enabled = dpop.lower() in ("true", "1", "yes")
        
        # Retry settings (Issue #8)
        if max_retries := os.getenv("PDP_CLIENT_MAX_RETRIES"):
            self.retry.max_retries = int(max_retries)
        
        if backoff := os.getenv("PDP_CLIENT_RETRY_BACKOFF_MS"):
            self.retry.backoff_ms = int(backoff)
        
        # Default application (Issue #3)
        if app := os.getenv("PDP_DEFAULT_APPLICATION"):
            self.default_application = app
        
        # Observability
        if metrics := os.getenv("PDP_ENABLE_METRICS"):
            self.enable_metrics = metrics.lower() in ("true", "1", "yes")
        
        if tracing := os.getenv("PDP_ENABLE_TRACING"):
            self.enable_tracing = tracing.lower() in ("true", "1", "yes")


# Singleton instance
_pdp_config: Optional[PDPConfig] = None


def get_pdp_config() -> PDPConfig:
    """Get the PDP configuration singleton."""
    global _pdp_config
    if _pdp_config is None:
        _pdp_config = PDPConfig()
    return _pdp_config


def reset_pdp_config() -> None:
    """Reset the PDP configuration singleton (for testing)."""
    global _pdp_config
    _pdp_config = None
