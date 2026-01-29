# Veto SDK

🛡️ **Stop AI Agents from going rogue.** Add comprehensive governance and human-in-the-loop approval to your AI agents with one line of code.

## Installation

```bash
pip install veto2
```

## Quick Start

### 1. Initialize SDK

```python
import veto2 as sdk

# Initialize with your API key (get from Dashboard → Settings)
sdk.init(
    api_key="sk_live_...",
    agent_name="MyAgent"
)
```

### 2. Protect Your Functions

```python
@sdk.guard()
def delete_user(user_id):
    # Your code here
    db.delete(user_id)
    return "Deleted"

# Function is now protected by Veto governance
```

### 3. Configure Policy in Dashboard

Navigate to **Dashboard → Tools** and configure the governance mode for your function:
- 🔴 **BLOCK** - Deny execution
- 🔵 **SHADOW** - Allow but log
- 🟡 **HUMAN_APPROVAL** - Require manual approval
- 🟣 **MASKING** - Redact PII in logs
- 🟠 **FEEDBACK** - Return helpful error messages

## Policy Modes

All policy modes are configured via the Dashboard, not in code.

### 🔴 BLOCK Mode
Denies execution immediately.
```python
@sdk.guard()
def dangerous_operation():
    # Will raise PermissionDeniedError if policy is set to BLOCK
    pass
```

### 🔵 SHADOW Mode
Allows execution but logs as warning. Perfect for monitoring.
```python
@sdk.guard()
def beta_feature():
    # Executes normally, logged in Activity Feed
    pass
```

### 🟡 HUMAN_APPROVAL Mode
Pauses execution until approved via Dashboard.
```python
@sdk.guard()
def large_refund(amount):
    # SDK waits here for approval
    return f"Refunded ${amount}"
```

The SDK will:
1. Send request to backend
2. Poll every 2 seconds
3. Continue when approved
4. Raise error if rejected

### 🟣 MASKING Mode
Redacts sensitive data in logs, uses original for execution.

Configure privacy fields in Dashboard:
- Privacy fields: `email, ssn, credit_card`

```python
@sdk.guard()
def send_notification(email, message):
    # Email masked in audit logs as "***REDACTED***"
    # Original email used for actual execution
    return f"Sent to {email}"
```

### 🟠 FEEDBACK Mode
Returns helpful error message instead of just blocking.
```python
@sdk.guard()
def sensitive_operation(data):
    # Raises helpful error with guidance
    pass
```

## API Reference

### sdk.init()
Initialize the SDK with your credentials.

```python
sdk.init(
    api_key: str,              # Required: Your API key
    agent_name: str,           # Required: Agent identifier  
    base_url: str = None       # Optional: Custom backend URL
)
```

### @sdk.guard()
Decorator to protect functions with governance policies.

```python
@sdk.guard(name: str = None)

# Parameters:
# - name: Optional custom tool name (default: function name)
```

**Example:**
```python
@sdk.guard(name="user_deleter")
def delete_user(id):
    db.delete(id)
```

### sdk.ping()
Test connection to Veto backend.

```python
if sdk.ping():
    print("✅ Connected!")
else:
    print("❌ Connection failed")
```

## Dashboard Usage

### Tools Page
Configure each tool's governance mode:
1. Navigate to **Tools**
2. Find your tool (auto-discovered on first use)
3. Click **Configure**
4. Select mode and privacy fields
5. Click **Save**

### Action Center
Approve/reject pending requests:
1. Navigate to **Dashboard**
2. See pending requests in Action Center
3. Review parameters
4. Click **✅ Approve** or **❌ Reject**

### Activity Feed
Monitor all agent actions with color-coded status badges.

## Best Practices

✅ **Initialize once** at application startup, not per request  
✅ **Use descriptive names** for tools  
✅ **Set appropriate modes** for different risk levels  
✅ **Handle errors gracefully** with try/except  

## Example: Complete Application

```python
import veto2 as sdk
import os

# Initialize SDK
sdk.init(
    api_key=os.getenv("VETO_API_KEY"),
    agent_name="CustomerSupportBot"
)

# Protect sensitive operations
@sdk.guard()
def issue_refund(customer_id, amount):
    """Requires HUMAN_APPROVAL in production"""
    # Process refund
    return {"status": "success", "amount": amount}

@sdk.guard()
def send_email(email, message):
    """Uses MASKING to redact email in logs"""
    # Send email
    return f"Sent to {email}"

@sdk.guard()
def view_customer_data(customer_id):
    """SHADOW mode for monitoring"""
    # Return customer data
    return {"id": customer_id, "name": "John Doe"}

# Use functions normally
try:
    view_customer_data("123")
    send_email("user@example.com", "Hello")
    issue_refund("123", 50.00)  # Waits for approval
except sdk.PermissionDeniedError as e:
    print(f"Action blocked: {e}")
```

## Error Handling

```python
from veto2 import PermissionDeniedError

@sdk.guard()
def risky_action():
    pass

try:
    risky_action()
except PermissionDeniedError as e:
    print(f"Action blocked: {e}")
    # Handle gracefully
```

## Billing & Limits

### Basic Plan (Free)
✅ 2 distinct tools  
✅ 1,000 logs/month  
✅ All policy modes  
❌ Slack integration  

### Pro Plan
✅ Unlimited tools  
✅ Unlimited logs  
✅ Slack notifications  
✅ Priority support  

## Support

- **Documentation**: Full docs at `/docs` in Dashboard
- **Dashboard**: [veto.example.com](http://localhost:5173)
- **Email**: support@veto.example.com

---

**Built for secure AI agent deployment** | © 2026 Veto
