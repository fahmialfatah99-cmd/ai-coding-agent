from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

try:
    from ...engine.orchestrator import AgentOrchestrator
except ImportError:
    from app.engine.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/agent", tags=["Agent Orchestration"])


class RoleModelSpec(BaseModel):
    """Per-role LLM override. Any field not set falls back to the top-level provider/model/api_key."""
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class AgentRunRequest(BaseModel):
    instruction: str
    active_file: Optional[str] = None
    file_content: Optional[str] = None
    workspace_path: str = "./workspace"
    mode: str = "team"  # "team" (Multi-Agent Swarm + Auditor) or "solo" (Fast Solo ReAct)
    provider: str = "9router"
    model: Optional[str] = "ag/gemini-2.5-flash"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_iterations: int = 8
    max_audit_cycles: int = 3
    # Per-role model overrides for the team swarm. Keys: "architect", "builder", "auditor".
    # Each value can independently set provider/model/api_key/base_url.
    # Useful pattern: opus for architect, gpt-4o for builder, haiku/mini for auditor.
    role_models: Optional[Dict[str, RoleModelSpec]] = Field(default=None)


@router.post("/run")
async def run_agent_stream(req: AgentRunRequest):
    """
    Executes the autonomous agent loop (Team Swarm or Solo) and streams real-time Server-Sent Events (SSE).
    """
    role_models_dict: Optional[Dict[str, Dict[str, Any]]] = None
    if req.role_models:
        role_models_dict = {
            role: {k: v for k, v in spec.model_dump().items() if v is not None}
            for role, spec in req.role_models.items()
            if spec
        }

    orchestrator = AgentOrchestrator(
        workspace_path=req.workspace_path,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url,
        role_models=role_models_dict,
    )

    if req.mode.lower() == "team":
        generator = orchestrator.run_team_swarm_loop(
            user_instruction=req.instruction,
            active_file=req.active_file,
            file_content=req.file_content,
            max_audit_cycles=req.max_audit_cycles
        )
    else:
        generator = orchestrator.run_agent_loop(
            user_instruction=req.instruction,
            active_file=req.active_file,
            file_content=req.file_content,
            max_iterations=req.max_iterations
        )

    return StreamingResponse(
        generator,
        media_type="text/event-stream"
    )


@router.get("/health")
async def agent_health():
    return {"status": "ready", "agent_mode": "autonomous_react"}
