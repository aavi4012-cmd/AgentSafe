from pathlib import Path


root = Path(__file__).resolve().parent.parent
print(f"AgentSafe repository created at {root}")
print("Run the backend: cd backend && python -m venv .venv && .\\.venv\\Scripts\\Activate.ps1 && pip install -r requirements.txt")
print("Run the frontend: cd frontend && npm install && npm run dev")
