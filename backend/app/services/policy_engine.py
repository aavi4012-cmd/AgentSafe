from __future__ import annotations

from typing import Any


def _matches(rule: dict[str, Any], action: dict[str, Any]) -> bool:
    field = rule.get("field_name", "")
    operator = rule.get("operator", "eq")
    expected = str(rule.get("value", "")).lower()
    actual = str(action.get(field, "")).lower()

    if field == "tool":
        actual = str(action.get("tool", "")).lower()
    elif field == "environment":
        actual = str(action.get("environment", "")).lower()
    elif field == "operation":
        actual = str(action.get("operation", "")).lower()
    elif field == "resource":
        actual = str(action.get("resource", "")).lower()

    if operator == "contains":
        return expected in actual
    if operator == "eq":
        return actual == expected
    if operator == "in":
        return actual in expected
    return actual == expected


def evaluate_policy(policies: list[dict[str, Any]], action: dict[str, Any]) -> tuple[str, str]:
    for policy in policies:
        rules = policy.get("rules", [])
        if not rules:
            continue
        matched = all(_matches(rule, action) for rule in rules)
        if matched:
            return policy.get("effect", "deny"), policy.get("name", "custom-policy")
    return "allow", "No matching policy"
