import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/files", tags=["File System & Explorer"])

def get_repo_root() -> str:
    curr = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):
        if os.path.exists(os.path.join(curr, "docker-compose.yml")) or os.path.exists(os.path.join(curr, ".git")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

def get_resolved_workspace(path: str = "./workspace") -> str:
    if os.path.isabs(path):
        resolved = os.path.abspath(path)
    else:
        base_dir = get_repo_root()
        clean_rel = path.lstrip("./").lstrip(".\\")
        resolved = os.path.abspath(os.path.join(base_dir, clean_rel))
    os.makedirs(resolved, exist_ok=True)
    return resolved

class FileReadRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str

class FileWriteRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str
    content: str

class FileDeleteRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str

@router.get("/workspaces")
async def list_available_workspaces():
    """
    Returns list of available top-level project folders for 1-click selection across Windows and Linux.
    """
    base_dir = get_repo_root()
    ignore_dirs = {".git", "node_modules", "__pycache__", ".next", ".pytest_cache", "venv", ".venv"}
    
    folders = []
    try:
        for entry in os.scandir(base_dir):
            if entry.is_dir() and entry.name not in ignore_dirs:
                folders.append({
                    "name": entry.name,
                    "path": f"./{entry.name}",
                    "abs_path": entry.path.replace("\\", "/")
                })
    except Exception:
        pass
        
    # Ensure default ./workspace is always included
    if not any(f["path"] == "./workspace" for f in folders):
        folders.insert(0, {
            "name": "workspace",
            "path": "./workspace",
            "abs_path": os.path.join(base_dir, "workspace").replace("\\", "/")
        })
        
    return {"workspaces": folders, "base_dir": base_dir.replace("\\", "/")}

@router.get("")
async def get_file_tree(workspace_path: str = Query("./workspace")):
    """Recursively lists files and directories in the workspace."""
    abs_root = get_resolved_workspace(workspace_path)

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

@router.post("/read")
async def read_file(req: FileReadRequest):
    """Reads content of a workspace file."""
    abs_root = get_resolved_workspace(req.workspace_path)
    abs_path = os.path.abspath(os.path.join(abs_root, req.file_path))
    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
        raise HTTPException(status_code=404, detail=f"File '{req.file_path}' not found at {abs_path}.")
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "file_path": req.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.post("/write")
async def write_file(req: FileWriteRequest):
    """Writes content to a workspace file."""
    abs_root = get_resolved_workspace(req.workspace_path)
    abs_path = os.path.abspath(os.path.join(abs_root, req.file_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "file_path": req.file_path, "bytes": len(req.content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing file: {str(e)}")

@router.post("/delete")
async def delete_file(req: FileDeleteRequest):
    """Deletes a file from workspace."""
    abs_root = get_resolved_workspace(req.workspace_path)
    abs_path = os.path.abspath(os.path.join(abs_root, req.file_path))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        if os.path.isdir(abs_path):
            import shutil
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
        return {"status": "success", "file_path": req.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
