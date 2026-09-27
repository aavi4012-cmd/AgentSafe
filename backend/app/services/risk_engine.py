from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


TOOL_BASE_RISK = {
    "read_file": 10,
    "read_database": 20,
    "write_database": 45,
    "delete_database": 90,
    "send_email": 35,
    "send_money": 95,
    "execute_shell": 85,
    "read_secret": 80,
    "delete_file": 85,
    "push_production_code": 75,
    "access_api_key": 90,
    "web.search": 12,
    "database.read": 20,
    "database.write": 45,
    "database.delete": 90,
    "database.delete_user": 90,
    "deploy": 75,
    "restart": 60,
    "shutdown": 80,
}


def clamp(value: int) -> int:
    return max(0, min(100, value))


@dataclass
class RiskAssessment:
    score: int
    level: str
    decision: str
    factors: list[str] = field(default_factory=list)
    explanation: str = ""
    recommended_policy: str = ""
    policy_name: str = ""


def _score_level(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def _classify_decision(score: int, environment: str, factors: list[str]) -> str:
    if score >= 80 or "destructive operation" in factors and environment == "production":
        return "BLOCK"
    if score >= 50 or environment == "production" and any(f in factors for f in ["financial operation", "production operation"]):
        return "REQUIRE_APPROVAL"
    return "ALLOW"


def _normalize_tool_name(tool_name: str) -> str:
    return tool_name.lower().strip()


def _operation_from_tool(tool_name: str) -> str:
    name = _normalize_tool_name(tool_name)
    if any(token in name for token in ["delete", "drop", "truncate", "destroy", "remove", "purge"]):
        return "delete"
    if any(token in name for token in ["write", "create", "update", "insert", "modify"]):
        return "write"
    if any(token in name for token in ["read", "fetch", "query", "search", "list"]):
        return "read"
    if any(token in name for token in ["deploy", "restart", "shutdown"]):
        return "deploy"
    return "other"


def _resource_from_tool(tool_name: str) -> str:
    name = _normalize_tool_name(tool_name)
    if "database" in name or "db" in name:
        return "database"
    if "file" in name or "filesystem" in name:
        return "file"
    if "email" in name or "message" in name:
        return "communication"
    if "money" in name or "refund" in name or "payment" in name or "transfer" in name:
        return "finance"
    if "secret" in name or "key" in name:
        return "credential"
    if "deploy" in name or "production" in name:
        return "production"
    return "general"


def analyze_action(tool_name: str, arguments: dict[str, Any] | None = None, environment: str = "development", context: dict[str, Any] | None = None) -> RiskAssessment:
    arguments = arguments or {}
    context = context or {}
    name = _normalize_tool_name(tool_name)
    combined = json.dumps({"tool": name, "arguments": arguments, "context": context}, sort_keys=True).lower()

    score = TOOL_BASE_RISK.get(name, 15)
    factors: list[str] = []

    if any(token in name for token in ["delete", "drop", "truncate", "destroy", "remove", "purge"]):
        score += 28
        factors.append("destructive operation")
    if any(token in name for token in ["secret", "password", "token", "key", "credential", "private_key", "aws"]):
        score += 25
        factors.append("secret access")
    if any(token in name for token in ["payment", "transfer", "refund", "purchase", "withdraw", "send_money", "charge"]):
        score += 32
        factors.append("financial operation")
    if any(token in name for token in ["send_email", "send_message", "email", "post_publicly", "upload_file", "webhook"]):
        score += 18
        factors.append("external communication")
    if any(token in name for token in ["deploy", "restart", "shutdown", "modify_production", "change_dns", "production"]):
        score += 22
        factors.append("production operation")
    if any(token in name for token in ["bash", "curl", "wget", "powershell", "sudo", "rm ", "chmod", "shell"]):
        score += 25
        factors.append("shell/system action")
    if any(keyword in combined for keyword in ["customer data", "pii", "health", "financial records", "ssn", "personal data"]):
        score += 18
        factors.append("sensitive data")

    arg_keys = " ".join(str(k).lower() for k in arguments.keys())
    arg_values = " ".join(str(v).lower() for v in arguments.values())
    if any(token in arg_keys + " " + arg_values for token in ["api_key", "password", "token", "secret", "private key", "aws_access_key", "db_password"]):
        score += 20
        factors.append("credential in arguments")

    if environment == "production":
        score += 18
        factors.append("production environment")
    if environment == "staging":
        score += 8
        factors.append("staging environment")

    if _resource_from_tool(name) == "database" and "delete" in _operation_from_tool(name):
        score += 8
    if _resource_from_tool(name) == "finance":
        score += 8

    score = clamp(score)
    level = _score_level(score)
    decision = _classify_decision(score, environment, factors)

    if decision == "BLOCK":
        recommended_policy = "Deny destructive production operations and require explicit approval for high-impact changes."
        policy_name = "Production Destructive Operations"
    elif decision == "REQUIRE_APPROVAL":
        recommended_policy = "Require human approval for sensitive or high-risk actions in production environments."
        policy_name = "High Risk Approval"
    else:
        recommended_policy = "Allow the action while continuing to record metrics and audit logs."
        policy_name = "Default Safe Allow"

    if "destructive operation" in factors and environment == "production":
        explanation = (
            f"Agent attempted to perform a destructive { _resource_from_tool(name) } action in the {environment} environment. "
            "This operation can remove data or disrupt critical systems. The action was evaluated as high risk and should be restricted."
        )
    elif "financial operation" in factors:
        explanation = "The action performs a financial operation that can move or change funds. This has material business impact and should be reviewed."
    elif "secret access" in factors:
        explanation = "The action touches secret or credential data. This is sensitive and can lead to unauthorized access if exposed."
    else:
        explanation = f"The action {tool_name} is being evaluated for risk based on sensitivity, potential impact, and environment."

    if not factors:
        factors.append("baseline operation risk")

    return RiskAssessment(
        score=score,
        level=level,
        decision=decision,
        factors=factors,
        explanation=explanation,
        recommended_policy=recommended_policy,
        policy_name=policy_name,
    )
