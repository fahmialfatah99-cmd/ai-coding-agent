from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

try:
    from ...engine.orchestrator import AgentOrchestrator
except ImportError:
    from app.engine.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/agent", tags=["Agent Orchestration"])

class AgentRunRequest(BaseModel):
    instruction: str
    active_file: Optional[str] = None
    file_content: Optional[str] = None
    workspace_path: str = "./workspace"
    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_iterations: int = 6

@router.post("/run")
async def run_agent_stream(req: AgentRunRequest):
    """
    Executes the autonomous ReAct agent loop and streams real-time Server-Sent Events (SSE).
    """
    orchestrator = AgentOrchestrator(
        workspace_path=req.workspace_path,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url
    )
    
    return StreamingResponse(
        orchestrator.run_agent_loop(
            user_instruction=req.instruction,
            active_file=req.active_file,
            file_content=req.file_content,
            max_iterations=req.max_iterations
        ),
        media_type="text/event-stream"
    )

@router.get("/health")
async def agent_health():
    return {"status": "ready", "agent_mode": "autonomous_react"}
