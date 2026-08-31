from fastapi import APIRouter, Query
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

@router.get("")
async def list_models(api_key: Optional[str] = Query(None)):
    """
    Returns live available LLM providers and auto-detects all 9Router combos and models.
    """
    providers = await UnifiedLLMClient.get_supported_providers_async(api_key=api_key)
    return {"providers": providers}

@router.get("/active")
async def get_active_model_defaults():
    """Returns default model configurations."""
    providers = await UnifiedLLMClient.get_supported_providers_async()
    first_model = providers[0]["models"][0] if providers and providers[0]["models"] else "all"
    return {
        "default_provider": "9router",
        "default_model": first_model,
        "supported_providers": providers
    }

@router.get("/sync-9router")
async def sync_9router(api_key: Optional[str] = Query(None)):
    """Forces real-time re-sync with local/remote 9Router instance."""
    models = await UnifiedLLMClient.fetch_dynamic_9router_models(api_key=api_key)
    return {
        "status": "synchronized",
        "total_models": len(models),
        "models": models
    }
