from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.approval import Approval
from app.schemas.approval import ApprovalRead

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
def list_approvals(db: Session = Depends(get_db)):
    return db.query(Approval).all()


@router.post("/{approval_id}/approve", response_model=ApprovalRead)
def approve(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "approved"
    approval.decided_at = datetime.utcnow().isoformat(timespec="seconds")
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/deny", response_model=ApprovalRead)
def deny(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "denied"
    approval.decided_at = datetime.utcnow().isoformat(timespec="seconds")
    db.commit()
    db.refresh(approval)
    return approval
