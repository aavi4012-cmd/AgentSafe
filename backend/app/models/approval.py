from sqlalchemy import Column, Integer, String, Text, Float

from app.core.database import Base


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, nullable=False)
    agent_name = Column(String(255), default="")
    requested_action = Column(String(255), default="")
    reason = Column(Text, default="")
    risk_score = Column(Float, default=0.0)
    status = Column(String(50), default="pending")
    created_at = Column(String(50), default="")
    decided_at = Column(String(50), default="")
