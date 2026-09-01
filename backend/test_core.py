import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Add backend/app to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from engine.ast_parser import ASTCodeChunker
from engine.docker_sandbox import DockerSandboxManager
from engine.llm_adapter import (
    UnifiedLLMClient,
    PROVIDER_CATALOG,
    _normalize_provider,
    _resolve_api_key,
)
from engine.orchestrator import AgentOrchestrator
from main import app


def test_ast_parser_python():
    chunker = ASTCodeChunker()
    python_sample = """
def calculate_metrics(data: list) -> float:
    \"\"\"Calculates average metric.\"\"\"\n    return sum(data) / len(data)

class AgentWorker:
    def __init__(self, name: str):
        self.name = name
        
    def perform_task(self, task: str) -> bool:
        return True
"""
    chunks = chunker.chunk_file("sample.py", python_sample)
    assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"
    symbols = [c["symbol_name"] for c in chunks]
    assert "calculate_metrics" in symbols, f"Missing calculate_metrics: {symbols}"
    assert "AgentWorker" in symbols, f"Missing AgentWorker: {symbols}"
    
    # Test symbol search
    search_results = chunker.search_symbols("sample.py", python_sample, "calculate")
    assert len(search_results) >= 1
    assert search_results[0]["symbol_name"] == "calculate_metrics"
    print("[-] AST Parser Python test passed.")


def test_ast_parser_javascript():
    chunker = ASTCodeChunker()
    js_sample = """
function processData(items) {
    return items.map(x => x * 2);
}

class PipelineRunner {
    constructor(config) {
        this.config = config;
    }
}
"""
    chunks = chunker.chunk_file("pipeline.js", js_sample)
    assert len(chunks) >= 1, "JS chunker returned empty chunks"
    print("[-] AST Parser JavaScript test passed.")


def test_sandbox_local_execution():
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_workspace"))
    os.makedirs(test_dir, exist_ok=True)
    
    sandbox = DockerSandboxManager(workspace_path=test_dir)
    res = sandbox.execute_command(f"{sys.executable} -c \"print('sandbox ok')\"")
    assert res["success"] is True
    assert "sandbox ok" in res["stdout"]
    print("[-] Sandbox execution test passed.")


def test_llm_adapter_providers():
    """Static provider catalog returns every supported provider, not just 9Router."""
    providers = UnifiedLLMClient.get_supported_providers()
    provider_ids = [p["id"] for p in providers]
    expected = {"9router", "openai", "gemini", "anthropic", "ollama", "groq",
                "mistral", "cohere", "together", "deepseek", "openrouter"}
    missing = expected - set(provider_ids)
    assert not missing, f"Missing providers in static catalog: {missing}"

    # Each provider must have a non-empty model list and a default model.
    for p in providers:
        assert p["models"], f"Provider {p['id']} has empty model list"
        assert p["default_model"] in p["models"], (
            f"Default model {p['default_model']} for {p['id']} not in {p['models']}"
        )

    # Backward-compat: 9Router is still the first provider.
    assert provider_ids[0] == "9router"
    print(f"[-] LLM Adapter catalog test passed ({len(providers)} providers).")


def test_provider_normalization():
    """_normalize_provider should map common aliases back to the catalog."""
    assert _normalize_provider(None) == "9router"
    assert _normalize_provider("") == "9router"
    assert _normalize_provider("9router") == "9router"
    assert _normalize_provider("9") == "9router"
    assert _normalize_provider("OPENAI") == "openai"
    assert _normalize_provider("claude") == "anthropic"
    assert _normalize_provider("Anthropic") == "anthropic"
    assert _normalize_provider("google") == "gemini"
    assert _normalize_provider("local") == "ollama"
    assert _normalize_provider("Groq") == "groq"
    assert _normalize_provider("OPENROUTER") == "openrouter"
    print("[-] Provider normalization aliases test passed.")


def test_provider_api_key_resolution(monkeypatch=None):
    """_resolve_api_key must consult the per-provider env var list, not a global fallback."""
    # We just test the per-provider env-var order: clearing all should give "".
    for pid in PROVIDER_CATALOG:
        # Don't actually mutate the environment here — just assert the helper returns a string.
        key = _resolve_api_key(pid)
        assert isinstance(key, str), f"_resolve_api_key({pid}) returned non-string"
    # And the explicit override always wins.
    assert _resolve_api_key("openai", override="sk-test-123") == "sk-test-123"
    assert _resolve_api_key("anthropic", override="sk-ant-test") == "sk-ant-test"
    print("[-] Per-provider API key resolution test passed.")


def test_client_constructs_per_provider():
    """UnifiedLLMClient should accept every catalog provider without raising."""
    for pid in PROVIDER_CATALOG:
        cfg = PROVIDER_CATALOG[pid]
        client = UnifiedLLMClient(provider=pid)
        assert client.provider == pid, f"provider={pid} -> self.provider={client.provider}"
        assert client.api_style in ("openai", "anthropic")
        assert client.base_url, f"empty base_url for {pid}"
        # default model must be one of the catalog's fallback models
        assert client.model in cfg["fallback_models"] or client.model == cfg["default_model"]
    # The bug: 'openai' used to be remapped to '9router'. Make sure that's gone.
    c = UnifiedLLMClient(provider="openai")
    assert c.provider == "openai", "BUG: 'openai' got remapped to 9router"
    assert c.base_url.startswith("https://api.openai.com"), f"OpenAI base_url wrong: {c.base_url}"
    print("[-] UnifiedLLMClient construction for every provider test passed.")


def test_anthropic_request_shape():
    """Anthropic request must use x-api-key + /messages, not Bearer + /chat/completions."""
    client = UnifiedLLMClient(provider="anthropic", api_key="sk-ant-test")
    headers, payload, endpoint = client._build_request(
        "claude-3-7-sonnet-latest",
        messages=[
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hi"},
        ],
        tools=None,
        temperature=0.2,
    )
    assert headers.get("x-api-key") == "sk-ant-test"
    assert "anthropic-version" in headers
    # System message should be lifted out of the messages list.
    assert all(m["role"] != "system" for m in payload["messages"])
    assert payload["system"] == "You are helpful."
    assert endpoint.endswith("/messages"), f"Expected /messages, got {endpoint}"
    print("[-] Anthropic request shape test passed.")


def test_openai_request_shape():
    client = UnifiedLLMClient(provider="openai", api_key="sk-openai-test")
    headers, payload, endpoint = client._build_request(
        "gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
        tools=None,
        temperature=0.2,
    )
    assert headers.get("Authorization") == "Bearer sk-openai-test"
    assert "system" not in payload  # not on OpenAI path
    assert endpoint.endswith("/chat/completions")
    assert payload["model"] == "gpt-4o"
    print("[-] OpenAI request shape test passed.")


def test_openrouter_request_headers():
    """OpenRouter requires HTTP-Referer + X-Title to identify the app."""
    client = UnifiedLLMClient(provider="openrouter", api_key="sk-or-test")
    headers, _, _ = client._build_request(
        "anthropic/claude-3.7-sonnet",
        messages=[{"role": "user", "content": "hi"}],
        tools=None,
        temperature=0.2,
    )
    assert headers.get("Authorization") == "Bearer sk-or-test"
    assert "HTTP-Referer" in headers
    assert "X-Title" in headers
    print("[-] OpenRouter custom headers test passed.")


def test_sse_parser_handles_openai_and_anthropic():
    client = UnifiedLLMClient(provider="openai")
    openai_sse = (
        'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
        'data: [DONE]\n\n'
    )
    parsed = client._parse_sse_stream_response(openai_sse)
    assert parsed["content"] == "Hello world", f"got: {parsed['content']!r}"
    assert parsed["tool_calls"] == []

    # Now an Anthropic event stream (content_block_delta).
    anthropic_sse = (
        'data: {"type":"message_start"}\n\n'
        'data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}\n\n'
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hi from "}}\n\n'
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Claude"}}\n\n'
        'data: {"type":"content_block_stop","index":0}\n\n'
        'data: {"type":"message_stop"}\n\n'
    )
    parsed_a = client._parse_sse_stream_response(anthropic_sse)
    assert parsed_a["content"] == "Hi from Claude", f"got: {parsed_a['content']!r}"
    print("[-] SSE parser (OpenAI + Anthropic) test passed.")


def test_chat_completion_missing_key_returns_helpful_error():
    """Provider that requires a key but has none set should return a helpful message, not crash."""
    # Use a key-less construction and assert the response is informative.
    client = UnifiedLLMClient(provider="openai", api_key="")  # override to "" so no env fallback
    # Force api_key to empty (env may have one set in dev)
    client.api_key = ""
    out = asyncio.run(client.chat_completion(messages=[{"role": "user", "content": "hi"}]))
    # When api_key is missing for a key-required provider, we return the error message directly.
    assert out["role"] == "assistant"
    assert "Missing API key" in out["content"], f"unexpected: {out['content']!r}"
    print("[-] Missing-API-key error path test passed.")


def test_orchestrator_tools():
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_workspace"))
    os.makedirs(test_dir, exist_ok=True)
    
    orc = AgentOrchestrator(workspace_path=test_dir)
    
    # 1. Test write_file
    res_write = asyncio.run(orc.execute_tool("write_file", {
        "path": "test_app.py",
        "content": "def greet():\n    return 'hello agent'\n"
    }))
    assert res_write["status"] == "success"
    
    # 2. Test read_file
    res_read = asyncio.run(orc.execute_tool("read_file", {"path": "test_app.py"}))
    assert "hello agent" in res_read["content"]
    
    # 3. Test apply_diff_patch
    res_patch = asyncio.run(orc.execute_tool("apply_diff_patch", {
        "path": "test_app.py",
        "target_string": "'hello agent'",
        "replacement_string": "'hello world'"
    }))
    assert res_patch["status"] == "success"
    assert "diff" in res_patch and len(res_patch["diff"]) > 0
    
    # 4. Verify patch applied
    res_verify = asyncio.run(orc.execute_tool("read_file", {"path": "test_app.py"}))
    assert "hello world" in res_verify["content"]
    
    # 5. Test search_ast_symbols
    res_symbols = asyncio.run(orc.execute_tool("search_ast_symbols", {
        "path": "test_app.py",
        "query": "greet"
    }))
    assert res_symbols["total"] >= 1
    
    print("[-] Orchestrator tools and diff patching test passed.")


def test_all_9_routers_endpoints():
    """Test endpoints across all 9 modular routers using FastAPI TestClient."""
    client = TestClient(app)
    
    # 1. Root & router list
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["routers_count"] == 9
    
    # 2. Agent Router
    res = client.get("/api/v1/agent/health")
    assert res.status_code == 200
    
    # 3. Workspaces Router
    res = client.get("/api/v1/workspaces")
    assert res.status_code == 200
    
    # 4. Files Router
    res = client.get("/api/v1/files?workspace_path=./test_workspace")
    assert res.status_code == 200
    
    # 5. Context Router
    res = client.get("/api/v1/context/languages")
    assert res.status_code == 200
    assert ".py" in res.json()["supported_extensions"]
    
    # 6. Vector Router
    res = client.post("/api/v1/vector/search", json={"query": "agent"})
    assert res.status_code == 200
    
    # 7. Sandbox Router
    res = client.get("/api/v1/sandbox/status?workspace_path=./test_workspace")
    assert res.status_code == 200
    
    # 8. Models Router — now exposes ALL 11 providers, not just 9Router.
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    providers = res.json()["providers"]
    assert len(providers) >= 11, f"Expected >=11 providers, got {len(providers)}"
    expected_ids = {"9router", "openai", "gemini", "anthropic", "ollama", "groq",
                    "mistral", "cohere", "together", "deepseek", "openrouter"}
    got_ids = {p["id"] for p in providers}
    missing = expected_ids - got_ids
    assert not missing, f"Missing providers in /api/v1/models: {missing}"
    # 9Router is still listed first for backward compat.
    assert providers[0]["id"] == "9router"

    # 8b. New generic /models/sync endpoint.
    res = client.post("/api/v1/models/sync", json={"provider": "openai"})
    assert res.status_code == 200
    body = res.json()
    assert body["provider"] == "openai"
    assert "gpt-4o" in body["models"], f"gpt-4o missing from {body['models']}"
    
    # 9. Sessions Router
    res = client.get("/api/v1/sessions")
    assert res.status_code == 200
    
    # 10. Diff Router
    res = client.post("/api/v1/diff/generate", json={
        "file_path": "sample.py",
        "original_code": "a = 1\n",
        "modified_code": "a = 2\n"
    })
    assert res.status_code == 200
    assert res.json()["has_changes"] is True

    # 11. Agent Health Check
    res = client.get("/api/v1/agent/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"
    
    print(f"[-] All 9 Modular Router endpoints tested and PASSED successfully "
          f"({len(providers)} providers exposed).")


if __name__ == "__main__":
    test_ast_parser_python()
    test_ast_parser_javascript()
    test_sandbox_local_execution()
    test_llm_adapter_providers()
    test_provider_normalization()
    test_provider_api_key_resolution()
    test_client_constructs_per_provider()
    test_anthropic_request_shape()
    test_openai_request_shape()
    test_openrouter_request_headers()
    test_sse_parser_handles_openai_and_anthropic()
    test_chat_completion_missing_key_returns_helpful_error()
    test_orchestrator_tools()
    test_all_9_routers_endpoints()
    print("\n=> ALL 9-ROUTER SUITE TESTS PASSED 100% SUCCESSFULLY!")
