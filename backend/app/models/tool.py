from sqlalchemy import Column, Integer, String, Text, Float

from app.core.database import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), default="general")
    sensitivity = Column(String(50), default="medium")
    operation = Column(String(50), default="read")
    default_risk = Column(Float, default=0.0)
    description = Column(Text, default="")
