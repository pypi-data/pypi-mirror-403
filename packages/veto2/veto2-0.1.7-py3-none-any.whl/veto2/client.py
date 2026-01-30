import os
import time
import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from .exceptions import PermissionDeniedError, ConfigurationError



class GovernanceClient:
    def __init__(self, api_key: str = None, base_url: str = None, agent_name: str = None):
        self.api_key = api_key or os.getenv("GOVERNANCE_API_KEY")
        
        # Default to production URL if none provided
        production_url = "https://vetoback-production.up.railway.app/api/v1"
        self.base_url = (
            base_url or 
            os.getenv("GOVERNANCE_BASE_URL") or 
            production_url
        )
        self.agent_name = agent_name or os.getenv("GOVERNANCE_AGENT_NAME") or "DefaultAgent"
        
        if not self.api_key:
            raise ConfigurationError("API Key is required. Call 'sdk.init()' or set GOVERNANCE_API_KEY.")

    def verify(self, tool_name: str, parameters: Dict[str, Any], skip_logging: bool = False) -> bool:
        """
        Verifies if a tool call is allowed based on backend policy configuration.
        Returns True if allowed, Raises PermissionDeniedError if blocked.
        
        :param tool_name: Name of the tool being called
        :param parameters: Parameters being passed to the tool
        :param skip_logging: If True, tell backend not to log this call (e.g. for ping/health checks)
        """
        safe_parameters = self._make_json_serializable(parameters)
        payload = {
            "api_key": self.api_key,
            "agent_name": self.agent_name,
            "tool_name": tool_name,
            "parameters": safe_parameters,
            "skip_logging": skip_logging
        }
        
        try:
            resp = requests.post(f"{self.base_url}/verify", json=payload)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            log_id = data.get("log_id")
            message = data.get("message")
            
            if status == "APPROVED":
                return True
            elif status == "BLOCKED":
                # Check if there's a feedback message
                if message:
                    raise PermissionDeniedError(message)
                else:
                    raise PermissionDeniedError(f"Tool call '{tool_name}' was BLOCKED by policy.")
            elif status == "PAUSE":
                print(f"[Veto2] Tool '{tool_name}' triggered a PAUSE. Waiting for approval...")
                return self._poll_for_approval(log_id)
            else:
                # Fallback
                return True
                
        except requests.exceptions.RequestException as e:
            # simple fail-open or fail-closed strategy? 
            # For strict governance, fail-closed.
            print(f"[Veto2] Error contacting backend: {e}")
            raise PermissionDeniedError("Could not verify tool compliance.")

    def _make_json_serializable(self, obj: Any) -> Any:
        """Helper to ensure all parameters are JSON serializable"""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        if isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(x) for x in obj]
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        # Handle objects with to_dict or dict methods (like Pydantic v1)
        if hasattr(obj, "dict") and callable(obj.dict):
            try:
                return self._make_json_serializable(obj.dict())
            except:
                pass
        # Handle objects with model_dump (Pydantic v2)
        if hasattr(obj, "model_dump") and callable(obj.model_dump):
            try:
                return self._make_json_serializable(obj.model_dump())
            except:
                pass
        # Default fallback for objects
        return str(obj)

    def _poll_for_approval(self, log_id: str) -> bool:
        """Polls the backend until status changes from PAUSE/PENDING.
        Uses Long Polling to reduce request frequency.
        """
        if not log_id:
             raise PermissionDeniedError("Action paused but no Log ID returned.")
        
        # Max wait: 7 days (604,800 seconds)
        max_wait_seconds = 604800
        start_time = time.time()
        
        print(f"[Veto2] Waiting for approval... (Max wait: 7 days)")
             
        while True:
            # Check if total timeout exceeded
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                raise PermissionDeniedError(f"Approval timeout: No response after 7 days.")
            
            try:
                # Long Polling Request: wait up to 30s server-side
                resp = requests.get(
                    f"{self.base_url}/check_status/{log_id}", 
                    params={"wait": "true"},
                    timeout=40 # > 30s server timeout
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status")
                    
                    if status == "APPROVED":
                        print("\n[Veto2] Action APPROVED.")
                        return True
                    elif status == "REJECTED" or status == "BLOCKED":
                        raise PermissionDeniedError("\nAction REJECTED by manager.")
                    elif status == "PAUSE" or status == "PENDING":
                        # Timeout server-side (30s) reached without change
                        print(".", end="", flush=True)
                        continue
            except requests.exceptions.Timeout:
                # Read timeout, just retry
                continue
            except Exception as e:
                # Network error, wait a bit and retry
                time.sleep(5)

    def check_connection(self) -> bool:
        """Checks if the backend is reachable and API key is valid."""
        try:
            # We use /verify with an empty/dummy payload to check key validity
            # since /config requires a User (not just an Org API Key)
            payload = {
                "api_key": self.api_key,
                "agent_name": "ConnectivityCheck",
                "tool_name": "ping",
                "parameters": {},
                "skip_logging": True
            }
            resp = requests.post(f"{self.base_url}/verify", json=payload)
            if resp.status_code == 200:
                print(f"✅ Connected to Veto Backend at {self.base_url}")
                return True
            else:
                print(f"❌ Connected, but auth failed (Status: {resp.status_code})")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to Veto Backend at {self.base_url}: {e}")
            return False
