from __future__ import annotations

from typing import Any


class AgentSafeMiddleware:
    def __init__(self, guard):
        self.guard = guard

    def before_call(self, *, agent: str, tool: str, arguments: dict[str, Any], environment: str = "development"):
        result = self.guard.check_action(agent=agent, tool=tool, arguments=arguments, environment=environment)
        if result.blocked:
            raise RuntimeError(result.reason)
        if result.requires_approval:
            raise RuntimeError("Approval required: " + result.reason)
        return result
