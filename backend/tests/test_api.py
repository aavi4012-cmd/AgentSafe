from datetime import datetime, timezone

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


def test_action_and_approval_timestamps_are_aware_utc():
    response = client.post(
        "/api/actions/check",
        json={
            "agent": "timezone-test-agent",
            "tool": "deploy",
            "arguments": {"service": "test"},
            "environment": "production",
        },
    )
    assert response.status_code == 200

    action = next(
        item for item in client.get("/api/actions").json()
        if item["agent_name"] == "timezone-test-agent"
    )
    action_time = datetime.fromisoformat(action["timestamp"])
    assert action_time.tzinfo is not None
    assert action_time.utcoffset() == timezone.utc.utcoffset(action_time)

    approval = next(
        item for item in client.get("/api/approvals").json()
        if item["action_id"] == action["id"]
    )
    approval_time = datetime.fromisoformat(approval["created_at"])
    assert approval_time.tzinfo is not None
    assert approval_time.utcoffset() == timezone.utc.utcoffset(approval_time)


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


def test_approval_decision_persists_and_updates_pending_count():
    pending_before = client.get("/api/dashboard/stats").json()["pending_approval"]
    action_response = client.post(
        "/api/actions/check",
        json={
            "agent": "approval-persistence-test",
            "tool": "deploy",
            "arguments": {"service": "api"},
            "environment": "production",
        },
    )
    assert action_response.status_code == 200
    assert action_response.json()["requires_approval"] is True

    approvals = client.get("/api/approvals").json()
    approval = max(
        (item for item in approvals if item["agent_name"] == "approval-persistence-test"),
        key=lambda item: item["id"],
    )
    decision_response = client.post(f"/api/approvals/{approval['id']}/approve")

    assert decision_response.status_code == 200
    assert decision_response.json()["status"] == "approved"
    assert client.get("/api/dashboard/stats").json()["pending_approval"] == pending_before
    assert client.post(f"/api/approvals/{approval['id']}/deny").status_code == 409

    actions = client.get("/api/actions").json()
    action = next(item for item in actions if item["id"] == approval["action_id"])
    assert action["approval_status"] == "approved"
    assert action["execution_status"] == "approved"
