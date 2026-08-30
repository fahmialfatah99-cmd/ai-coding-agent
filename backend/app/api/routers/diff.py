import os
import difflib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/diff", tags=["Diff & Patch Synthesizer"])

class DiffGenerateRequest(BaseModel):
    file_path: str
    original_code: str
    modified_code: str

class PatchApplyRequest(BaseModel):
    workspace_path: str = "./workspace"
    file_path: str
    target_string: str
    replacement_string: str

@router.post("/generate")
async def generate_diff(req: DiffGenerateRequest):
    """Generates a unified diff between original and modified code."""
    orig_lines = req.original_code.splitlines(keepends=True)
    mod_lines = req.modified_code.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{req.file_path}",
        tofile=f"b/{req.file_path}"
    )
    diff_text = "".join(diff)
    return {
        "file_path": req.file_path,
        "has_changes": len(diff_text) > 0,
        "unified_diff": diff_text
    }

@router.post("/patch")
async def apply_diff_patch(req: PatchApplyRequest):
    """Applies an atomic search-and-replace diff patch to a file."""
    abs_path = os.path.abspath(os.path.join(req.workspace_path, req.file_path))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"File '{req.file_path}' not found.")
        
    with open(abs_path, "r", encoding="utf-8") as f:
        current = f.read()

    if req.target_string not in current:
        raise HTTPException(status_code=400, detail="Target string not found in file.")

    updated = current.replace(req.target_string, req.replacement_string, 1)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(updated)

    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{req.file_path}",
        tofile=f"b/{req.file_path}"
    )

    return {
        "status": "success",
        "file_path": req.file_path,
        "diff": "".join(diff)
    }
