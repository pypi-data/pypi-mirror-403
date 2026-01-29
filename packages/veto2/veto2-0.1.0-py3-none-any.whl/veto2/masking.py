import re
from typing import Any, Dict, List, Union

def mask_pii(data: Any) -> Any:
    """
    Recursively traverse data and mask PII.
    Currently supports Email.
    """
    if isinstance(data, dict):
        return {k: mask_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_pii(i) for i in data]
    elif isinstance(data, str):
        # Email Regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        
        def replace_email(match):
            return "***@***.com"
            
        return re.sub(email_pattern, replace_email, data)
    else:
        return data
