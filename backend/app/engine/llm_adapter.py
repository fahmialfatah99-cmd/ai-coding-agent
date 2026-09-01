import json
import os
import asyncio
from typing import List, Dict, Any, Optional
import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Provider catalog
# ---------------------------------------------------------------------------
# Every provider is described by:
#   - id: stable slug used in URLs / API requests
#   - name: human-readable label shown in the model picker
#   - base_url: OpenAI-compatible endpoint (or Anthropic native endpoint)
#   - api_style: "openai" (chat/completions) or "anthropic" (messages)
#   - api_key_env: ordered list of env var names that may contain the key
#   - default_model: hardcoded default if discovery fails
#   - fallback_models: hardcoded catalog used when /models discovery fails
#   - requires_api_key: if False, the provider can be used without auth
#   - description: short blurb shown in the UI
# ---------------------------------------------------------------------------
PROVIDER_CATALOG: Dict[str, Dict[str, Any]] = {
    "9router": {
        "id": "9router",
        "name": "9Router (Auto-Detect Combos)",
        "base_url": os.getenv("NINEROUTER_BASE_URL", "http://127.0.0.1:20128/v1"),
        "api_style": "openai",
        "api_key_env": ["NINEROUTER_API_KEY", "OPENAI_API_KEY"],
        "default_model": "ag/gemini-3.7-flash-high",
        "fallback_models": [
            "all",
            "ag/gemini-3.7-flash-high",
            "ag/gemini-3.7-flash-medium",
            "ag/gemini-3.5-flash-high",
            "ag/gemini-3.6-flash-high",
            "ag/gemini-3-flash-agent",
            "ag/gemini-3-flash",
            "ag/claude-sonnet-4-6",
            "ag/claude-opus-4-6-thinking",
            "gemini/gemini-3.7-flash",
            "nvidia/deepseek-ai/deepseek-v4-pro",
        ],
        "requires_api_key": False,
        "description": "Local AI Gateway with auto-detected combos (Claude, Gemini, DeepSeek, GPT, Ollama).",
    },
    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "api_style": "openai",
        "api_key_env": ["OPENAI_API_KEY"],
        "default_model": "gpt-4o",
        "fallback_models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "o1",
            "o1-mini",
            "o1-pro",
            "o3",
            "o3-mini",
            "o4-mini",
        ],
        "requires_api_key": True,
        "description": "OpenAI GPT-4o, GPT-5, o1/o3 reasoning models.",
    },
    "gemini": {
        "id": "gemini",
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "api_style": "openai",
        "api_key_env": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "default_model": "gemini-2.0-flash",
        "fallback_models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
        "requires_api_key": True,
        "description": "Google Gemini 2.5 / 2.0 / 1.5 family via OpenAI-compatible endpoint.",
    },
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "api_style": "anthropic",
        "api_key_env": ["ANTHROPIC_API_KEY"],
        "default_model": "claude-3-7-sonnet-latest",
        "fallback_models": [
            "claude-opus-4-1-20250805",
            "claude-opus-4-20250514",
            "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-20250514",
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-opus-20240229",
        ],
        "requires_api_key": True,
        "description": "Anthropic Claude 4.x / 3.x with native API + extended thinking.",
    },
    "ollama": {
        "id": "ollama",
        "name": "Ollama (Local)",
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
        "api_style": "openai",
        "api_key_env": ["OLLAMA_API_KEY"],
        "default_model": "deepseek-r1:latest",
        "fallback_models": [
            "llama3.3:latest",
            "llama3.2:latest",
            "llama3.1:70b",
            "qwen2.5-coder:32b",
            "qwen2.5:72b",
            "deepseek-r1:latest",
            "deepseek-coder-v2:latest",
            "codellama:34b",
            "mistral:latest",
            "mixtral:8x22b",
            "gemma3:27b",
            "phi3:14b",
        ],
        "requires_api_key": False,
        "description": "Ollama local models (Llama, Qwen, DeepSeek, Mistral, Gemma, Phi).",
    },
    "groq": {
        "id": "groq",
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_style": "openai",
        "api_key_env": ["GROQ_API_KEY"],
        "default_model": "llama-3.3-70b-versatile",
        "fallback_models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-3.2-90b-vision-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "deepseek-r1-distill-llama-70b",
            "qwen-2.5-32b",
        ],
        "requires_api_key": True,
        "description": "Groq ultra-fast inference (LPU) for Llama, Mixtral, Gemma, Qwen, DeepSeek.",
    },
    "mistral": {
        "id": "mistral",
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "api_style": "openai",
        "api_key_env": ["MISTRAL_API_KEY"],
        "default_model": "mistral-large-latest",
        "fallback_models": [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "codestral-latest",
            "pixtral-large-latest",
            "ministral-8b-latest",
            "ministral-3b-latest",
        ],
        "requires_api_key": True,
        "description": "Mistral Large, Medium, Small, Codestral, Pixtral — all OpenAI-compatible.",
    },
    "cohere": {
        "id": "cohere",
        "name": "Cohere",
        "base_url": "https://api.cohere.com/v1",
        "api_style": "openai",
        "api_key_env": ["COHERE_API_KEY", "CO_API_KEY"],
        "default_model": "command-r-plus",
        "fallback_models": [
            "command-r-plus",
            "command-r",
            "command",
            "command-light",
            "c4ai-aya-expanse-32b",
            "c4ai-aya-expanse-8b",
        ],
        "requires_api_key": True,
        "description": "Cohere Command R+ / R / Aya Expanse via OpenAI-compatible endpoint.",
    },
    "together": {
        "id": "together",
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "api_style": "openai",
        "api_key_env": ["TOGETHER_API_KEY"],
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "fallback_models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-V3",
            "mistralai/Mixtral-8x22B-Instruct-v0.1",
            "google/gemma-2-27b-it",
        ],
        "requires_api_key": True,
        "description": "Together AI — open models (Llama, Qwen, DeepSeek, Mixtral, Gemma) at low cost.",
    },
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_style": "openai",
        "api_key_env": ["DEEPSEEK_API_KEY"],
        "default_model": "deepseek-chat",
        "fallback_models": [
            "deepseek-chat",
            "deepseek-reasoner",
            "deepseek-coder",
        ],
        "requires_api_key": True,
        "description": "DeepSeek V3 (chat) and R1 (reasoner) — OpenAI-compatible API.",
    },
    "openrouter": {
        "id": "openrouter",
        "name": "OpenRouter (All Models)",
        "base_url": "https://openrouter.ai/api/v1",
        "api_style": "openai",
        "api_key_env": ["OPENROUTER_API_KEY"],
        "default_model": "anthropic/claude-3.7-sonnet",
        "fallback_models": [
            "anthropic/claude-3.7-sonnet",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/o1",
            "openai/o3-mini",
            "google/gemini-2.5-pro",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.3-70b-instruct",
            "meta-llama/llama-3.1-405b-instruct",
            "qwen/qwen-2.5-72b-instruct",
            "deepseek/deepseek-r1",
            "deepseek/deepseek-chat",
            "mistralai/mistral-large-latest",
        ],
        "requires_api_key": True,
        "description": "OpenRouter — 100+ models from all major providers through one API key.",
    },
}


def _resolve_api_key(provider_id: str, override: Optional[str] = None) -> str:
    """Pick the first non-empty API key for a provider from override + env vars."""
    if override:
        return override
    cfg = PROVIDER_CATALOG.get(provider_id, {})
    for env_name in cfg.get("api_key_env", []):
        val = os.getenv(env_name, "")
        if val:
            return val
    return ""


def _normalize_provider(provider: Optional[str]) -> str:
    """Normalize any provider string to a known catalog id, defaulting to 9router."""
    if not provider:
        return "9router"
    p = provider.strip().lower()
    aliases = {
        "9": "9router",
        "9router": "9router",
        "9-router": "9router",
        "ninerouter": "9router",
        "claude": "anthropic",
        "google": "gemini",
        "local": "ollama",
        "llama": "ollama",
    }
    if p in PROVIDER_CATALOG:
        return p
    return aliases.get(p, "9router")


class UnifiedLLMClient:
    """
    Multi-Provider LLM Client with Real-Time Dynamic Model Discovery,
    Exponential Backoff Auto-Retry, and Universal SSE Stream + JSON Parser.
    Supports 9Router, OpenAI, Gemini, Anthropic, Ollama, Groq, Mistral,
    Cohere, Together AI, DeepSeek, and OpenRouter.
    """

    def __init__(
        self,
        provider: str = "9router",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = _normalize_provider(provider)
        cfg = PROVIDER_CATALOG[self.provider]
        self.api_style = cfg["api_style"]
        self.api_key = _resolve_api_key(self.provider, api_key)
        self.model = model or cfg["default_model"]
        # If base_url is overridden (e.g. via env or user input), respect it; otherwise use catalog.
        # 9Router's base_url is dynamic (env var) so we re-resolve it.
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif self.provider == "9router":
            self.base_url = os.getenv(
                "NINEROUTER_BASE_URL",
                "http://host.docker.internal:20128/v1" if os.path.exists("/.dockerenv") else "http://127.0.0.1:20128/v1",
            ).rstrip("/")
        elif self.provider == "ollama":
            self.base_url = os.getenv("OLLAMA_BASE_URL", cfg["base_url"]).rstrip("/")
        else:
            self.base_url = cfg["base_url"].rstrip("/")

        self.requires_api_key = cfg.get("requires_api_key", True)

    # ---------------------------------------------------------------------
    # Chat completion (main entrypoint used by the orchestrator)
    # ---------------------------------------------------------------------
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Executes chat completion request with multi-model failover and automatic retry.
        """
        # 9Router & Ollama can run without a key; everything else needs one.
        if not self.api_key and self.requires_api_key:
            return {
                "role": "assistant",
                "content": (
                    f"[Missing API key for provider '{self.provider}']. "
                    f"Set one of: {', '.join(PROVIDER_CATALOG[self.provider].get('api_key_env', []))} "
                    f"in the backend .env, or pass api_key in the request body."
                ),
                "tool_calls": [],
                "reasoning": "",
            }

        # Build candidate list: prefer self.model, then a handful of reliable fallbacks
        # so a transient failure on the primary model still returns an answer.
        candidate_models = [self.model]
        if self.provider == "9router":
            for rm in PROVIDER_CATALOG["9router"]["fallback_models"]:
                if rm not in candidate_models:
                    candidate_models.append(rm)

        last_error = ""

        for current_model in candidate_models:
            request_headers, payload, endpoint = self._build_request(
                current_model, messages, tools, temperature
            )

            # Anthropic can stream SSE; the rest come back as JSON or SSE depending on the gateway.
            max_attempts = 2
            for attempt in range(max_attempts):
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            endpoint, headers=request_headers, json=payload
                        )
                        if response.status_code >= 400:
                            # Capture the upstream error verbatim so users can debug
                            # quota, model-not-found, bad API key, etc.
                            try:
                                err_body = response.json()
                            except Exception:
                                err_body = {"raw": response.text[:500]}
                            last_error = (
                                f"{current_model} -> HTTP {response.status_code}: "
                                f"{json.dumps(err_body)[:300]}"
                            )
                            # Don't retry for client errors (bad model / bad key) — bail out fast.
                            if 400 <= response.status_code < 500 and response.status_code != 429:
                                break
                            await asyncio.sleep(1.0)
                            continue

                        content_type = response.headers.get("content-type", "")
                        raw_text = response.text

                        # SSE event stream (9Router, some Anthropic proxies, OpenRouter streaming)
                        if "text/event-stream" in content_type or raw_text.strip().startswith("data:"):
                            parsed = self._parse_sse_stream_response(raw_text)
                            if parsed.get("content") or parsed.get("tool_calls") or parsed.get("reasoning"):
                                return parsed
                            # Stream was empty — try next model.
                            last_error = f"{current_model}: empty SSE stream"
                            break

                        # Native Anthropic JSON (non-streaming /v1/messages)
                        if self.api_style == "anthropic":
                            data = response.json()
                            content_blocks = data.get("content", [])
                            text = "".join(
                                b.get("text", "") for b in content_blocks if b.get("type") == "text"
                            )
                            # Anthropic also surfaces a `thinking` block — surface it as reasoning
                            reasoning = "".join(
                                b.get("thinking", "") for b in content_blocks if b.get("type") == "thinking"
                            )
                            tool_blocks = [b for b in content_blocks if b.get("type") == "tool_use"]
                            tool_calls = [
                                {
                                    "id": b.get("id", f"call_{i}"),
                                    "type": "function",
                                    "function": {
                                        "name": b.get("name", ""),
                                        "arguments": json.dumps(b.get("input", {})),
                                    },
                                }
                                for i, b in enumerate(tool_blocks)
                            ]
                            if text or tool_calls:
                                return {
                                    "role": "assistant",
                                    "content": text,
                                    "tool_calls": tool_calls,
                                    "reasoning": reasoning,
                                }
                            last_error = f"{current_model}: empty anthropic response"
                            break

                        # Standard OpenAI-compatible JSON
                        data = response.json()
                        choice = (data.get("choices") or [{}])[0]
                        message = choice.get("message", {}) or {}
                        content = message.get("content", "") or ""
                        t_calls = message.get("tool_calls") or []
                        reasoning = (
                            message.get("reasoning_content")
                            or message.get("reasoning")
                            or ""
                        )
                        if content or t_calls:
                            return {
                                "role": message.get("role", "assistant"),
                                "content": content,
                                "tool_calls": t_calls,
                                "reasoning": reasoning,
                            }
                        last_error = f"{current_model}: empty response"
                        break
                except Exception as e:
                    last_error = f"{current_model} error: {e}"
                    await asyncio.sleep(1.0)
                    continue

        return {
            "role": "assistant",
            "content": f"LLM Request failed ({self.provider} - {self.model}): {last_error}",
            "tool_calls": [],
            "reasoning": "",
        }

    # ---------------------------------------------------------------------
    # Per-provider request builder
    # ---------------------------------------------------------------------
    def _build_request(
        self,
        current_model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
    ):
        """Returns (headers, payload, endpoint) for a single chat-completion call."""
        headers: Dict[str, str] = {"Content-Type": "application/json"}

        if self.api_style == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
            payload: Dict[str, Any] = {
                "model": current_model,
                "messages": [m for m in messages if m.get("role") != "system"],
                "temperature": temperature,
                "max_tokens": 8192,
            }
            system_msg = next(
                (m["content"] for m in messages if m.get("role") == "system"), None
            )
            if system_msg:
                payload["system"] = system_msg
            if tools:
                # Convert OpenAI-style tool defs to Anthropic tool defs.
                payload["tools"] = [
                    {
                        "name": t["function"]["name"],
                        "description": t["function"].get("description", ""),
                        "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}}),
                    }
                    for t in tools
                    if t.get("type") == "function"
                ]
            endpoint = f"{self.base_url}/messages"
            return headers, payload, endpoint

        # OpenAI-compatible path (used by 9Router, OpenAI, Gemini, Ollama, Groq, Mistral,
        # Cohere, Together, DeepSeek, OpenRouter)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.provider == "openrouter":
            # OpenRouter recommends sending these to identify the app.
            headers["HTTP-Referer"] = os.getenv("OPENROUTER_REFERER", "https://ai-coding-agent.local")
            headers["X-Title"] = os.getenv("OPENROUTER_TITLE", "AI Coding Agent")
        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,  # We use non-stream by default; orchestrator streams SSE downstream.
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        endpoint = f"{self.base_url}/chat/completions"
        return headers, payload, endpoint

    # ---------------------------------------------------------------------
    # SSE parser
    # ---------------------------------------------------------------------
    def _parse_sse_stream_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses and aggregates text/event-stream chunks into a single completion object,
        including content, tool_calls, and reasoning_content. Compatible with both
        OpenAI delta format and Anthropic event format.
        """
        full_content_parts: List[str] = []
        reasoning_parts: List[str] = []
        tool_calls_map: Dict[int, Dict[str, Any]] = {}

        for line in raw_text.splitlines():
            line = line.strip()
            if not line.startswith("data:") or line.startswith("data: [DONE]"):
                continue

            json_str = line[5:].strip()
            if not json_str:
                continue

            try:
                chunk = json.loads(json_str)
            except Exception:
                continue

            # ---- OpenAI-style delta ----
            choices = chunk.get("choices")
            if choices:
                choice = choices[0]
                delta = choice.get("delta", {}) or {}
                # Some providers (DeepSeek R1, 9Router combos) stream reasoning_content
                if delta.get("reasoning_content"):
                    reasoning_parts.append(delta["reasoning_content"])
                if delta.get("reasoning"):
                    reasoning_parts.append(delta["reasoning"])
                if delta.get("content"):
                    full_content_parts.append(delta["content"])
                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {
                            "id": tc.get("id", f"call_{idx}"),
                            "type": tc.get("type", "function"),
                            "function": {
                                "name": (tc.get("function") or {}).get("name", ""),
                                "arguments": (tc.get("function") or {}).get("arguments", ""),
                            },
                        }
                    else:
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            tool_calls_map[idx]["function"]["name"] += fn["name"]
                        if fn.get("arguments"):
                            tool_calls_map[idx]["function"]["arguments"] += fn["arguments"]
                continue

            # ---- Anthropic event-stream format (content_block_delta etc.) ----
            ev_type = chunk.get("type")
            if ev_type == "content_block_delta":
                delta = chunk.get("delta", {}) or {}
                if delta.get("type") == "text_delta":
                    full_content_parts.append(delta.get("text", ""))
                elif delta.get("type") == "thinking_delta":
                    reasoning_parts.append(delta.get("thinking", ""))
                elif delta.get("type") == "input_json_delta":
                    idx = chunk.get("index", 0)
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {
                            "id": f"call_{idx}",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    tool_calls_map[idx]["function"]["arguments"] += delta.get("partial_json", "")
            elif ev_type == "content_block_start":
                block = chunk.get("content_block") or {}
                if block.get("type") == "tool_use":
                    idx = chunk.get("index", 0)
                    tool_calls_map[idx] = {
                        "id": block.get("id", f"call_{idx}"),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": "",
                        },
                    }
            elif ev_type == "message_delta":
                # Stop reason / usage — nothing to extract for content.
                pass

        final_tool_calls = list(tool_calls_map.values()) if tool_calls_map else []
        return {
            "role": "assistant",
            "content": "".join(full_content_parts),
            "tool_calls": final_tool_calls,
            "reasoning": "".join(reasoning_parts),
        }

    # ---------------------------------------------------------------------
    # Model discovery
    # ---------------------------------------------------------------------
    @classmethod
    async def fetch_dynamic_models(
        cls,
        provider_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> List[str]:
        """
        Tries the provider's /v1/models endpoint to discover models live.
        Falls back to the hardcoded catalog on any failure.
        """
        cfg = PROVIDER_CATALOG.get(_normalize_provider(provider_id))
        if not cfg:
            return []
        key = _resolve_api_key(_normalize_provider(provider_id), api_key)
        headers: Dict[str, str] = {}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        # Build a list of candidate /models URLs to probe.
        base = (base_url or cfg["base_url"]).rstrip("/")
        candidates = [f"{base}/models"]
        # 9Router: also try common host aliases so docker / windows / linux all work.
        if _normalize_provider(provider_id) == "9router":
            candidates = [
                "http://127.0.0.1:20128/v1/models",
                "http://localhost:20128/v1/models",
                "http://host.docker.internal:20128/v1/models",
                f"{base}/models",
            ]
            if os.getenv("NINEROUTER_BASE_URL"):
                candidates.insert(0, f"{os.getenv('NINEROUTER_BASE_URL').rstrip('/')}/models")
        # Ollama has a custom /api/tags endpoint; translate to OpenAI-style list.
        if _normalize_provider(provider_id) == "ollama":
            candidates = [f"{base.rstrip('/v1') if base.endswith('/v1') else base}/api/tags"]

        timeout = httpx.Timeout(5.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for url in candidates:
                try:
                    res = await client.get(url, headers=headers)
                    if res.status_code != 200:
                        continue
                    data = res.json()
                    # OpenAI shape: {"data": [{"id": "..."}]}
                    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                        models = [
                            m.get("id") if isinstance(m, dict) else str(m)
                            for m in data["data"]
                            if m
                        ]
                        if models:
                            return models
                    # Ollama shape: {"models": [{"name": "..."}]}
                    if isinstance(data, dict) and "models" in data and isinstance(data["models"], list):
                        models = [
                            m.get("name") if isinstance(m, dict) else str(m)
                            for m in data["models"]
                            if m
                        ]
                        if models:
                            return models
                    # Some gateways return a bare list.
                    if isinstance(data, list) and data:
                        models = [
                            m.get("id") if isinstance(m, dict) else str(m) for m in data
                        ]
                        if models:
                            return models
                except Exception:
                    continue

        # Fallback to hardcoded catalog
        return list(cfg.get("fallback_models", []))

    @classmethod
    async def fetch_dynamic_9router_models(cls, api_key: Optional[str] = None) -> List[str]:
        """Backward-compatible alias used by the old /models/sync-9router endpoint."""
        return await cls.fetch_dynamic_models("9router", api_key=api_key)

    @classmethod
    async def get_supported_providers_async(
        cls, api_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns the full provider catalog, with live model discovery for each provider
        (so the UI shows up-to-date model lists when a key is supplied).
        """
        providers: List[Dict[str, Any]] = []
        for pid, cfg in PROVIDER_CATALOG.items():
            models = await cls.fetch_dynamic_models(pid, api_key=api_key)
            # Ensure the default model is always present in the list.
            if cfg["default_model"] not in models:
                models = [cfg["default_model"]] + models
            providers.append(
                {
                    "id": pid,
                    "name": cfg["name"],
                    "models": models,
                    "default_model": cfg["default_model"],
                    "description": cfg.get("description", ""),
                    "requires_api_key": cfg.get("requires_api_key", True),
                    "api_style": cfg.get("api_style", "openai"),
                }
            )
        return providers

    @staticmethod
    def get_supported_providers() -> List[Dict[str, Any]]:
        """Sync variant used in tests & cold-start paths: returns the full catalog with fallback models."""
        return [
            {
                "id": pid,
                "name": cfg["name"],
                "models": list(cfg.get("fallback_models", [])),
                "default_model": cfg["default_model"],
                "description": cfg.get("description", ""),
                "requires_api_key": cfg.get("requires_api_key", True),
                "api_style": cfg.get("api_style", "openai"),
            }
            for pid, cfg in PROVIDER_CATALOG.items()
        ]
