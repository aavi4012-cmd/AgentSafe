import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentsafe.db")
AGENTSAFE_ENV = os.getenv("AGENTSAFE_ENV", "development")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
