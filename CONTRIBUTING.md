# Contributing to AgentSafe

Thanks for your interest in helping build AgentSafe.

This project is open for community contributions. Anyone can propose improvements, bug fixes, and feature ideas through GitHub pull requests. The maintainer will review and approve or request changes before merging.

## How to contribute

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make a focused change.
4. Run the relevant checks locally.
5. Open a pull request with a clear summary and testing notes.

## Contribution standards

- Keep changes small and focused.
- Add or update tests when behavior changes.
- Follow the existing project structure and naming conventions.
- Prefer clear, human-readable code and documentation.
- Do not add hidden dependencies or secret keys to the project.

## Local validation

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Frontend:

```powershell
cd frontend
npm install
npm run build
```

## Review policy

- Anyone may open a pull request.
- Maintainers review all submissions.
- Merge approvals are controlled by the repository owner.
- Contributions should be respectful, constructive, and aligned with the product goals.

## Code of conduct

Please keep discussions professional, helpful, and respectful.
