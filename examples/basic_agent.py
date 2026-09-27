from agentsafe_sdk import AgentSafe


guard = AgentSafe(api_url="http://localhost:8000")


def search_docs(query: str):
    result = guard.check_action(
        agent="research-agent",
        tool="web.search",
        arguments={"query": query},
        environment="development",
    )
    if result.blocked:
        raise RuntimeError(result.reason)
    return {"tool": "web.search", "query": query, "risk": result.risk_score}


if __name__ == "__main__":
    print(search_docs("billing FAQ"))
