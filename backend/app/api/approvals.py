from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.action import Action
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
    if approval.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approval has already been decided")
    approval.status = "approved"
    approval.decided_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    action = db.query(Action).filter(Action.id == approval.action_id).first()
    if action:
        action.approval_status = "approved"
        action.execution_status = "approved"
    db.commit()
    db.refresh(approval)
    return approval


@router.post("/{approval_id}/deny", response_model=ApprovalRead)
def deny(approval_id: int, db: Session = Depends(get_db)):
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approval has already been decided")
    approval.status = "denied"
    approval.decided_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    action = db.query(Action).filter(Action.id == approval.action_id).first()
    if action:
        action.approval_status = "denied"
        action.execution_status = "denied"
    db.commit()
    db.refresh(approval)
    return approval
