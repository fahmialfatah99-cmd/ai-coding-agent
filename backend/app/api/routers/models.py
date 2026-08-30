from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

try:
    from ...engine.llm_adapter import UnifiedLLMClient
except ImportError:
    from app.engine.llm_adapter import UnifiedLLMClient

router = APIRouter(prefix="/models", tags=["LLM Models & Providers"])

class ProviderInfo(BaseModel):
    id: str
    name: str
    models: List[str]
    default_model: str

@router.get("", response_model=Dict[str, List[Dict[str, Any]]])
async def list_models():
    """Returns available LLM providers (OpenAI, Gemini, Claude, Ollama) and supported models."""
    return {"providers": UnifiedLLMClient.get_supported_providers()}

@router.get("/active")
async def get_active_model_defaults():
    """Returns default model configurations."""
    return {
        "default_provider": "gemini",
        "default_model": "gemini-2.0-flash",
        "supported_providers": UnifiedLLMClient.get_supported_providers()
    }
