from pydantic import BaseModel, ConfigDict


class ToolBase(BaseModel):
    name: str
    category: str = "general"
    sensitivity: str = "medium"
    operation: str = "read"
    default_risk: float = 0.0
    description: str = ""


class ToolCreate(ToolBase):
    pass


class ToolRead(ToolBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
