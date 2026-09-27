from agentsafe_sdk import AgentSafe, AgentSafeApprovalRequired, AgentSafeBlockedError


guard = AgentSafe(api_url="http://localhost:8000")


@guard.protect(tool="database.delete_user", environment="production")
def delete_user(user_id: str):
    return {"deleted": True, "user_id": user_id}


if __name__ == "__main__":
    try:
        print(delete_user("123"))
    except AgentSafeApprovalRequired:
        print("Approval required before this action can proceed.")
    except AgentSafeBlockedError:
        print("Action blocked by AgentSafe policy.")
