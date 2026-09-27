from agentsafe_sdk import AgentSafe


guard = AgentSafe(api_url="http://localhost:8000")

actions = [
    {"agent": "research-agent", "tool": "web.search", "arguments": {"query": "customer support"}, "environment": "development"},
    {"agent": "support-agent", "tool": "database.read", "arguments": {"table": "orders"}, "environment": "production"},
    {"agent": "support-agent", "tool": "database.delete_user", "arguments": {"user_id": "123"}, "environment": "production"},
    {"agent": "deployment-agent", "tool": "deploy", "arguments": {"service": "api"}, "environment": "production"},
]

for action in actions:
    result = guard.check_action(**action)
    print(action["tool"], "->", result.risk_score, result.risk_level, result.reason[:120])
