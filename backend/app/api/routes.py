import os
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    from ..engine.orchestrator import AgentOrchestrator
    from ..engine.llm_adapter import UnifiedLLMClient
    from ..engine.docker_sandbox import DockerSandboxManager
except ImportError:
    from app.engine.orchestrator import AgentOrchestrator
    from app.engine.llm_adapter import UnifiedLLMClient
    from app.engine.docker_sandbox import DockerSandboxManager

router = APIRouter(prefix="/api/v1")

class AgentRunRequest(BaseModel):
    instruction: str
    active_file: Optional[str] = None
    file_content: Optional[str] = None
    workspace_path: str = "./workspace"
    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class FileReadRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str

class FileWriteRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str
    content: str

class TerminalExecRequest(BaseModel):
    workspace_path: str = "./workspace"
    command: str

@router.get("/models")
async def get_models():
    """Returns available LLM providers and models."""
    return {"providers": UnifiedLLMClient.get_supported_providers()}

@router.post("/agent/run")
async def run_agent(req: AgentRunRequest):
    """Executes ReAct agent loop and streams real-time Server-Sent Events."""
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
            file_content=req.file_content
        ),
        media_type="text/event-stream"
    )

@router.get("/files")
async def get_file_tree(workspace_path: str = Query("./workspace")):
    """Recursively lists files and folders in the workspace."""
    abs_root = os.path.abspath(workspace_path)
    if not os.path.exists(abs_root):
        os.makedirs(abs_root, exist_ok=True)

    ignore_dirs = {".git", "node_modules", "__pycache__", ".next", ".pytest_cache", "venv", ".venv"}

    def build_tree(current_path: str) -> List[Dict[str, Any]]:
        items = []
        try:
            entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.name in ignore_dirs:
                    continue
                rel_path = os.path.relpath(entry.path, abs_root).replace("\\", "/")
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "is_dir": True,
                        "children": build_tree(entry.path)
                    })
                else:
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "is_dir": False,
                        "size": entry.stat().st_size
                    })
        except Exception:
            pass
        return items

    return {"workspace": abs_root, "tree": build_tree(abs_root)}

@router.post("/files/read")
async def read_file(req: FileReadRequest):
    """Reads content of a workspace file."""
    abs_path = os.path.abspath(os.path.join(req.workspace_path, req.file_path))
    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
        raise HTTPException(status_code=404, detail=f"File '{req.file_path}' not found.")
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"file_path": req.file_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.post("/files/write")
async def write_file(req: FileWriteRequest):
    """Creates or updates a workspace file."""
    abs_path = os.path.abspath(os.path.join(req.workspace_path, req.file_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "file_path": req.file_path, "bytes": len(req.content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")

@router.post("/sandbox/exec")
async def execute_sandbox_command(req: TerminalExecRequest):
    """Runs a command directly inside the workspace sandbox."""
    sandbox = DockerSandboxManager(req.workspace_path)
    result = sandbox.execute_command(req.command)
    return result
