import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/files", tags=["File System & Explorer"])

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

@router.get("")
async def get_file_tree(workspace_path: str = Query("./workspace")):
    """Recursively lists files and directories in the workspace."""
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

@router.post("/read")
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

@router.post("/write")
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

@router.post("/delete")
async def delete_file(req: FileDeleteRequest):
    """Deletes a file from the workspace."""
    abs_path = os.path.abspath(os.path.join(req.workspace_path, req.file_path))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        if os.path.isdir(abs_path):
            import shutil
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
        return {"status": "deleted", "file_path": req.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
