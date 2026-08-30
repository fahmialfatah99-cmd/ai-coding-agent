import os
import sys
import asyncio

# Add backend/app to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "app")))

from engine.ast_parser import ASTCodeChunker
from engine.docker_sandbox import DockerSandboxManager
from engine.llm_adapter import UnifiedLLMClient
from engine.orchestrator import AgentOrchestrator

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

if __name__ == "__main__":
    test_ast_parser_python()
    test_ast_parser_javascript()
    test_sandbox_local_execution()
    test_llm_adapter_providers()
    test_orchestrator_tools()
    print("\n=> ALL COMPREHENSIVE BACKEND TESTS PASSED SUCCESSFULLY!")
