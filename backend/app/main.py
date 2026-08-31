import os
import subprocess
import glob

try:
    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], capture_output=True)
except Exception:
    pass

try:
    nvm_nodes = glob.glob('/home/fahmial/.nvm/versions/node/*/bin') + glob.glob('/root/.nvm/versions/node/*/bin')
    if nvm_nodes:
        os.environ['PATH'] = ':'.join(nvm_nodes) + ':' + os.environ.get('PATH', '')
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .api.routers import (
        agent_router,
        workspaces_router,
        files_router,
        context_router,
        vector_router,
        sandbox_router,
        models_router,
        sessions_router,
        diff_router,
    )
except ImportError:
    from app.api.routers import (
        agent_router,
        workspaces_router,
        files_router,
        context_router,
        vector_router,
        sandbox_router,
        models_router,
        sessions_router,
        diff_router,
    )

app = FastAPI(
    title="AI Coding Agent Engine",
    description="Autonomous ReAct AI Coding Agent Platform (Cursor-grade) with 9 Modular Routers.",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount 9 Enterprise Routers under /api/v1
API_PREFIX = "/api/v1"
app.include_router(agent_router, prefix=API_PREFIX)
app.include_router(workspaces_router, prefix=API_PREFIX)
app.include_router(files_router, prefix=API_PREFIX)
app.include_router(context_router, prefix=API_PREFIX)
app.include_router(vector_router, prefix=API_PREFIX)
app.include_router(sandbox_router, prefix=API_PREFIX)
app.include_router(models_router, prefix=API_PREFIX)
app.include_router(sessions_router, prefix=API_PREFIX)
app.include_router(diff_router, prefix=API_PREFIX)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "AI Coding Agent Engine"}

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "AI Coding Agent Engine (Cursor-grade Web Platform)",
        "version": "2.1.0",
        "routers_count": 9,
        "routers": [
            "/api/v1/agent",
            "/api/v1/workspaces",
            "/api/v1/files",
            "/api/v1/context",
            "/api/v1/vector",
            "/api/v1/sandbox",
            "/api/v1/models",
            "/api/v1/sessions",
            "/api/v1/diff",
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
