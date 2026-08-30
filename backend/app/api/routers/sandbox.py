import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

try:
    from ...engine.docker_sandbox import DockerSandboxManager
except ImportError:
    from app.engine.docker_sandbox import DockerSandboxManager

router = APIRouter(prefix="/sandbox", tags=["Isolated Sandbox & Terminal"])

class CommandExecRequest(BaseModel):
    workspace_path: str = "./workspace"
    command: str
    timeout_sec: int = 30

@router.post("/exec")
async def execute_command(req: CommandExecRequest):
    """
    Executes a shell command (compiler, test runner, bash) inside the Docker sandbox
    or local fallback subprocess.
    """
    sandbox = DockerSandboxManager(req.workspace_path)
    result = sandbox.execute_command(req.command, timeout_sec=req.timeout_sec)
    return result

@router.get("/status")
async def sandbox_status(workspace_path: str = "./workspace"):
    """Checks the sandbox status and Docker daemon availability."""
    sandbox = DockerSandboxManager(workspace_path)
    return {
        "docker_available": sandbox.docker_client is not None,
        "workspace_path": os.path.abspath(workspace_path),
        "resource_limits": {
            "memory": sandbox.mem_limit,
            "cpu_quota": sandbox.cpu_quota
        }
    }
