import json
import os
import asyncio
from typing import List, Dict, Any, Optional
import httpx

class UnifiedLLMClient:
    """
    Multi-Provider LLM Client with Real-Time Dynamic Model Discovery,
    Exponential Backoff Auto-Retry (3x), and Universal SSE Stream + JSON Parser.
    Optimized for 9Router local/cloud AI gateway with automatic fallback.
    """
    
    DEFAULT_BASE_URLS = {
        "9router": "http://localhost:20128/v1",
        "openai": "https://api.openai.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        "ollama": "http://localhost:11434/v1",
        "anthropic": "https://api.anthropic.com/v1",
    }
    
    DEFAULT_MODELS = {
        "9router": "all",
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
        self.provider = provider.lower()
        self.api_key = (
            api_key
            or os.getenv(f"{self.provider.upper()}_API_KEY", "")
            or os.getenv("NINEROUTER_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )
        self.model = model or self.DEFAULT_MODELS.get(self.provider, "all")
        self.base_url = (base_url or self.DEFAULT_BASE_URLS.get(self.provider, "http://localhost:20128/v1")).rstrip("/")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Executes chat completion request with 3x Exponential Backoff Retry on network/timeout/rate-limit issues.
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

        if self.provider == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
            payload = {
                "model": self.model,
                "messages": [m for m in messages if m.get("role") != "system"],
                "temperature": temperature,
                "max_tokens": 4096
            }
            system_msg = next((m["content"] for m in messages if m.get("role") == "system"), None)
            if system_msg:
                payload["system"] = system_msg
            endpoint = f"{self.base_url}/messages"
        else:
            # 9Router / OpenAI / Gemini / Ollama (OpenAI-compatible format)
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            endpoint = f"{self.base_url}/chat/completions"

        max_retries = 3
        backoff_delays = [1.0, 2.5, 5.0]
        last_error = ""

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(endpoint, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    content_type = response.headers.get("content-type", "")
                    raw_text = response.text

                    # Check if the gateway returned an SSE event stream (e.g. 9Router default behavior)
                    if "text/event-stream" in content_type or raw_text.strip().startswith("data:"):
                        return self._parse_sse_stream_response(raw_text)

                    if self.provider == "anthropic":
                        data = response.json()
                        content_blocks = data.get("content", [])
                        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
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
                        return {
                            "role": message.get("role", "assistant"),
                            "content": message.get("content", ""),
                            "tool_calls": message.get("tool_calls", []),
                            "reasoning": message.get("reasoning_content", "")
                        }
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_delays[attempt])
                    continue
                else:
                    break

        return {
            "role": "assistant",
            "content": f"LLM Request failed after {max_retries} automatic retries ({self.provider} - {self.model}): {last_error}",
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
            "http://localhost:20128/v1/models",
            "http://127.0.0.1:20128/v1/models",
            "https://api.9router.com/v1/models"
        ]

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
        Returns full provider list with dynamically detected 9Router combos and models.
        """
        dynamic_9router_models = await cls.fetch_dynamic_9router_models(api_key)

        return [
            {
                "id": "9router",
                "name": "9Router (Auto-Detected Combos)",
                "models": dynamic_9router_models,
                "default_model": dynamic_9router_models[0] if dynamic_9router_models else "all"
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "default_model": "gemini-2.0-flash"
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
                "default_model": "gpt-4o"
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "models": ["claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"],
                "default_model": "claude-3-7-sonnet"
            },
            {
                "id": "ollama",
                "name": "Ollama / Local LLM",
                "models": ["deepseek-r1:latest", "qwen2.5-coder:latest", "llama3.3:latest"],
                "default_model": "deepseek-r1:latest"
            }
        ]

    @staticmethod
    def get_supported_providers() -> List[Dict[str, Any]]:
        return [
            {
                "id": "9router",
                "name": "9Router (Auto-Detected Combos)",
                "models": ["all", "ag/gemini-3.7-flash-high", "ag/claude-sonnet-4-6", "nvidia/deepseek-ai/deepseek-v4-pro"],
                "default_model": "all"
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "default_model": "gemini-2.0-flash"
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
                "default_model": "gpt-4o"
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "models": ["claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"],
                "default_model": "claude-3-7-sonnet"
            },
            {
                "id": "ollama",
                "name": "Ollama / Local LLM",
                "models": ["deepseek-r1:latest", "qwen2.5-coder:latest", "llama3.3:latest"],
                "default_model": "deepseek-r1:latest"
            }
        ]
