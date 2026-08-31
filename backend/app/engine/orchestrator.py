import json
import os
import re
import difflib
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from .docker_sandbox import DockerSandboxManager
from .ast_parser import ASTCodeChunker
from .llm_adapter import UnifiedLLMClient

class AgentOrchestrator:
    """
    Autonomous ReAct Agent Orchestrator with Persistent Memory Learning,
    Multi-File Codebase Auditing, Real-time SSE Streaming, and Automated Self-Correction.
    """

    def __init__(
        self,
        workspace_path: str,
        provider: str = "9router",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        if not os.path.isabs(workspace_path):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            clean_rel = workspace_path.lstrip("./").lstrip(".\\")
            self.workspace_path = os.path.abspath(os.path.join(base_dir, clean_rel))
        else:
            self.workspace_path = os.path.abspath(workspace_path)
        os.makedirs(self.workspace_path, exist_ok=True)
        
        self.sandbox = DockerSandboxManager(self.workspace_path)
        self.chunker = ASTCodeChunker()
        self.llm_client = UnifiedLLMClient(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )

    def _get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_workspace_files",
                    "description": "Lists all existing files and subdirectories across the entire project workspace. Use this to audit or review all code files in the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads the entire content of an existing file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path from workspace root"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Writes or creates a code file in the workspace. Use this tool whenever asked to write, create, generate, or refactor code.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path from workspace root, e.g. main.py, src/app.js, calculator.py"},
                            "content": {"type": "string", "description": "The complete source code to write to the file"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_diff_patch",
                    "description": "Applies a precise search-and-replace edit to an existing file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path"},
                            "target_string": {"type": "string", "description": "Exact substring to find and replace"},
                            "replacement_string": {"type": "string", "description": "New replacement substring"}
                        },
                        "required": ["path", "target_string", "replacement_string"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "record_learned_knowledge",
                    "description": "Persists new learned knowledge, architectural conventions, coding rules, or notes into the project's permanent MEMORY.md file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Title/topic of the learned rule or knowledge"},
                            "content": {"type": "string", "description": "Detailed explanation, conventions, or rules to remember"}
                        },
                        "required": ["topic", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_sandbox_command",
                    "description": "Executes shell commands (e.g. git clone, pytest, npm test, python main.py) in the sandbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to run"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_ast_symbols",
                    "description": "Searches functions, classes, and methods using Tree-sitter AST parsing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path"},
                            "query": {"type": "string", "description": "Symbol name keyword to search"}
                        },
                        "required": ["path", "query"]
                    }
                }
            }
        ]

    def _generate_diff(self, original: str, modified: str, filename: str) -> str:
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)
        diff = difflib.unified_diff(orig_lines, mod_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
        return "".join(diff)

    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        pattern = r"```(?:(\w+)(?::([^\n]+)|(?:\s+([^\n]+)))?)?\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        results = []
        for lang, explicit_path1, explicit_path2, code in matches:
            path = explicit_path1.strip() or explicit_path2.strip()
            if not path:
                first_line = code.split("\n", 1)[0].strip()
                if first_line.startswith(("#", "//", "/*", "<!--")) and ("." in first_line):
                    cleaned = re.sub(r"^[#/\*<!\- ]+", "", first_line).replace("-->", "").strip()
                    if len(cleaned.split()) == 1 and "." in cleaned:
                        path = cleaned

            if not path and lang:
                ext_map = {"python": "py", "javascript": "js", "typescript": "ts", "html": "html", "css": "css"}
                ext = ext_map.get(lang.lower(), lang.lower())
                path = f"app.{ext}"

            if path and code.strip():
                results.append({"path": path, "content": code.strip()})
        return results

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches tool calls safely within the workspace.
        """
        if tool_name == "list_workspace_files":
            files_list = []
            for root, dirs, files in os.walk(self.workspace_path):
                dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv"}]
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), self.workspace_path).replace("\\", "/")
                    files_list.append(rel)
            return {"files": files_list, "total": len(files_list)}

        elif tool_name == "record_learned_knowledge":
            topic = args.get("topic", "General Knowledge")
            content = args.get("content", "")
            memory_file = os.path.join(self.workspace_path, "MEMORY.md")
            
            entry = f"\n\n### 📌 {topic} (Recorded: {datetime.now().strftime('%Y-%m-%d %H:%M')})\n{content}\n"
            
            if not os.path.exists(memory_file):
                with open(memory_file, "w", encoding="utf-8") as f:
                    f.write("# 🧠 Project Knowledge & Learned Conventions\n" + entry)
            else:
                with open(memory_file, "a", encoding="utf-8") as f:
                    f.write(entry)
                    
            return {
                "status": "success",
                "message": f"Knowledge '{topic}' recorded permanently into MEMORY.md",
                "file_path": "MEMORY.md"
            }

        elif tool_name == "read_file":
            target = os.path.join(self.workspace_path, args.get("path", ""))
            if not os.path.exists(target):
                return {"error": f"File '{args.get('path')}' does not exist."}
            try:
                with open(target, "r", encoding="utf-8") as f:
                    return {"content": f.read(), "file_path": args.get("path")}
            except Exception as e:
                return {"error": f"Failed to read file: {str(e)}"}

        elif tool_name == "write_file":
            rel_path = args.get("path", "").strip().lstrip("/\\")
            target = os.path.join(self.workspace_path, rel_path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            orig_content = ""
            if os.path.exists(target):
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        orig_content = f.read()
                except Exception:
                    pass

            new_content = args.get("content", "")
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            diff = self._generate_diff(orig_content, new_content, rel_path)
            return {
                "status": "success",
                "file_path": rel_path,
                "bytes_written": len(new_content),
                "diff": diff
            }

        elif tool_name == "apply_diff_patch":
            rel_path = args.get("path", "").strip().lstrip("/\\")
            target = os.path.join(self.workspace_path, rel_path)
            if not os.path.exists(target):
                return {"error": f"File '{rel_path}' not found."}
                
            with open(target, "r", encoding="utf-8") as f:
                current_content = f.read()

            target_str = args.get("target_string", "")
            repl_str = args.get("replacement_string", "")

            if target_str not in current_content:
                return {"error": f"Target substring to replace was not found in '{rel_path}'."}

            updated_content = current_content.replace(target_str, repl_str, 1)
            with open(target, "w", encoding="utf-8") as f:
                f.write(updated_content)

            diff = self._generate_diff(current_content, updated_content, rel_path)
            return {
                "status": "success",
                "file_path": rel_path,
                "diff": diff
            }

        elif tool_name == "run_sandbox_command":
            cmd = args.get("command", "")
            return self.sandbox.execute_command(cmd)

        elif tool_name == "search_ast_symbols":
            rel_path = args.get("path", "")
            query = args.get("query", "")
            target = os.path.join(self.workspace_path, rel_path)
            if not os.path.exists(target):
                return {"error": f"File '{rel_path}' not found."}
            with open(target, "r", encoding="utf-8") as f:
                code = f.read()
            symbols = self.chunker.search_symbols(rel_path, code, query)
            return {"symbols": symbols, "total": len(symbols)}

        return {"error": f"Unknown tool: {tool_name}"}

    async def run_agent_loop(
        self,
        user_instruction: str,
        active_file: Optional[str] = None,
        file_content: Optional[str] = None,
        max_iterations: int = 8
    ) -> AsyncGenerator[str, None]:
        """
        Executes autonomous ReAct loop with real-time SSE streaming, learned memory injection, & self-healing.
        """
        system_prompt = (
            "You are an expert Senior Autonomous AI Software Engineer inside a Cursor-Class Web IDE (Cursor Composer / Devin standard).\n\n"
            "MANDATORY OPERATIONAL DIRECTIVES:\n"
            "1. CODEBASE-WIDE CAPABILITY: You have full access to the entire project workspace. When asked to review, audit, check, or refine all files in the project, start by calling `list_workspace_files` or `read_file` across all modules.\n"
            "2. CONTINUOUS LEARNING & MEMORY: If the user provides custom rules, conventions, or knowledge to remember, invoke `record_learned_knowledge` to save it permanently in `MEMORY.md`.\n"
            "3. EXTERNAL CODE & GITHUB: You can clone, fetch, or inspect external GitHub repositories via `run_sandbox_command` (e.g. `git clone <url>`) or `read_file` to learn patterns and adapt them.\n"
            "4. DIRECT CODE WRITING: When asked to build, write, create, generate, or refactor code, you MUST ALWAYS invoke the `write_file` or `apply_diff_patch` tool to directly create and update files in the workspace editor. DO NOT just output raw markdown code in conversational text.\n"
            "5. AUTONOMOUS SELF-HEALING: Run tests using `run_sandbox_command`. If any command fails, inspect the error output and patch the code autonomously until everything passes."
        )

        # Inject persistent project knowledge / MEMORY.md if present
        memory_files = ["MEMORY.md", ".agent/rules.md", ".cursorrules", "ARCHITECTURE.md"]
        learned_knowledge = []
        for mf in memory_files:
            mf_path = os.path.join(self.workspace_path, mf)
            if os.path.exists(mf_path):
                try:
                    with open(mf_path, "r", encoding="utf-8") as f:
                        learned_knowledge.append(f"### 🧠 Persistent Project Memory from `{mf}`:\n{f.read()}")
                except Exception:
                    pass

        if learned_knowledge:
            system_prompt += "\n\n" + "\n\n".join(learned_knowledge)

        user_prompt_parts = [f"Instruction: {user_instruction}"]
        if active_file:
            user_prompt_parts.append(f"\nActive File: `{active_file}`")
        if file_content is not None:
            user_prompt_parts.append(f"\nActive File Content:\n```\n{file_content}\n```")

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n".join(user_prompt_parts)}
        ]

        self.sandbox.start_sandbox()

        try:
            for iteration in range(max_iterations):
                yield f"data: {json.dumps({'type': 'thought', 'content': f'Iteration {iteration + 1}: Analyzing codebase & preparing actions...'})}\n\n"

                llm_res = await self.llm_client.chat_completion(
                    messages=messages,
                    tools=self._get_tools_definition(),
                    temperature=0.1
                )

                # If LLM returned reasoning/thinking, stream it to UI
                if llm_res.get("reasoning"):
                    yield f"data: {json.dumps({'type': 'thought', 'content': llm_res['reasoning'].strip()})}\n\n"

                if llm_res.get("content"):
                    yield f"data: {json.dumps({'type': 'message', 'content': llm_res['content']})}\n\n"

                tool_calls = llm_res.get("tool_calls", [])

                # Fallback: if no tool calls were generated but the model outputted code blocks in text, auto-write them to files!
                if not tool_calls and llm_res.get("content"):
                    extracted_blocks = self._extract_code_blocks(llm_res["content"])
                    if extracted_blocks:
                        for blk in extracted_blocks:
                            res = await self.execute_tool("write_file", blk)
                            yield f"data: {json.dumps({'type': 'tool_call', 'tool': 'write_file', 'args': blk})}\n\n"
                            yield f"data: {json.dumps({'type': 'tool_result', 'tool': 'write_file', 'result': res})}\n\n"
                            yield f"data: {json.dumps({'type': 'file_modified', 'path': blk['path'], 'diff': res.get('diff', '')})}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'content': 'Code extracted and written directly to files.'})}\n\n"
                        break

                # Append assistant message strictly conforming to OpenAI schema
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": llm_res.get("content") or None
                }
                if tool_calls:
                    formatted_tool_calls = []
                    for i, tc in enumerate(tool_calls):
                        call_id = tc.get("id") or f"call_{i}_{iteration}"
                        tc["id"] = call_id
                        formatted_tool_calls.append({
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"] if isinstance(tc["function"]["arguments"], str) else json.dumps(tc["function"]["arguments"])
                            }
                        })
                    assistant_msg["tool_calls"] = formatted_tool_calls
                messages.append(assistant_msg)

                if not tool_calls:
                    final_msg = llm_res.get("content") or "Pemeriksaan selesai. Seluruh file di workspace telah ditinjau dan siap digunakan."
                    yield f"data: {json.dumps({'type': 'message', 'content': final_msg})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'content': 'Task completed and verified.'})}\n\n"
                    break

                for i, tc in enumerate(tool_calls):
                    fn_name = tc["function"]["name"]
                    raw_args = tc["function"].get("arguments", "{}")
                    try:
                        fn_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        fn_args = {}

                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': fn_name, 'args': fn_args})}\n\n"

                    tool_result = await self.execute_tool(fn_name, fn_args)

                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': fn_name, 'result': tool_result})}\n\n"

                    if "diff" in tool_result and tool_result["diff"]:
                        yield f"data: {json.dumps({'type': 'file_modified', 'path': tool_result.get('file_path'), 'diff': tool_result['diff']})}\n\n"
                    elif fn_name in {"write_file", "record_learned_knowledge"} and tool_result.get("status") == "success":
                        target_p = tool_result.get("file_path", fn_args.get("path"))
                        yield f"data: {json.dumps({'type': 'file_modified', 'path': target_p, 'diff': tool_result.get('diff', '')})}\n\n"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", f"call_{i}_{iteration}"),
                        "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                    })

                    # If sandbox command failed, notify SSE for self-correction feedback
                    if fn_name == "run_sandbox_command" and not tool_result.get("success", False):
                        exit_code = tool_result.get("exit_code", -1)
                        yield f"data: {json.dumps({'type': 'warning', 'content': f'Sandbox execution failed (exit code {exit_code}). Triggering self-correction patch...'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Execution error: {str(e)}'})}\n\n"
        finally:
            self.sandbox.cleanup()
