from sqlalchemy import Column, Integer, String, Text, Float

from app.core.database import Base


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, nullable=False)
    agent_name = Column(String(255), default="")
    tool_name = Column(String(255), nullable=False)
    arguments = Column(Text, default="{}")
    context = Column(Text, default="{}")
    environment = Column(String(50), default="development")
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(50), default="LOW")
    decision = Column(String(50), default="ALLOW")
    explanation = Column(Text, default="")
    policy_name = Column(String(255), default="")
    approval_status = Column(String(50), default="not_required")
    execution_status = Column(String(50), default="pending")
    timestamp = Column(String(50), default="")
