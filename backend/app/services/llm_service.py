import os

from app.core.config import LLM_ENABLED, OPENAI_API_KEY


def enhance_explanation(base_explanation: str, tool_name: str, environment: str) -> str:
    if not (LLM_ENABLED and OPENAI_API_KEY):
        return base_explanation

    try:
        import openai

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You help explain AI security decisions in concise, developer-friendly language."},
                {"role": "user", "content": f"Tool: {tool_name}. Environment: {environment}. Base explanation: {base_explanation}"},
            ],
            max_tokens=120,
        )
        return response.choices[0].message.content or base_explanation
    except Exception:
        return base_explanation
