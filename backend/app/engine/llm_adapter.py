import json
import os
from typing import List, Dict, Any, Optional
import httpx

class UnifiedLLMClient:
    """
    Multi-Provider LLM Client using asynchronous HTTP requests (httpx)
    supporting OpenAI, Google Gemini, Anthropic Claude, Ollama, and custom OpenAI-compatible endpoints.
    """
    
    DEFAULT_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
        "ollama": "http://localhost:11434/v1",
        "anthropic": "https://api.anthropic.com/v1",
    }
    
    DEFAULT_MODELS = {
        "openai": "gpt-4o",
        "gemini": "gemini-2.0-flash",
        "ollama": "deepseek-r1:latest",
        "anthropic": "claude-3-7-sonnet",
    }

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.api_key = (
            api_key
            or os.getenv(f"{self.provider.upper()}_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )
        self.model = model or self.DEFAULT_MODELS.get(self.provider, "gpt-4o")
        self.base_url = (base_url or self.DEFAULT_BASE_URLS.get(self.provider, "https://api.openai.com/v1")).rstrip("/")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Executes an asynchronous chat completion request and normalizes the response.
        """
        if not self.api_key and self.provider != "ollama":
            # Return simulation message if no API key configured during offline tests
            return {
                "role": "assistant",
                "content": f"[Simulated Response from {self.provider} ({self.model})]: API key not set.",
                "tool_calls": []
            }

        headers = {
            "Content-Type": "application/json"
        }

        if self.provider == "anthropic":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
            # Anthropic messages endpoint formatting
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
            # OpenAI / Gemini / Ollama OpenAI-compatible format
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if self.provider == "anthropic":
                    content_blocks = data.get("content", [])
                    text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                    return {
                        "role": "assistant",
                        "content": text,
                        "tool_calls": []
                    }
                else:
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {})
                    return {
                        "role": message.get("role", "assistant"),
                        "content": message.get("content", ""),
                        "tool_calls": message.get("tool_calls", [])
                    }
            except Exception as e:
                return {
                    "role": "assistant",
                    "content": f"LLM Request failed ({self.provider}): {str(e)}",
                    "tool_calls": []
                }

    @staticmethod
    def get_supported_providers() -> List[Dict[str, Any]]:
        return [
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
                "default_model": "gpt-4o"
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "default_model": "gemini-2.0-flash"
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
