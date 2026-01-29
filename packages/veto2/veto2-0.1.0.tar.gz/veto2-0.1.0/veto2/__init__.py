from .decorator import guard, init, ping
from .client import save_config
from .exceptions import GovernanceError, PermissionDeniedError

# Alias for user convenience
login = save_config

__all__ = ["guard", "init", "login", "ping", "GovernanceError", "PermissionDeniedError"]
