class GovernanceError(Exception):
    """Base exception for GovernanceGuard SDK"""
    pass

class PermissionDeniedError(GovernanceError):
    """Raised when a tool call is blocked by policy"""
    pass

class ConfigurationError(GovernanceError):
    """Raised when SDK is not configured properly (e.g. missing API key)"""
    pass
