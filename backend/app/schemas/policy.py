from pydantic import BaseModel, ConfigDict


class PolicyRuleBase(BaseModel):
    field_name: str
    operator: str = "eq"
    value: str
    outcome: str = "deny"


class PolicyRuleCreate(PolicyRuleBase):
    pass


class PolicyBase(BaseModel):
    name: str
    description: str = ""
    effect: str = "deny"
    environment: str = "all"


class PolicyCreate(PolicyBase):
    rules: list[PolicyRuleCreate] = []


class PolicyRead(PolicyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rules: list[PolicyRuleBase] = []
