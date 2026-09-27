from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.policy import Policy, PolicyRule
from app.schemas.policy import PolicyCreate, PolicyRead

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=list[PolicyRead])
def list_policies(db: Session = Depends(get_db)):
    return db.query(Policy).all()


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    policy = Policy(
        name=payload.name,
        description=payload.description,
        effect=payload.effect,
        environment=payload.environment,
    )
    db.add(policy)
    db.flush()

    for rule in payload.rules:
        db.add(PolicyRule(policy_id=policy.id, **rule.model_dump()))
    db.commit()
    db.refresh(policy)
    return policy


@router.put("/{policy_id}", response_model=PolicyRead)
def update_policy(policy_id: int, payload: PolicyCreate, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.name = payload.name
    policy.description = payload.description
    policy.effect = payload.effect
    policy.environment = payload.environment
    policy.rules.clear()
    for rule in payload.rules:
        policy.rules.append(PolicyRule(**rule.model_dump()))
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()
    return {"deleted": True}
