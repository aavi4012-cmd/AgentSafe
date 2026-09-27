from dataclasses import dataclass
from typing import Any


@dataclass
class ActionRequest:
    agent: str
    tool: str
    arguments: dict[str, Any] | None = None
    environment: str = "development"
    context: dict[str, Any] | None = None


@dataclass
class ActionDecision:
    decision: str
    risk_score: int
    risk_level: str
    explanation: str
    blocked: bool = False
    requires_approval: bool = False
