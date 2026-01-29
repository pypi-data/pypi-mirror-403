import os
import time
import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from .masking import mask_pii
from .exceptions import PermissionDeniedError, ConfigurationError

CONFIG_DIR = Path.home() / ".veto"
CONFIG_FILE = CONFIG_DIR / "config.json"

def save_config(api_key: str = None, base_url: str = None):
    """Save API key and optional base URL to local config file."""
    if not api_key:
        print("Please enter your Veto API Key:")
        api_key = input("API Key: ").strip()
        
    if not api_key:
        print("Error: No API Key provided.")
        return

    config = {"api_key": api_key}
    if base_url:
        config["base_url"] = base_url

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    print(f"Credentials saved to {CONFIG_FILE}")

def load_config() -> Dict[str, str]:
    """Load config from local file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

class GovernanceClient:
    def __init__(self, api_key: str = None, base_url: str = None, agent_name: str = "DefaultAgent"):
        config = load_config()
        self.api_key = api_key or os.getenv("GOVERNANCE_API_KEY") or config.get("api_key")
        
        # Default to production URL if none provided
        production_url = "https://vetoback-production.up.railway.app/api/v1"
        self.base_url = (
            base_url or 
            os.getenv("GOVERNANCE_BASE_URL") or 
            config.get("base_url") or 
            production_url
        )
        self.agent_name = agent_name
        
        if not self.api_key:
            raise ConfigurationError("API Key is required. Run 'sdk.login()' or set GOVERNANCE_API_KEY.")

    def verify(self, tool_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Verifies if a tool call is allowed.
        Returns True if allowed, Raises PermissionDeniedError if blocked.
        """
        # 1. Mask PII locally
        masked_params = mask_pii(parameters)
        
        payload = {
            "api_key": self.api_key,
            "agent_name": self.agent_name,
            "tool_name": tool_name,
            "parameters": masked_params
        }
        
        try:
            resp = requests.post(f"{self.base_url}/verify", json=payload)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            log_id = data.get("log_id")
            
            if status == "APPROVED":
                return True
            elif status == "BLOCKED":
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

    def _poll_for_approval(self, log_id: str) -> bool:
        """Polls the backend until status changes from PAUSE"""
        if not log_id:
             # Should not happen if backend is correct
             raise PermissionDeniedError("Action paused but no Log ID returned.")
             
        while True:
            time.sleep(2) # Poll every 2 seconds
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
