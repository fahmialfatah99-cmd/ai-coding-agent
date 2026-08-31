import json
import os
import re
import difflib
from typing import AsyncGenerator, Dict, Any, List, Optional
from .docker_sandbox import DockerSandboxManager
from .ast_parser import ASTCodeChunker
from .llm_adapter import UnifiedLLMClient

class AgentOrchestrator:
    """
    Autonomous ReAct Agent Orchestrator with Multi-Provider LLM,
    Tool Dispatching, Real-time SSE Streaming, and Automated Self-Correction.
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
                    "name": "run_sandbox_command",
                    "description": "Executes shell commands (test suites, build, lint, compilers) in the isolated sandbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to run, e.g. pytest, npm test, python main.py"}
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
        """
        Fallback parser: extracts markdown code blocks with inferred or explicit file paths.
        """
        pattern = r"```(?:(\w+)(?::([^\n]+)|(?:\s+([^\n]+)))?)?\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        results = []
        for lang, explicit_path1, explicit_path2, code in matches:
            path = explicit_path1.strip() or explicit_path2.strip()
            if not path:
                # Check first line of code for filename comment e.g. # calculator.py or // app.js
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
        if tool_name == "read_file":
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
        max_iterations: int = 6
    ) -> AsyncGenerator[str, None]:
        """
        Executes autonomous ReAct loop with real-time SSE streaming, automatic tool dispatching, & self-healing.
        """
        system_prompt = (
            "You are an expert Senior Autonomous AI Software Engineer inside a Cursor-Class Web IDE (like Cursor Composer / Devin).\n\n"
            "MANDATORY OPERATIONAL DIRECTIVES:\n"
            "1. DIRECT CODE WRITING: When asked to build, write, create, generate, or refactor code, you MUST ALWAYS invoke the `write_file` or `apply_diff_patch` tool to directly create and update files in the workspace editor. DO NOT just output raw markdown code in conversational text.\n"
            "2. IMMEDIATE ACTION: Start by inspecting files if needed, then immediately write/patch the code files.\n"
            "3. SANDBOX VERIFICATION: Run commands using `run_sandbox_command` (e.g. tests, lint, compiler) to verify correctness.\n"
            "4. SELF-HEALING: If tests fail in the sandbox, inspect the error output and patch the code autonomously."
        )

        user_prompt_parts = [f"Instruction: {user_instruction}"]
        if active_file:
            user_prompt_parts.append(f"\nActive File: `{active_file}`")
        if file_content is not None:
            user_prompt_parts.append(f"\nActive File Content:\n```\n{file_content}\n```")

        messages = [
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
                        tool_calls = [
                            {
                                "id": f"auto_write_{i}",
                                "type": "function",
                                "function": {
                                    "name": "write_file",
                                    "arguments": json.dumps(blk)
                                }
                            } for i, blk in enumerate(extracted_blocks)
                        ]

                # Append assistant message to context
                messages.append({
                    "role": "assistant",
                    "content": llm_res.get("content") or "",
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        } for tc in tool_calls
                    ] if tool_calls else None
                })

                if not tool_calls:
                    yield f"data: {json.dumps({'type': 'done', 'content': 'Task completed and verified.'})}\n\n"
                    break

                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    try:
                        fn_args = json.loads(tc["function"]["arguments"])
                    except Exception:
                        fn_args = {}

                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': fn_name, 'args': fn_args})}\n\n"

                    tool_result = await self.execute_tool(fn_name, fn_args)

                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': fn_name, 'result': tool_result})}\n\n"

                    if "diff" in tool_result and tool_result["diff"]:
                        yield f"data: {json.dumps({'type': 'file_modified', 'path': tool_result.get('file_path'), 'diff': tool_result['diff']})}\n\n"
                    elif fn_name == "write_file" and tool_result.get("status") == "success":
                        yield f"data: {json.dumps({'type': 'file_modified', 'path': fn_args.get('path'), 'diff': tool_result.get('diff', '')})}\n\n"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result)
                    })

                    # If sandbox command failed, notify SSE for self-correction feedback
                    if fn_name == "run_sandbox_command" and not tool_result.get("success", False):
                        exit_code = tool_result.get("exit_code", -1)
                        yield f"data: {json.dumps({'type': 'warning', 'content': f'Sandbox execution failed (exit code {exit_code}). Triggering self-correction patch...'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Execution error: {str(e)}'})}\n\n"
        finally:
            self.sandbox.cleanup()
