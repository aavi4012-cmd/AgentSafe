from app.core.security import redact_secret_string, redact_secrets
from app.services.action_engine import evaluate_action
from app.services.policy_engine import evaluate_policy
from app.services.risk_engine import analyze_action


def test_low_risk_web_search():
    assessment = analyze_action("web.search", {"query": "billing faq"}, "development")
    assert assessment.score <= 25
    assert assessment.level in {"LOW", "MEDIUM"}


def test_low_risk_read_file():
    assessment = analyze_action("read_file", {"path": "notes.txt"}, "development")
    assert assessment.score < 30


def test_medium_database_read():
    assessment = analyze_action("database.read", {"table": "orders"}, "production")
    assert assessment.score >= 20


def test_high_risk_database_write():
    assessment = analyze_action("database.write", {"table": "customers"}, "production")
    assert assessment.score >= 45
    assert assessment.level in {"MEDIUM", "HIGH"}


def test_critical_delete_database():
    assessment = analyze_action("database.delete", {"table": "customers"}, "production")
    assert assessment.score >= 80
    assert assessment.decision == "BLOCK"


def test_delete_operation_detection():
    assessment = analyze_action("database.delete_user", {"user_id": "123"}, "development")
    assert "destructive operation" in assessment.factors


def test_secret_detection():
    assessment = analyze_action("read_secret", {"API_KEY": "sk-123456"}, "production")
    assert "secret access" in assessment.factors or "credential in arguments" in assessment.factors


def test_financial_operation_detection():
    assessment = analyze_action("send_money", {"amount": 250}, "production")
    assert "financial operation" in assessment.factors


def test_production_deploy_detection():
    assessment = analyze_action("deploy", {"service": "api"}, "production")
    assert "production operation" in assessment.factors


def test_shell_execution_detection():
    assessment = analyze_action("execute_shell", {"command": "rm -rf /tmp"}, "development")
    assert "shell/system action" in assessment.factors


def test_sensitive_data_detection():
    assessment = analyze_action("database.read", {"table": "customer_records", "pii": "ssn"}, "production")
    assert "sensitive data" in assessment.factors


def test_policy_allow_rule():
    result = evaluate_policy([
        {"name": "Allow reads", "effect": "allow", "rules": [{"field_name": "environment", "operator": "eq", "value": "development"}]}
    ], {"environment": "development", "tool": "web.search"})
    assert result == ("allow", "Allow reads")


def test_policy_deny_rule():
    result = evaluate_policy([
        {"name": "Block deletes", "effect": "deny", "rules": [{"field_name": "operation", "operator": "eq", "value": "delete"}]}
    ], {"environment": "production", "operation": "delete"})
    assert result == ("deny", "Block deletes")


def test_action_engine_requires_approval_for_high_risk():
    evaluation = evaluate_action("deploy", {"service": "api"}, "production", policies=[{"name": "High Risk Approval", "effect": "require_approval", "rules": [{"field_name": "tool", "operator": "contains", "value": "deploy"}]}])
    assert evaluation["decision"] in {"REQUIRE_APPROVAL", "BLOCK"}


def test_action_engine_blocks_dangerous_action_with_policy():
    evaluation = evaluate_action("database.delete_user", {"user_id": "123"}, "production", policies=[{"name": "Deny Production Deletes", "effect": "deny", "rules": [{"field_name": "operation", "operator": "eq", "value": "delete"},{"field_name": "environment", "operator": "eq", "value": "production"}]}])
    assert evaluation["decision"] == "BLOCK"


def test_redact_secret_string():
    assert redact_secret_string("API_KEY=sk-123456") == "API_KEY=****456"


def test_redact_secret_dict():
    redacted = redact_secrets({"API_KEY": "sk-123456", "nested": {"password": "abc12345"}})
    assert "sk-" not in redacted["API_KEY"]
    assert "abc" not in redacted["nested"]["password"]


def test_rule_match_contains():
    action = {"tool": "deploy.production", "environment": "production"}
    result = evaluate_policy([
        {"name": "Prod deploy policy", "effect": "require_approval", "rules": [{"field_name": "tool", "operator": "contains", "value": "deploy"}]}
    ], action)
    assert result == ("require_approval", "Prod deploy policy")


def test_risk_explanation_contains_operation_summary():
    assessment = analyze_action("database.delete_user", {"user_id": 123}, "production")
    assert "destructive" in assessment.explanation.lower() or "action" in assessment.explanation.lower()


def test_policy_without_matching_rule_falls_back_allow():
    result = evaluate_policy([
        {"name": "prod policy", "effect": "deny", "rules": [{"field_name": "environment", "operator": "eq", "value": "production"}]}
    ], {"environment": "development", "tool": "web.search"})
    assert result == ("allow", "No matching policy")


def test_environment_modifies_risk():
    prod = analyze_action("send_email", {"to": "ops@example.com"}, "production")
    dev = analyze_action("send_email", {"to": "ops@example.com"}, "development")
    assert prod.score >= dev.score


def test_destructive_in_production_always_blocking():
    assessment = analyze_action("delete_file", {"path": "/var/lib/data.bin"}, "production")
    assert assessment.decision == "BLOCK"
