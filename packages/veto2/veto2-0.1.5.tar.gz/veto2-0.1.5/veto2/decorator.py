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
    Decorator to intercept tool calls and verify them against the governance policy.
    
    Policy modes (configured via Dashboard):
    - BLOCK: Deny execution
    - SHADOW: Allow but log as warning
    - HUMAN_APPROVAL: Pause and wait for manual approval
    - MASKING: Redact PII from logs (execution uses original data)
    - FEEDBACK: Return helpful error message
    
    :param name: Optional custom tool name. If None, uses function name.
    """
    def decorator(func):
        tool_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Capture arguments
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                parameters = bound_args.arguments
            except ValueError:
                parameters = {"args": args, "kwargs": kwargs}
            
            # 2. Verify with Backend
            client = _get_client()
            client.verify(tool_name=tool_name, parameters=parameters)
            
            # 3. Execute original function if allowed
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 1. Capture arguments
            try:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                parameters = bound_args.arguments
            except ValueError:
                parameters = {"args": args, "kwargs": kwargs}
            
            # 2. Verify with Backend
            client = _get_client()
            # Note: verify is synchronous (using requests), which blocks the event loop briefly.
            # In a production async SDK, we should use httpx or run_in_executor.
            # For now, we accept the small blocking overhead or run it in executor if desired.
            client.verify(tool_name=tool_name, parameters=parameters)
            
            # 3. Execute original async function
            return await func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    return decorator
