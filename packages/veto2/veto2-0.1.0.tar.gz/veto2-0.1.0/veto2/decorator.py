import functools
import inspect
from typing import Optional
from .client import GovernanceClient

# Global client instance
_client: Optional[GovernanceClient] = None

def init(api_key: str, agent_name: str = "DefaultAgent", base_url: str = None):
    """Initialize the global Veto2 client."""
    global _client
    _client = GovernanceClient(api_key=api_key, agent_name=agent_name, base_url=base_url)

def _get_client():
    global _client
    if _client is None:
        # Try to init from env vars
        try:
            _client = GovernanceClient()
        except:
            raise RuntimeError("Veto2 SDK not initialized. Call sdk.init(), sdk.login(), or set GOVERNANCE_API_KEY.")
    return _client

def ping() -> bool:
    """Check connection to the Veto backend."""
    try:
        return _get_client().check_connection()
    except RuntimeError:
        print("SDK not initialized. Please call sdk.init() first.")
        return False

def guard(name: str = None):
    """
    Decorator to intercept tool calls and verify them against the policy.
    
    :param name: Optional custom tool name. If None, uses function name.
    """
    def decorator(func):
        tool_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Capture arguments
            # We want to enable name-based argument masking, so let's try to bind args to signature
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                parameters = bound_args.arguments
            except ValueError:
                # Fallback if signature fails (e.g. C extension)
                parameters = {"args": args, "kwargs": kwargs}
            
            # 2. Verify with Backend
            client = _get_client()
            client.verify(tool_name=tool_name, parameters=parameters)
            
            # 3. Execute original function if allowed
            return func(*args, **kwargs)
            
        return wrapper
    return decorator
