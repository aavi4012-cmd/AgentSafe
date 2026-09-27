from __future__ import annotations

from typing import Any

import httpx

from agentsafe_sdk.exceptions import AgentSafeApprovalRequired, AgentSafeBlockedError


class CheckResult:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.blocked = payload.get("decision") == "BLOCK"
        self.requires_approval = payload.get("requires_approval") or payload.get("decision") == "REQUIRE_APPROVAL"
        self.reason = payload.get("explanation", "")
        self.risk_score = payload.get("risk_score", 0)
        self.risk_level = payload.get("risk_level", "LOW")


class AgentSafe:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip("/")

    def check_action(self, *, agent: str, tool: str, arguments: dict[str, Any] | None = None, environment: str = "development", context: dict[str, Any] | None = None) -> CheckResult:
        payload = {
            "agent": agent,
            "tool": tool,
            "arguments": arguments or {},
            "environment": environment,
            "context": context or {},
        }
        response = httpx.post(f"{self.api_url}/api/actions/check", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return CheckResult(data)

    def protect(self, *, tool: str, environment: str = "development"):
        def decorator(func):
            def wrapper(*args, **kwargs):
                result = self.check_action(agent="local-agent", tool=tool, arguments={**kwargs, **dict(zip(func.__code__.co_varnames[: len(args)], args))}, environment=environment)
                if result.blocked:
                    raise AgentSafeBlockedError(result.reason)
                if result.requires_approval:
                    raise AgentSafeApprovalRequired(result.reason)
                return func(*args, **kwargs)
            return wrapper
        return decorator
