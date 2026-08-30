import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Add backend/app to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from engine.ast_parser import ASTCodeChunker
from engine.docker_sandbox import DockerSandboxManager
from engine.llm_adapter import UnifiedLLMClient
from engine.orchestrator import AgentOrchestrator
from main import app

def test_ast_parser_python():
    chunker = ASTCodeChunker()
    python_sample = """
def calculate_metrics(data: list) -> float:
    \"\"\"Calculates average metric.\"\"\"
    return sum(data) / len(data)

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
    res = sandbox.execute_command("python -c \"print('sandbox ok')\"")
    assert res["success"] is True
    assert "sandbox ok" in res["stdout"]
    print("[-] Sandbox execution test passed.")

def test_llm_adapter_providers():
    providers = UnifiedLLMClient.get_supported_providers()
    provider_ids = [p["id"] for p in providers]
    assert "openai" in provider_ids
    assert "gemini" in provider_ids
    assert "anthropic" in provider_ids
    assert "ollama" in provider_ids
    
    client = UnifiedLLMClient(provider="gemini")
    assert client.model == "gemini-2.0-flash"
    print("[-] LLM Adapter multi-provider definition test passed.")

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
    
    # 8. Models Router
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    assert len(res.json()["providers"]) >= 4
    
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
    
    print("[-] All 9 Modular Router endpoints tested and PASSED successfully.")

if __name__ == "__main__":
    test_ast_parser_python()
    test_ast_parser_javascript()
    test_sandbox_local_execution()
    test_llm_adapter_providers()
    test_orchestrator_tools()
    test_all_9_routers_endpoints()
    print("\n=> ALL 9-ROUTER SUITE TESTS PASSED 100% SUCCESSFULLY!")
