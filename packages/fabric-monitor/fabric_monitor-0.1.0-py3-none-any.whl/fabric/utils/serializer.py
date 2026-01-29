"""Serialization utility functions"""

import json
from typing import Any, Optional
from datetime import datetime


def truncate_body(
    body: Optional[str],
    max_size: int = 10240
) -> Optional[str]:
    """Truncate request/response body
    
    Args:
        body: Original content
        max_size: Maximum size (bytes)
        
    Returns:
        Truncated content
    """
    if body is None:
        return None
    
    if len(body) <= max_size:
        return body
    
    return body[:max_size] + f"... (truncated, total {len(body)} bytes)"


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safe JSON serialization
    
    Automatically handles special types like datetime.
    
    Args:
        obj: Object to serialize
        **kwargs: Arguments to pass to json.dumps
        
    Returns:
        JSON string
    """
    def default_handler(o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        elif hasattr(o, "__dict__"):
            return o.__dict__
        else:
            return str(o)
    
    return json.dumps(obj, default=default_handler, **kwargs)


def mask_sensitive_data(
    data: dict,
    sensitive_keys: list = None
) -> dict:
    """Mask sensitive data
    
    Args:
        data: Original data dictionary
        sensitive_keys: List of sensitive field names
        
    Returns:
        Processed dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "password", "token", "secret", "key", "auth",
            "authorization", "cookie", "session"
        ]
    
    result = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field is sensitive
        is_sensitive = any(s in key_lower for s in sensitive_keys)
        
        if is_sensitive and isinstance(value, str):
            # Keep first and last few characters
            if len(value) > 8:
                result[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                result[key] = "*" * len(value)
        elif isinstance(value, dict):
            result[key] = mask_sensitive_data(value, sensitive_keys)
        else:
            result[key] = value
    
    return result
