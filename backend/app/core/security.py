from __future__ import annotations

import re
from typing import Any

SECRET_KEY_PATTERNS = (
    "api_key",
    "apikey",
    "password",
    "passwd",
    "token",
    "secret",
    "private_key",
    "aws_access_key",
    "db_password",
    "authorization",
    "cookie",
    "bearer",
)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if isinstance(key, str) and any(pattern in key.lower() for pattern in SECRET_KEY_PATTERNS):
                redacted[key] = redact_secret_string(str(item))
            else:
                redacted[key] = redact_secrets(item)
        return redacted
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        return redact_secret_string(value)
    return value


def redact_secret_string(value: str) -> str:
    if not value:
        return value
    if "=" in value:
        left, right = value.split("=", 1)
        suffix = right[-3:] if len(right) > 3 else right
        return f"{left}=****{suffix}"
    masked = re.sub(r"(?i)(sk-[A-Za-z0-9]+)", "****", value)
    if masked != value:
        return masked
    if len(value) > 6:
        return "****" + value[-3:]
    return "****"


def safe_simulation_mode() -> bool:
    return True
