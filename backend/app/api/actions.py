import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import redact_secrets
from app.models.action import Action
from app.models.approval import Approval
from app.schemas.action import ActionEvaluateRequest, ActionRead, ActionResult
from app.services.action_engine import evaluate_action

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/check", response_model=ActionResult)
def check_action(payload: ActionEvaluateRequest, db: Session = Depends(get_db)):
    policies = []
    db_policies = db.query(__import__("app.models.policy", fromlist=["Policy"]).Policy).all()
    for policy in db_policies:
        rule_items = []
        for rule in policy.rules:
            rule_items.append({
                "field_name": rule.field_name,
                "operator": rule.operator,
                "value": rule.value,
                "outcome": rule.outcome,
            })
        policies.append({"name": policy.name, "effect": policy.effect, "rules": rule_items})

    result = evaluate_action(
        tool_name=payload.tool,
        arguments=payload.arguments,
        environment=payload.environment,
        context=payload.context,
        policies=policies,
    )

    action_record = Action(
        agent_id=1,
        agent_name=payload.agent,
        tool_name=payload.tool,
        arguments=json.dumps(redact_secrets(payload.arguments), default=str),
        context=json.dumps(redact_secrets(payload.context), default=str),
        environment=payload.environment,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        decision=result["decision"],
        explanation=result["explanation"],
        policy_name=result["policy_name"],
        approval_status="required" if result["requires_approval"] else "not_required",
        execution_status="allowed" if result["decision"] == "ALLOW" else "blocked" if result["decision"] == "BLOCK" else "pending",
        timestamp=datetime.utcnow().isoformat(timespec="seconds"),
    )
    db.add(action_record)
    db.commit()
    db.refresh(action_record)

    if result["requires_approval"]:
        approval = Approval(
            action_id=action_record.id,
            agent_name=payload.agent,
            requested_action=payload.tool,
            reason=result["risk_factors"][0] if result["risk_factors"] else "high-risk action",
            risk_score=result["risk_score"],
            status="pending",
            created_at=datetime.utcnow().isoformat(timespec="seconds"),
        )
        db.add(approval)
        db.commit()

    return ActionResult(
        agent=payload.agent,
        tool=payload.tool,
        environment=payload.environment,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        decision=result["decision"],
        explanation=result["explanation"],
        risk_factors=result["risk_factors"],
        recommended_policy=result["recommended_policy"],
        policy_name=result["policy_name"],
        blocked=result["blocked"],
        requires_approval=result["requires_approval"],
    )


@router.get("", response_model=list[ActionRead])
def list_actions(db: Session = Depends(get_db)):
    return db.query(Action).order_by(Action.id.desc()).all()


@router.get("/{action_id}", response_model=ActionRead)
def get_action(action_id: int, db: Session = Depends(get_db)):
    item = db.query(Action).filter(Action.id == action_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action not found")
    return item
