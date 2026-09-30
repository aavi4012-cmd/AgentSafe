from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.action import Action
from app.models.approval import Approval

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(Action).count()
    allowed = db.query(Action).filter(Action.decision == "ALLOW").count()
    blocked = db.query(Action).filter(Action.decision == "BLOCK").count()
    pending = db.query(Approval).filter(Approval.status == "pending").count()
    return {
        "total_actions": total,
        "allowed": allowed,
        "blocked": blocked,
        "pending_approval": pending,
        "risk_distribution": {
            "LOW": db.query(Action).filter(Action.risk_level == "LOW").count(),
            "MEDIUM": db.query(Action).filter(Action.risk_level == "MEDIUM").count(),
            "HIGH": db.query(Action).filter(Action.risk_level == "HIGH").count(),
            "CRITICAL": db.query(Action).filter(Action.risk_level == "CRITICAL").count(),
        },
    }


@router.get("/recent-actions")
def recent_actions(db: Session = Depends(get_db), limit: int = 10):
    items = db.query(Action).order_by(Action.id.desc()).limit(limit).all()
    return [
        {
            "id": item.id,
            "agent_name": item.agent_name,
            "tool_name": item.tool_name,
            "risk_score": item.risk_score,
            "risk_level": item.risk_level,
            "decision": item.decision,
            "timestamp": item.timestamp,
        }
        for item in items
    ]
