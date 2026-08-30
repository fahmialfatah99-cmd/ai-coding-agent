import json
import os
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
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
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
                    "name": "read_file",
                    "description": "Reads the entire content of a file in the workspace.",
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
                    "description": "Writes or overwrites a complete file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative file path"},
                            "content": {"type": "string", "description": "Full file content to write"}
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
                    "name": "run_sandbox_command",
                    "description": "Executes shell commands (test suites, build, lint, compilers) in the isolated sandbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command to run, e.g. pytest, npm test, python -m unittest"}
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
            rel_path = args.get("path", "")
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
            rel_path = args.get("path", "")
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
        Executes autonomous ReAct loop with real-time SSE streaming & self-healing.
        """
        system_prompt = (
            "You are an expert Senior AI Software Engineer operating inside an autonomous IDE. "
            "You have tools to read/write files, apply patches, parse AST symbols, and run commands in a sandbox. "
            "Always follow this workflow:\n"
            "1. Read relevant code and examine AST symbols.\n"
            "2. Make minimal, precise changes using write_file or apply_diff_patch.\n"
            "3. Run automated tests or linter in the sandbox to verify changes.\n"
            "4. If tests fail, diagnose the error and automatically fix it (Self-Correction)."
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
                yield f"data: {json.dumps({'type': 'thought', 'content': f'Iteration {iteration + 1}: Planning next action...'})}\n\n"

                llm_res = await self.llm_client.chat_completion(
                    messages=messages,
                    tools=self._get_tools_definition(),
                    temperature=0.1
                )

                if llm_res.get("content"):
                    yield f"data: {json.dumps({'type': 'message', 'content': llm_res['content']})}\n\n"

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
                        } for tc in llm_res.get("tool_calls", [])
                    ] if llm_res.get("tool_calls") else None
                })

                tool_calls = llm_res.get("tool_calls", [])
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
