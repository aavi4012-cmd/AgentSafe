from typing import Any

from pydantic import BaseModel, ConfigDict


class ActionEvaluateRequest(BaseModel):
    agent: str
    tool: str
    arguments: dict[str, Any] = {}
    environment: str = "development"
    context: dict[str, Any] = {}


class ActionResult(BaseModel):
    agent: str
    tool: str
    environment: str
    risk_score: int
    risk_level: str
    decision: str
    explanation: str
    risk_factors: list[str]
    recommended_policy: str
    policy_name: str = ""
    blocked: bool
    requires_approval: bool


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    agent_name: str
    tool_name: str
    arguments: str
    environment: str
    risk_score: float
    risk_level: str
    decision: str
    explanation: str
    policy_name: str
    approval_status: str
    execution_status: str
    timestamp: str
