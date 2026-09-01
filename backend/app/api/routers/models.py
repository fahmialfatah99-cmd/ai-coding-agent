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
    description: Optional[str] = ""
    requires_api_key: Optional[bool] = True
    api_style: Optional[str] = "openai"


class SyncProviderRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@router.get("", response_model=Dict[str, List[ProviderInfo]])
async def list_models(api_key: Optional[str] = Query(None)):
    """
    Returns the full provider catalog (9Router, OpenAI, Gemini, Anthropic, Ollama,
    Groq, Mistral, Cohere, Together, DeepSeek, OpenRouter) with auto-discovered
    models when reachable.
    """
    providers = await UnifiedLLMClient.get_supported_providers_async(api_key=api_key)
    return {"providers": providers}


@router.get("/active")
async def get_active_model_defaults():
    """Returns default model configurations and the full supported provider list."""
    providers = await UnifiedLLMClient.get_supported_providers_async()
    first_model = providers[0]["models"][0] if providers and providers[0]["models"] else "all"
    return {
        "default_provider": "9router",
        "default_model": first_model,
        "supported_providers": providers,
    }


# ---------------------------------------------------------------------------
# Legacy endpoint kept for backwards compatibility (returns 9Router combo list).
# ---------------------------------------------------------------------------
@router.get("/sync-9router")
async def sync_9router(api_key: Optional[str] = Query(None)):
    """Forces real-time re-sync with the local/remote 9Router instance."""
    models = await UnifiedLLMClient.fetch_dynamic_9router_models(api_key=api_key)
    return {
        "status": "synchronized",
        "provider": "9router",
        "total_models": len(models),
        "models": models,
    }


# ---------------------------------------------------------------------------
# Generic sync — works for every provider in the catalog.
# ---------------------------------------------------------------------------
@router.post("/sync")
async def sync_provider(req: SyncProviderRequest):
    """Re-discovers live models for the given provider. Falls back to hardcoded catalog on failure."""
    models = await UnifiedLLMClient.fetch_dynamic_models(
        provider_id=req.provider,
        api_key=req.api_key,
        base_url=req.base_url,
    )
    return {
        "status": "synchronized",
        "provider": req.provider,
        "total_models": len(models),
        "models": models,
    }
