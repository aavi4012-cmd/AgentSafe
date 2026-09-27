from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, default="")
    effect = Column(String(50), default="deny")
    environment = Column(String(50), default="all")

    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    operator = Column(String(50), default="eq")
    value = Column(String(255), nullable=False)
    outcome = Column(String(50), default="deny")

    policy = relationship("Policy", back_populates="rules")
