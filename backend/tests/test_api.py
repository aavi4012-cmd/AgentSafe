from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agents_endpoint_returns_list():
    response = client.get("/api/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tools_endpoint_returns_list():
    response = client.get("/api/tools")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_actions_check_endpoint_allows_low_risk():
    payload = {"agent": "research-agent", "tool": "web.search", "arguments": {"query": "pricing"}, "environment": "development"}
    response = client.post("/api/actions/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in {"ALLOW", "REQUIRE_APPROVAL"}


def test_actions_check_endpoint_blocks_critical_risk():
    payload = {"agent": "support-agent", "tool": "database.delete_user", "arguments": {"user_id": "123"}, "environment": "production"}
    response = client.post("/api/actions/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"


def test_actions_check_endpoint_approval_for_deploy():
    payload = {"agent": "deployment-agent", "tool": "deploy", "arguments": {"service": "api"}, "environment": "production"}
    response = client.post("/api/actions/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["requires_approval"] or data["decision"] == "REQUIRE_APPROVAL"


def test_dashboard_stats_endpoint():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_actions" in data
    assert "risk_distribution" in data


def test_recent_actions_endpoint():
    response = client.get("/api/dashboard/recent-actions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_policies_endpoint_returns_data():
    response = client.get("/api/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_approvals_endpoint_returns_data():
    response = client.get("/api/approvals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
