from __future__ import annotations

from datetime import datetime, timedelta


def approval_expired(created_at: str) -> bool:
    try:
        created = datetime.fromisoformat(created_at)
        return datetime.utcnow() - created > timedelta(hours=24)
    except ValueError:
        return False
