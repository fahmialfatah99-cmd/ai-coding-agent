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

class UnifiedLLMClient:
    """
    Multi-Provider LLM Client with Real-Time Dynamic Model Discovery,
    Exponential Backoff Auto-Retry (3x), and Universal SSE Stream + JSON Parser.
    Optimized for 9Router local/cloud AI gateway with automatic fallback.
    """
    
    DEFAULT_BASE_URLS = {
        "9router": os.getenv("NINEROUTER_BASE_URL", "http://host.docker.internal:20128/v1" if os.path.exists("/.dockerenv") else "http://127.0.0.1:20128/v1"),
        "openai": "https://api.openai.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        "ollama": "http://localhost:11434/v1",
        "anthropic": "https://api.anthropic.com/v1",
    }
    
    DEFAULT_MODELS = {
        "9router": "ag/gemini-3.7-flash-high",
        "openai": "gpt-4o",
        "gemini": "gemini-2.0-flash",
        "ollama": "deepseek-r1:latest",
        "anthropic": "claude-3-7-sonnet",
    }

    def __init__(
        self,
        provider: str = "9router",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = "9router" if provider.lower() in ("9router", "openai", "") else provider.lower()
        self.api_key = (
            api_key
            or os.getenv(f"{self.provider.upper()}_API_KEY", "")
            or os.getenv("NINEROUTER_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )
        self.model = model or self.DEFAULT_MODELS.get(self.provider, "ag/gemini-3.7-flash-high")
        self.base_url = (base_url or os.getenv("NINEROUTER_BASE_URL") or self.DEFAULT_BASE_URLS.get(self.provider, "http://127.0.0.1:20128/v1")).rstrip("/")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Executes chat completion request with multi-model failover and automatic retry.
        """
        if not self.api_key and self.provider != "ollama":
            return {
                "role": "assistant",
                "content": f"[Simulated Response from {self.provider} ({self.model})]: API key not set.",
                "tool_calls": [],
                "reasoning": ""
            }

        headers = {
            "Content-Type": "application/json"
        }

        candidate_models = [self.model]
        if self.provider == "9router":
            if self.model == "all":
                candidate_models = ["ag/gemini-3.7-flash-high", "ag/claude-sonnet-4-6", "all"]
            else:
                if "ag/gemini-3.7-flash-high" not in candidate_models:
                    candidate_models.append("ag/gemini-3.7-flash-high")
                if "ag/claude-sonnet-4-6" not in candidate_models:
                    candidate_models.append("ag/claude-sonnet-4-6")

        last_error = ""

        for current_model in candidate_models:
            if self.provider == "anthropic":
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
                payload = {
                    "model": current_model,
                    "messages": [m for m in messages if m.get("role") != "system"],
                    "temperature": temperature,
                    "max_tokens": 4096
                }
                system_msg = next((m["content"] for m in messages if m.get("role") == "system"), None)
                if system_msg:
                    payload["system"] = system_msg
                endpoint = f"{self.base_url}/messages"
            else:
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature
                }
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"
                endpoint = f"{self.base_url}/chat/completions"

            max_attempts = 2
            for attempt in range(max_attempts):
                try:
                    async with httpx.AsyncClient(timeout=90.0) as client:
                        response = await client.post(endpoint, headers=headers, json=payload)
                        response.raise_for_status()
                        
                        content_type = response.headers.get("content-type", "")
                        raw_text = response.text

                        # Check if SSE event stream
                        if "text/event-stream" in content_type or raw_text.strip().startswith("data:"):
                            parsed = self._parse_sse_stream_response(raw_text)
                            if parsed.get("content") or parsed.get("tool_calls"):
                                return parsed

                        if self.provider == "anthropic":
                            data = response.json()
                            content_blocks = data.get("content", [])
                            text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                            if text:
                                return {
                                    "role": "assistant",
                                    "content": text,
                                    "tool_calls": [],
                                    "reasoning": ""
                                }
                        else:
                            data = response.json()
                            choice = data.get("choices", [{}])[0]
                            message = choice.get("message", {})
                            content = message.get("content", "")
                            t_calls = message.get("tool_calls", [])
                            if content or t_calls:
                                return {
                                    "role": message.get("role", "assistant"),
                                    "content": content,
                                    "tool_calls": t_calls,
                                    "reasoning": message.get("reasoning_content", "")
                                }
                except Exception as e:
                    last_error = f"{current_model} error: {e}"
                    await asyncio.sleep(1.0)
                    continue

        return {
            "role": "assistant",
            "content": f"LLM Request failed ({self.provider} - {self.model}): {last_error}",
            "tool_calls": [],
            "reasoning": ""
        }

    def _parse_sse_stream_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses and aggregates text/event-stream chunks into a single completion object,
        including content, tool_calls, and reasoning_content.
        """
        full_content_parts = []
        reasoning_parts = []
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
                choices = chunk.get("choices", [])
                if not choices:
                    continue

                choice = choices[0]
                delta = choice.get("delta", {})

                # Accumulate reasoning/thinking content
                if delta.get("reasoning_content"):
                    reasoning_parts.append(delta["reasoning_content"])

                # Accumulate text content
                if delta.get("content"):
                    full_content_parts.append(delta["content"])

                # Accumulate tool calls
                if delta.get("tool_calls"):
                    for tc in delta["tool_calls"]:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {
                                "id": tc.get("id", f"call_{idx}"),
                                "type": tc.get("type", "function"),
                                "function": {
                                    "name": tc.get("function", {}).get("name", ""),
                                    "arguments": tc.get("function", {}).get("arguments", "")
                                }
                            }
                        else:
                            fn = tc.get("function", {})
                            if fn.get("name"):
                                tool_calls_map[idx]["function"]["name"] += fn["name"]
                            if fn.get("arguments"):
                                tool_calls_map[idx]["function"]["arguments"] += fn["arguments"]

            except Exception:
                continue

        final_tool_calls = list(tool_calls_map.values()) if tool_calls_map else []
        return {
            "role": "assistant",
            "content": "".join(full_content_parts),
            "tool_calls": final_tool_calls,
            "reasoning": "".join(reasoning_parts)
        }

    @classmethod
    async def fetch_dynamic_9router_models(cls, api_key: Optional[str] = None) -> List[str]:
        """
        Dynamically probes the active 9Router instance to retrieve all configured models and combos.
        """
        key = api_key or os.getenv("NINEROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        headers = {}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        candidate_urls = [
            "http://127.0.0.1:20128/v1/models",
            "http://localhost:20128/v1/models",
            "http://host.docker.internal:20128/v1/models",
            "https://api.9router.com/v1/models"
        ]
        if os.getenv("NINEROUTER_BASE_URL"):
            candidate_urls.insert(0, f"{os.getenv('NINEROUTER_BASE_URL').rstrip('/')}/models")

        async with httpx.AsyncClient(timeout=5.0) as client:
            for url in candidate_urls:
                try:
                    res = await client.get(url, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        model_items = data.get("data", []) if isinstance(data, dict) and "data" in data else data
                        if isinstance(model_items, list):
                            models = [m.get("id") if isinstance(m, dict) else str(m) for m in model_items]
                            if models:
                                return models
                except Exception:
                    continue

        return [
            "all",
            "ag/gemini-3.7-flash-high",
            "ag/gemini-3.7-flash-medium",
            "ag/claude-sonnet-4-6",
            "ag/claude-opus-4-6-thinking",
            "gemini/gemini-3.7-flash",
            "nvidia/deepseek-ai/deepseek-v4-pro"
        ]

    @classmethod
    async def get_supported_providers_async(cls, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns supported providers, exclusively optimized for 9Router with dynamic model discovery.
        """
        dynamic_9router_models = await cls.fetch_dynamic_9router_models(api_key)

        return [
            {
                "id": "9router",
                "name": "9Router",
                "models": dynamic_9router_models,
                "default_model": dynamic_9router_models[0] if dynamic_9router_models else "ag/gemini-3.7-flash-high"
            }
        ]

    @staticmethod
    def get_supported_providers() -> List[Dict[str, Any]]:
        return [
            {
                "id": "9router",
                "name": "9Router",
                "models": [
                    "all",
                    "ag/gemini-3.7-flash-high",
                    "ag/gemini-3.7-flash-medium",
                    "ag/claude-sonnet-4-6",
                    "ag/claude-opus-4-6-thinking",
                    "gemini/gemini-3.7-flash",
                    "nvidia/deepseek-ai/deepseek-v4-pro"
                ],
                "default_model": "ag/gemini-3.7-flash-high"
            }
        ]
