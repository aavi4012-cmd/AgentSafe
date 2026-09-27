from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.actions import router as actions_router
from app.api.agents import router as agents_router
from app.api.approvals import router as approvals_router
from app.api.dashboard import router as dashboard_router
from app.api.policies import router as policies_router
from app.api.tools import router as tools_router
from app.core.database import init_db
from app.seed.demo_data import seed_demo_data

app = FastAPI(title="AgentSafe", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()
seed_demo_data()


@app.on_event("startup")
def startup_event():
    init_db()
    seed_demo_data()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "agentsafe"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})


app.include_router(agents_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(policies_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
