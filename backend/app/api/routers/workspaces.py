import os
import shutil
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

class WorkspaceInitRequest(BaseModel):
    name: str
    root_path: Optional[str] = None

class WorkspaceInfo(BaseModel):
    id: str
    name: str
    root_path: str
    is_active: bool
    total_files: int
    size_bytes: int

@router.get("", response_model=List[Dict[str, Any]])
async def list_workspaces(base_dir: str = Query("./workspaces")):
    """Lists all available workspaces."""
    abs_base = os.path.abspath(base_dir)
    os.makedirs(abs_base, exist_ok=True)
    
    workspaces = []
    default_ws = os.path.abspath("./workspace")
    os.makedirs(default_ws, exist_ok=True)
    
    # Add default workspace
    workspaces.append({
        "id": "default",
        "name": "default-workspace",
        "root_path": default_ws,
        "is_active": True
    })
    
    try:
        for entry in os.scandir(abs_base):
            if entry.is_dir():
                workspaces.append({
                    "id": entry.name,
                    "name": entry.name,
                    "root_path": os.path.abspath(entry.path),
                    "is_active": False
                })
    except Exception:
        pass
        
    return workspaces

@router.post("/init")
async def init_workspace(req: WorkspaceInitRequest):
    """Initializes a new isolated project workspace."""
    safe_name = os.path.basename(req.name.strip().replace("\\", "/"))
    if not safe_name or safe_name in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid workspace name.")

    if req.root_path:
        target_path = os.path.abspath(req.root_path)
    else:
        target_path = os.path.abspath(os.path.join("./workspaces", safe_name))

    os.makedirs(target_path, exist_ok=True)
    
    # Initialize basic README
    readme_path = os.path.join(target_path, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# Workspace: {safe_name}\n\nCreated by AI Coding Agent.\n")
            
    return {
        "status": "created",
        "name": safe_name,
        "root_path": target_path
    }
