from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import datetime

router = APIRouter(prefix="/sessions", tags=["Chat Sessions & Memory"])

# In-memory session store with fallback
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

class CreateSessionRequest(BaseModel):
    title: str = "New Coding Session"
    workspace_path: str = "./workspace"
    provider: str = "openai"
    model: str = "gpt-4o"

class SaveMessageRequest(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None

@router.get("")
async def list_sessions():
    """Lists all active and historical chat sessions."""
    return {"sessions": list(ACTIVE_SESSIONS.values())}

@router.post("")
async def create_session(req: CreateSessionRequest):
    """Creates a new agent session."""
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "title": req.title,
        "workspace_path": req.workspace_path,
        "provider": req.provider,
        "model": req.model,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "messages": []
    }
    ACTIVE_SESSIONS[session_id] = session_data
    return session_data

@router.get("/{session_id}")
async def get_session(session_id: str):
    """Retrieves session messages and audit history."""
    if session_id not in ACTIVE_SESSIONS:
        # Create on the fly if not exists
        ACTIVE_SESSIONS[session_id] = {
            "id": session_id,
            "title": "Agent Session",
            "messages": []
        }
    return ACTIVE_SESSIONS[session_id]

@router.post("/{session_id}/messages")
async def add_message_to_session(session_id: str, msg: SaveMessageRequest):
    """Appends a message to the session history."""
    if session_id not in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS[session_id] = {"id": session_id, "messages": []}
        
    msg_entry = {
        "id": str(uuid.uuid4()),
        "role": msg.role,
        "content": msg.content,
        "tool_calls": msg.tool_calls,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    ACTIVE_SESSIONS[session_id]["messages"].append(msg_entry)
    return msg_entry
