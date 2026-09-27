from pydantic import BaseModel, ConfigDict


class AgentBase(BaseModel):
    name: str
    description: str = ""
    status: str = "active"


class AgentCreate(AgentBase):
    pass


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

