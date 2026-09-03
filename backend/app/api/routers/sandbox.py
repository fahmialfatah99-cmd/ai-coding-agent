import os
import httpx
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

class GitHubConfigRequest(BaseModel):
    token: str
    username: Optional[str] = None
    email: Optional[str] = None
    remote_url: Optional[str] = None
    workspace_path: str = "./workspace"

@router.post("/exec")
async def execute_command(req: CommandExecRequest):
    """
    Executes a shell command (compiler, test runner, bash, git) inside the Docker sandbox
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

@router.post("/github-config")
async def configure_github(req: GitHubConfigRequest):
    """
    Validates GitHub Personal Access Token against GitHub API and sets git credentials.
    """
    if not req.token:
        raise HTTPException(status_code=400, detail="GitHub token is required.")

    # 1. Validate token with GitHub API
    headers = {
        "Authorization": f"Bearer {req.token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Coding-Agent"
    }
    
    user_data = {}
    oauth_scopes = ""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get("https://api.github.com/user", headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=401, detail=f"GitHub token invalid: {res.text}")
            user_data = res.json()
            oauth_scopes = res.headers.get("x-oauth-scopes", "")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to GitHub API: {str(e)}")

    gh_username = user_data.get("login") or req.username or "user"
    gh_email = req.email or user_data.get("email") or f"{gh_username}@users.noreply.github.com"
    gh_name = user_data.get("name") or gh_username

    sandbox = DockerSandboxManager(req.workspace_path)
    
    # 2. Configure Git user name and email safely without shell interpolation
    sandbox.execute_command_argv(["git", "config", "--global", "user.name", gh_name])
    sandbox.execute_command_argv(["git", "config", "--global", "user.email", gh_email])
    
    # 3. Configure remote URL with token if provided
    if req.remote_url:
        clean_url = req.remote_url.strip()
        if clean_url.startswith("https://"):
            # Strip existing user/token if present
            base_part = clean_url.split("@")[-1] if "@" in clean_url else clean_url.replace("https://", "")
            auth_url = f"https://{req.token}@{base_part}"
            sandbox.execute_command_argv(["git", "remote", "set-url", "origin", auth_url])

    return {
        "status": "connected",
        "username": gh_username,
        "name": gh_name,
        "avatar_url": user_data.get("avatar_url", ""),
        "email": gh_email,
        "scopes": oauth_scopes
    }

@router.get("/github-status")
async def github_status():
    """Returns local git config status."""
    sandbox = DockerSandboxManager("./workspace")
    user_res = sandbox.execute_command_argv(["git", "config", "--global", "user.name"])
    email_res = sandbox.execute_command_argv(["git", "config", "--global", "user.email"])
    remote_res = sandbox.execute_command_argv(["git", "remote", "-v"])
    
    return {
        "configured": bool(user_res.get("stdout", "").strip()),
        "user_name": user_res.get("stdout", "").strip(),
        "user_email": email_res.get("stdout", "").strip(),
        "remote": remote_res.get("stdout", "").strip()
    }
