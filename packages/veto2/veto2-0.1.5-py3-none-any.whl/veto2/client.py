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

    def verify(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Verifies if a tool call is allowed based on backend policy configuration.
        Returns True if allowed, Raises PermissionDeniedError if blocked.
        
        :param tool_name: Name of the tool being called
        :param parameters: Parameters being passed to the tool
        """
        safe_parameters = self._make_json_serializable(parameters)
        payload = {
            "api_key": self.api_key,
            "agent_name": self.agent_name,
            "tool_name": tool_name,
            "parameters": safe_parameters
        }
        
        try:
            resp = requests.post(f"{self.base_url}/verify", json=payload)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            log_id = data.get("log_id")
            message = data.get("message")
            plan = data.get("plan", "BASIC")  # Get plan from response
            
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
                return self._poll_for_approval(log_id, plan)
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

    def _poll_for_approval(self, log_id: str, plan: str = "BASIC") -> bool:
        """Polls the backend until status changes from PAUSE
        
        Timeout based on plan:
        - BASIC: 3 hours (10,800 seconds)
        - PRO: 7 days (604,800 seconds)
        """
        if not log_id:
             # Should not happen if backend is correct
             raise PermissionDeniedError("Action paused but no Log ID returned.")
        
        # Set timeout based on plan
        max_wait_seconds = 10800 if plan == "BASIC" else 604800  # 3 hours or 7 days
        start_time = time.time()
             
        while True:
            # Check if timeout exceeded
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                timeout_hours = max_wait_seconds / 3600
                raise PermissionDeniedError(f"Approval timeout: No response after {timeout_hours:.0f} hours.")
            
            time.sleep(5)  # Poll every 5 seconds
            try:
                resp = requests.get(f"{self.base_url}/check_status/{log_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status")
                    
                    if status == "APPROVED":
                        print("[Veto2] Action APPROVED.")
                        return True
                    elif status == "REJECTED" or status == "BLOCKED":
                        raise PermissionDeniedError("Action REJECTED by manager.")
                    elif status == "PAUSE" or status == "PENDING":
                        print(".", end="", flush=True)
                        continue
            except Exception as e:
                pass

    def check_connection(self) -> bool:
        """Checks if the backend is reachable and API key is valid."""
        try:
            # We use /verify with an empty/dummy payload to check key validity
            # since /config requires a User (not just an Org API Key)
            payload = {
                "api_key": self.api_key,
                "agent_name": "ConnectivityCheck",
                "tool_name": "ping",
                "parameters": {}
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
