backend-install:
	cd backend && python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt

backend-run:
	cd backend && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

backend-test:
	cd backend && .\.venv\Scripts\Activate.ps1 && pytest -q

frontend-build:
	cd frontend && npm run build
