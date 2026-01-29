# Veto2 SDK (veto2)

🛡️ **Stop AI Agents from going rogue.** Add strict access control and human-in-the-loop approval to your AI agents with one line of code.

## Installation

```bash
pip install veto2
```

## Quick Start

### 1. Login
First, set up your credentials. This will save your API key locally.

```python
import veto2

veto2.login() # Follow the prompt to enter your API key
```

### 2. Protect Your Tools
Wrap any sensitive function (tool) with the `@veto2.guard()` decorator.

```python
import veto2

@veto2.guard(name="delete_database")
def delete_everything():
    # This logic will only execute if APPROVED in the Veto dashboard
    db.drop_all()
    return "Action performed"

# When called, this will verify with the backend
delete_everything()
```

## How it Works

- **Interception**: The SDK intercepts the function call before it executes.
- **Verification**: It sends the tool name and (masked) parameters to the Veto backend.
- **Decision**: 
    - `APPROVED`: Function executes normally.
    - `BLOCKED`: Raises `PermissionDeniedError`.
    - `PAUSE`: The SDK polls until a human manager approves/rejects the action via the dashboard.

## Security & Privacy
Veto2 automatically masks potential PII (like emails) locally before sending any data to our servers.

---
For more information, visit [Veto](https://vetoback-production.up.railway.app).
