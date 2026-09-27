from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.policy_engine import evaluate_policy
from app.services.risk_engine import analyze_action


def evaluate_action(tool_name: str, arguments: dict[str, Any], environment: str = "development", context: dict[str, Any] | None = None, policies: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    context = context or {}
    policies = policies or []
    assessment = analyze_action(tool_name=tool_name, arguments=arguments, environment=environment, context=context)
    action = {
        "tool": tool_name,
        "environment": environment,
        "operation": "read" if "read" in tool_name.lower() else "write" if any(token in tool_name.lower() for token in ["write", "create", "update"]) else "delete" if any(token in tool_name.lower() for token in ["delete", "drop", "purge"]) else "deploy" if any(token in tool_name.lower() for token in ["deploy", "restart", "shutdown"]) else "other",
        "resource": "database" if "database" in tool_name.lower() else "file" if "file" in tool_name.lower() else "finance" if any(token in tool_name.lower() for token in ["payment", "refund", "transfer", "money"]) else "general",
    }
    policy_effect, policy_name = evaluate_policy(policies, action)

    decision = assessment.decision
    if policy_effect == "deny":
        decision = "BLOCK"
    elif policy_effect == "require_approval":
        decision = "REQUIRE_APPROVAL"
    elif policy_effect == "allow":
        decision = "ALLOW"

    return {
        "risk_score": assessment.score,
        "risk_level": assessment.level,
        "decision": decision,
        "explanation": assessment.explanation,
        "risk_factors": assessment.factors,
        "recommended_policy": assessment.recommended_policy,
        "policy_name": assessment.policy_name if policy_name == "No matching policy" else policy_name,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        "requires_approval": decision == "REQUIRE_APPROVAL",
        "blocked": decision == "BLOCK",
    }
