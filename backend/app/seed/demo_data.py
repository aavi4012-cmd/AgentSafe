from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.action import Action
from app.models.agent import Agent
from app.models.approval import Approval
from app.models.policy import Policy, PolicyRule
from app.models.tool import Tool


def seed_demo_data():
    db = SessionLocal()
    try:
        if db.query(Agent).count() == 0:
            agents = [
                Agent(name="Customer Support Agent", description="Handles customer operations and ticket triage.", status="active", created_at=datetime.utcnow().isoformat(timespec="seconds")),
                Agent(name="Research Agent", description="Performs research and reads files for analytics.", status="active", created_at=datetime.utcnow().isoformat(timespec="seconds")),
                Agent(name="Deployment Agent", description="Performs deploy actions and infrastructure changes.", status="active", created_at=datetime.utcnow().isoformat(timespec="seconds")),
            ]
            db.add_all(agents)
            db.commit()

        if db.query(Tool).count() == 0:
            tools = [
                Tool(name="web.search", category="Web", sensitivity="low", operation="read", default_risk=12.0, description="Search the public web."),
                Tool(name="read_file", category="Filesystem", sensitivity="medium", operation="read", default_risk=10.0, description="Read a local file."),
                Tool(name="database.read", category="Database", sensitivity="medium", operation="read", default_risk=20.0, description="Read database data."),
                Tool(name="database.write", category="Database", sensitivity="high", operation="write", default_risk=45.0, description="Write database data."),
                Tool(name="database.delete", category="Database", sensitivity="critical", operation="delete", default_risk=90.0, description="Delete a database record."),
                Tool(name="database.delete_user", category="Database", sensitivity="critical", operation="delete", default_risk=90.0, description="Delete a user record."),
                Tool(name="send_email", category="Communication", sensitivity="medium", operation="write", default_risk=35.0, description="Send an email."),
                Tool(name="execute_shell", category="Shell", sensitivity="critical", operation="execute", default_risk=85.0, description="Execute shell commands."),
                Tool(name="deploy", category="Production", sensitivity="high", operation="deploy", default_risk=75.0, description="Deploy code to production."),
                Tool(name="send_money", category="Finance", sensitivity="critical", operation="write", default_risk=95.0, description="Send funds."),
            ]
            db.add_all(tools)
            db.commit()

        if db.query(Policy).count() == 0:
            policies = [
                Policy(name="Production Destructive Operations", description="Never allow destructive production database operations.", effect="deny", environment="production"),
                Policy(name="High Risk Approval", description="Require approval for high-risk actions.", effect="require_approval", environment="production"),
                Policy(name="Secret Handling", description="Blocks secret access.", effect="deny", environment="all"),
                Policy(name="Financial Transfers", description="Require human approval for money transfers.", effect="require_approval", environment="all"),
                Policy(name="Safe Read Only", description="Allow read-only development operations.", effect="allow", environment="development"),
            ]
            db.add_all(policies)
            db.flush()
            db.add_all([
                PolicyRule(policy_id=policies[0].id, field_name="environment", operator="eq", value="production", outcome="deny"),
                PolicyRule(policy_id=policies[0].id, field_name="operation", operator="eq", value="delete", outcome="deny"),
                PolicyRule(policy_id=policies[1].id, field_name="tool", operator="contains", value="deploy", outcome="require_approval"),
                PolicyRule(policy_id=policies[1].id, field_name="environment", operator="eq", value="production", outcome="require_approval"),
                PolicyRule(policy_id=policies[2].id, field_name="tool", operator="contains", value="secret", outcome="deny"),
                PolicyRule(policy_id=policies[2].id, field_name="tool", operator="contains", value="key", outcome="deny"),
                PolicyRule(policy_id=policies[3].id, field_name="tool", operator="contains", value="money", outcome="require_approval"),
                PolicyRule(policy_id=policies[3].id, field_name="tool", operator="contains", value="refund", outcome="require_approval"),
                PolicyRule(policy_id=policies[4].id, field_name="environment", operator="eq", value="development", outcome="allow"),
            ])
            db.commit()

        if db.query(Action).count() == 0:
            template_time = datetime.utcnow() - timedelta(minutes=20)
            actions = [
                Action(agent_id=1, agent_name="Customer Support Agent", tool_name="web.search", arguments='{"query":"billing FAQ"}', context='{"task":"support"}', environment="development", risk_score=12, risk_level="LOW", decision="ALLOW", explanation="Basic read-only web search.", policy_name="Safe Read Only", approval_status="not_required", execution_status="allowed", timestamp=(template_time + timedelta(minutes=0)).isoformat(timespec="seconds")),
                Action(agent_id=1, agent_name="Customer Support Agent", tool_name="database.read", arguments='{"table":"customers"}', context='{"task":"support"}', environment="production", risk_score=20, risk_level="LOW", decision="ALLOW", explanation="Read-only query in production.", policy_name="Safe Read Only", approval_status="not_required", execution_status="allowed", timestamp=(template_time + timedelta(minutes=2)).isoformat(timespec="seconds")),
                Action(agent_id=1, agent_name="Customer Support Agent", tool_name="database.delete_user", arguments='{"user_id":"123"}', context='{"task":"customer removal"}', environment="production", risk_score=90, risk_level="CRITICAL", decision="BLOCK", explanation="Destructive database delete in production.", policy_name="Production Destructive Operations", approval_status="not_required", execution_status="blocked", timestamp=(template_time + timedelta(minutes=5)).isoformat(timespec="seconds")),
                Action(agent_id=2, agent_name="Research Agent", tool_name="read_file", arguments='{"path":"/tmp/report.txt"}', context='{"task":"research"}', environment="development", risk_score=10, risk_level="LOW", decision="ALLOW", explanation="Read-only file access.", policy_name="Safe Read Only", approval_status="not_required", execution_status="allowed", timestamp=(template_time + timedelta(minutes=7)).isoformat(timespec="seconds")),
                Action(agent_id=3, agent_name="Deployment Agent", tool_name="deploy", arguments='{"service":"api","version":"v2"}', context='{"task":"release"}', environment="production", risk_score=75, risk_level="HIGH", decision="REQUIRE_APPROVAL", explanation="Production deployment requires explicit approval.", policy_name="High Risk Approval", approval_status="required", execution_status="pending", timestamp=(template_time + timedelta(minutes=11)).isoformat(timespec="seconds")),
            ]
            db.add_all(actions)
            db.commit()

        if db.query(Approval).count() == 0:
            approvals = [
                Approval(action_id=1, agent_name="Deployment Agent", requested_action="deploy", reason="Production deployment", risk_score=75.0, status="pending", created_at=(datetime.utcnow() - timedelta(minutes=10)).isoformat(timespec="seconds"), decided_at=""),
                Approval(action_id=2, agent_name="Customer Support Agent", requested_action="database.delete_user", reason="Destructive delete", risk_score=90.0, status="pending", created_at=(datetime.utcnow() - timedelta(minutes=8)).isoformat(timespec="seconds"), decided_at=""),
                Approval(action_id=3, agent_name="Customer Support Agent", requested_action="send_money", reason="Financial transfer", risk_score=95.0, status="approved", created_at=(datetime.utcnow() - timedelta(minutes=7)).isoformat(timespec="seconds"), decided_at=(datetime.utcnow() - timedelta(minutes=6)).isoformat(timespec="seconds")),
                Approval(action_id=4, agent_name="Research Agent", requested_action="execute_shell", reason="Shell execution", risk_score=85.0, status="denied", created_at=(datetime.utcnow() - timedelta(minutes=5)).isoformat(timespec="seconds"), decided_at=(datetime.utcnow() - timedelta(minutes=4)).isoformat(timespec="seconds")),
                Approval(action_id=5, agent_name="Customer Support Agent", requested_action="send_email", reason="External email", risk_score=35.0, status="approved", created_at=(datetime.utcnow() - timedelta(minutes=3)).isoformat(timespec="seconds"), decided_at=(datetime.utcnow() - timedelta(minutes=2)).isoformat(timespec="seconds")),
            ]
            db.add_all(approvals)
            db.commit()
    finally:
        db.close()
