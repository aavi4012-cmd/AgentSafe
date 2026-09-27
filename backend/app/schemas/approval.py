from pydantic import BaseModel, ConfigDict


class ApprovalBase(BaseModel):
    action_id: int
    agent_name: str
    requested_action: str
    reason: str = ""
    risk_score: float = 0.0


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalRead(ApprovalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: str
    decided_at: str | None = None
