from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .api.routes import router as api_router
except ImportError:
    from app.api.routes import router as api_router

app = FastAPI(
    title="AI Coding Agent Engine",
    description="Autonomous ReAct AI Coding Agent Platform with Multi-Provider LLM, Tree-sitter AST, and Docker Sandbox.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": "AI Coding Agent Engine (Cursor-grade Web Platform)",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
