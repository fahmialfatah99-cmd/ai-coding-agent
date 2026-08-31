"""
Agent Tool Definitions and Execution Handlers
"""
import os
import aiofiles
from typing import Dict, Any, Callable

# OpenAI Tool Schemas
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Membaca seluruh isi file dari workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path dari workspace root"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Menulis atau membuat file baru dalam workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "content": {"type": "string", "description": "Seluruh isi source code baru"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_diff_patch",
            "description": "Menerapkan search-and-replace edit presisi ke file yang ada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "target_string": {"type": "string", "description": "Substring persis yang ingin diganti"},
                    "replacement_string": {"type": "string", "description": "Substring baru pengganti"}
                },
                "required": ["path", "target_string", "replacement_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_ast_symbols",
            "description": "Mencari definisi fungsi, class, method menggunakan Tree-sitter AST parser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path file atau folder"},
                    "query": {"type": "string", "description": "Nama keyword simbol/fungsi/class"}
                },
                "required": ["path", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sandbox_command",
            "description": "Menjalankan perintah shell di isolated docker sandbox (test, lint, compiler, bash).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Perintah shell, contoh: pytest, npm run build"}
                },
                "required": ["command"]
            }
        }
    }
]

# Tool Handlers
async def read_file_handler(path: str, workspace_path: str = "/workspace") -> str:
    full_path = os.path.join(workspace_path, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File {path} tidak ditemukan.")
    async with aiofiles.open(full_path, mode="r", encoding="utf-8") as f:
        return await f.read()

async def write_file_handler(path: str, content: str, workspace_path: str = "/workspace") -> str:
    full_path = os.path.join(workspace_path, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    async with aiofiles.open(full_path, mode="w", encoding="utf-8") as f:
        await f.write(content)
    return f"File {path} berhasil ditulis ({len(content)} bytes)."

async def apply_diff_patch_handler(path: str, target_string: str, replacement_string: str, workspace_path: str = "/workspace") -> str:
    full_path = os.path.join(workspace_path, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File {path} tidak ditemukan.")
    async with aiofiles.open(full_path, mode="r", encoding="utf-8") as f:
        content = await f.read()
    
    if target_string not in content:
        raise ValueError(f"target_string tidak ditemukan di dalam {path}. Pastikan exact match.")
    
    new_content = content.replace(target_string, replacement_string, 1)
    async with aiofiles.open(full_path, mode="w", encoding="utf-8") as f:
        await f.write(new_content)
    return f"Diff patch berhasil diaplikasikan pada {path}."

async def search_ast_symbols_handler(path: str, query: str, ast_parser: Any = None) -> str:
    if not ast_parser:
        return "AST Parser tidak tersedia."
    return await ast_parser.search_symbols(path, query)

async def run_sandbox_command_handler(command: str, sandbox: Any = None, workspace_path: str = "/workspace") -> str:
    if not sandbox:
        return "Sandbox Manager tidak aktif."
    return await sandbox.execute(command, workspace_path)

TOOL_EXECUTORS: Dict[str, Callable] = {
    "read_file": read_file_handler,
    "write_file": write_file_handler,
    "apply_diff_patch": apply_diff_patch_handler,
    "search_ast_symbols": search_ast_symbols_handler,
    "run_sandbox_command": run_sandbox_command_handler
}
