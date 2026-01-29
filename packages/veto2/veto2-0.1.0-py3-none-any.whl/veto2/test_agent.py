import os
import sys

# Add parent dir to path to import sdk
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sdk import init, guard, PermissionDeniedError

# Init SDK
init(api_key="test-api-key-123", agent_name="Agent007")

@guard(name="send_email")
def send_email(to_email: str, subject: str, body: str):
    print(f">> [Real Implementation] Sending email to {to_email}...")
    return "Email Sent!"

def test_run():
    print("1. Testing Normal Call (Auto-discovery logic should ALLOW by default)...")
    try:
        # PII should be masked in the backend logs
        result = send_email(to_email="secret.ceo@company.com", subject="Project X", body="This is top secret")
        print(f"Result: {result}")
    except PermissionDeniedError:
        print("BLOCKED!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_run()
