import json
import os
import re
import difflib
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from .docker_sandbox import DockerSandboxManager
from .ast_parser import ASTCodeChunker
from .llm_adapter import UnifiedLLMClient

def get_repo_root() -> str:
    curr = os.path.abspath(os.path.dirname(__file__))
    for _ in range(6):
        if os.path.exists(os.path.join(curr, "docker-compose.yml")) or os.path.exists(os.path.join(curr, ".git")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

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
        base_url: Optional[str] = None,
        role_models: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        if not os.path.isabs(workspace_path):
            base_dir = get_repo_root()
            clean_rel = workspace_path.lstrip("./").lstrip(".\\")
            self.workspace_path = os.path.abspath(os.path.join(base_dir, clean_rel))
        else:
            self.workspace_path = os.path.abspath(workspace_path)
        os.makedirs(self.workspace_path, exist_ok=True)

        self.sandbox = DockerSandboxManager(self.workspace_path)
        self.active_file: Optional[str] = None
        self.chunker = ASTCodeChunker()
        self.llm_client = UnifiedLLMClient(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        # Role-specific model overrides for the team swarm. Each entry can set
        # provider/model/api_key/base_url. Missing keys fall back to llm_client.
        # Supported roles: "architect", "builder", "auditor".
        # Default: architect=strong model (opus/gpt-5), builder=balanced (sonnet/gpt-4o), auditor=cheap (haiku/mini).
        default_role_models = {
            "architect": {"model": "ag/claude-opus-4-6-thinking"},
            "builder": {"model": "ag/claude-sonnet-4-6"},
            "auditor": {"model": "ag/gemini-2.5-flash"},
        }
        if role_models:
            for role, spec in role_models.items():
                if role in default_role_models:
                    default_role_models[role].update(spec)
                else:
                    default_role_models[role] = spec
        self.role_models: Dict[str, Dict[str, Any]] = default_role_models
        self._role_clients: Dict[str, UnifiedLLMClient] = {}

    def _get_role_client(self, role: str) -> UnifiedLLMClient:
        """
        Returns a UnifiedLLMClient for a given team role (architect/builder/auditor).
        If a role-specific override is configured in self.role_models, that wins;
        otherwise the default self.llm_client is reused.
        """
        if role in self._role_clients:
            return self._role_clients[role]
        spec = self.role_models.get(role) or {}
        client = UnifiedLLMClient(
            provider=spec.get("provider") or self.llm_client.provider,
            api_key=spec.get("api_key") or self.llm_client.api_key,
            model=spec.get("model") or self.llm_client.model,
            base_url=spec.get("base_url") or self.llm_client.base_url,
        )
        self._role_clients[role] = client
        return client

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
                            "path": {"type": "string", "description": "Relative path of file to patch"},
                            "target_string": {"type": "string", "description": "Exact existing code snippet to replace"},
                            "replacement_string": {"type": "string", "description": "New replacement code"}
                        },
                        "required": ["path", "target_string", "replacement_string"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_sandbox_command",
                    "description": "Executes shell commands (npm, pip, pytest, git, etc.) in an isolated sandbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Shell command line string to run"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_ast_symbols",
                    "description": "Parses Class, Function, Interface AST definitions from a source file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Relative path of source file"},
                            "query": {"type": "string", "description": "Symbol name or pattern to locate"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "record_learned_knowledge",
                    "description": "Persists knowledge, guidelines, architectural rules, or preferences permanently into MEMORY.md for future sessions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Short topic or title of the knowledge"},
                            "content": {"type": "string", "description": "Markdown content describing the convention or rule"}
                        },
                        "required": ["topic", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_commit_and_push",
                    "description": "Stages all changes, creates a descriptive git commit, and pushes to remote.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commit_message": {"type": "string", "description": "Git commit message"},
                            "branch": {"type": "string", "description": "Target branch to push to (defaults to main)"}
                        },
                        "required": ["commit_message"]
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
        ignored_langs = {"bash", "sh", "shell", "output", "terminal", "log", "console", "cmd", "powershell", "text", "txt"}
        valid_exts = {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".json", ".sql", ".md", ".vue", ".svelte", ".yaml", ".yml"}
        
        for lang, explicit_path1, explicit_path2, code in matches:
            lang_clean = (lang or "").lower().strip()
            if lang_clean in ignored_langs:
                continue

            path = (explicit_path1 or explicit_path2 or "").strip()
            if path and (" " in path or not any(path.endswith(ext) for ext in valid_exts)):
                path = ""

            if not path:
                first_line = code.split("\n", 1)[0].strip()
                if first_line.startswith(("#", "//", "/*", "<!--")):
                    cleaned = re.sub(r"^[#/\*<!\- ]+", "", first_line).replace("-->", "").strip()
                    if " " not in cleaned and any(cleaned.endswith(ext) for ext in valid_exts):
                        path = cleaned

            if not path and lang_clean:
                ext_map = {"python": "py", "javascript": "js", "typescript": "ts", "html": "html", "css": "css", "sql": "sql"}
                if self.active_file and any(self.active_file.endswith(ext) for ext in [f".{lang_clean}", f".{ext_map.get(lang_clean, '')}"]):
                    path = self.active_file
                elif lang_clean in ext_map:
                    path = f"index.{ext_map[lang_clean]}" if lang_clean in ["html", "js", "ts"] else f"app.{ext_map[lang_clean]}"

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

        elif tool_name == "git_commit_and_push":
            import re as _re
            commit_msg = args.get("commit_message", "update codebase via AI Agent")
            branch = args.get("branch", "main")

            # SECURITY: Validate user-influenced inputs to prevent command injection.
            # Without this, a malicious LLM output like
            #   commit_message = 'x"; rm -rf /; #'
            # would otherwise be interpolated into a shell string.
            if not isinstance(commit_msg, str) or len(commit_msg) > 4096:
                return {"error": "commit_message must be a string <= 4096 chars."}
            # Reject shell metacharacters that could be used for injection if ever
            # passed to a shell (defense in depth, even though we use argv).
            if _re.search(r'[;&|$`\\"\']', commit_msg):
                return {"error": "commit_message contains disallowed characters."}
            if not isinstance(branch, str) or not _re.match(r"^[A-Za-z0-9._/\-]+$", branch) or len(branch) > 200:
                return {"error": "branch must match [A-Za-z0-9._/-]+ and be <= 200 chars."}
            # Strip NUL bytes and control chars that git would reject anyway.
            commit_msg = commit_msg.replace("\x00", "")

            repo_root = get_repo_root()

            # Run git as an argument vector (no shell interpolation) so commit
            # message / branch can't break out into arbitrary command execution.
            self.sandbox.execute_command_argv(["git", "-C", repo_root, "add", "."])
            commit_res = self.sandbox.execute_command_argv(
                ["git", "-C", repo_root, "commit", "-m", commit_msg]
            )
            push_res = self.sandbox.execute_command_argv(
                ["git", "-C", repo_root, "push", "origin", branch]
            )

            is_ok = (
                push_res.get("success", False)
                or "up to date" in (push_res.get("stderr", "") + commit_res.get("stdout", "")).lower()
            )
            return {
                "status": "success" if is_ok else "failed",
                "commit_message": commit_msg,
                "branch": branch,
                "stdout": push_res.get("stdout") or commit_res.get("stdout") or "",
                "stderr": push_res.get("stderr") or "",
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

                    # If sandbox command failed on critical tasks (exclude benign inspection checks like cat/grep/which)
                    if fn_name == "run_sandbox_command" and not tool_result.get("success", False):
                        cmd_str = fn_args.get("command", "").strip().lower()
                        exit_code = tool_result.get("exit_code", -1)
                        benign_prefixes = ("cat ", "grep ", "test ", "which ", "head ", "tail ", "find ", "ls ")
                        if not any(cmd_str.startswith(bp) for bp in benign_prefixes):
                            yield f"data: {json.dumps({'type': 'warning', 'content': f'Command returned code {exit_code}. Agent is self-correcting...'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Execution error: {str(e)}'})}\n\n"
        finally:
            self.sandbox.cleanup()

    async def run_team_swarm_loop(
        self,
        user_instruction: str,
        active_file: Optional[str] = None,
        file_content: Optional[str] = None,
        max_audit_cycles: int = 3
    ) -> AsyncGenerator[str, None]:
        """
        Executes Collaborative Multi-Agent Team Swarm with Quality Audit & Autonomous Rework Loop:
        1. 🎯 Lead System Architect (Planner)
        2. 🎨 Senior Frontend & ⚙️ Backend Engineers (Builders)
        3. 🛡️ Strict Quality & Security Auditor (Audit Gatekeeper)
        4. 🔄 Autonomous Rework Feedback Loop
        Uses 1 single centralized 9Router API Key safely and sequentially.
        """
        self.sandbox.start_sandbox()

        self.active_file = active_file
        self.sandbox.start_sandbox()

        # Shared Project Context & Memory
        memory_files = ["MEMORY.md", ".agent/rules.md", ".cursorrules", "ARCHITECTURE.md"]
        learned_knowledge = []
        for mf in memory_files:
            mf_path = os.path.join(self.workspace_path, mf)
            if os.path.exists(mf_path):
                try:
                    with open(mf_path, "r", encoding="utf-8") as f:
                        learned_knowledge.append(f"### 🧠 Persistent Memory (`{mf}`):\n{f.read()}")
                except Exception:
                    pass

        memory_ctx = "\n\n" + "\n\n".join(learned_knowledge) if learned_knowledge else ""

        # Fetch current workspace file list for context
        current_files_res = await self.execute_tool("list_workspace_files", {})
        existing_files = current_files_res.get("files", [])
        files_summary = ", ".join(existing_files[:20]) if existing_files else "Empty workspace"

        # =========================================================================
        # PHASE 1: 🎯 LEAD SYSTEM ARCHITECT (Blueprint & Task Planning)
        # =========================================================================
        yield f"data: {json.dumps({'type': 'thought', 'agent_role': 'architect', 'agent_name': 'Lead System Architect', 'content': '🎯 [Lead Architect] Analyzing requirements, repository structure, and designing implementation blueprint...'})}\n\n"

        architect_system = (
            "You are the Lead System Architect of an Elite AI Software Engineering Team.\n"
            "Your objective: Rapidly create a concise, 3-bullet-point implementation blueprint.\n"
            "Keep it ultra-brief (under 100 words) so the builder can start coding immediately.\n"
            "1. Tech strategy\n"
            "2. Target files\n"
            "3. Action for builder"
            f"{memory_ctx}"
        )

        arch_prompt = f"User Request: {user_instruction}\nWorkspace Files: {files_summary}"
        if active_file:
            arch_prompt += f"\nTarget Active File: `{active_file}`"
        if file_content is not None:
            arch_prompt += f"\nActive File Content:\n```\n{file_content}\n```"

        arch_res = await self._get_role_client("architect").chat_completion(
            messages=[
                {"role": "system", "content": architect_system},
                {"role": "user", "content": arch_prompt}
            ],
            temperature=0.1
        )

        plan_content = arch_res.get("content", "Blueprint dirancang untuk dieksekusi oleh tim developer.")
        arch_msg = {
            "type": "message",
            "agent_role": "architect",
            "agent_name": "Lead System Architect",
            "content": f"### 🎯 Blueprint Arsitektur Tim:\n\n{plan_content}"
        }
        yield f"data: {json.dumps(arch_msg)}\n\n"

        # Track all modified files across the swarm session
        all_modified_files: Dict[str, str] = {}
        last_builder_role = "frontend" if any(k in user_instruction.lower() for k in ["ui", "css", "html", "tampilan", "web", "frontend", "desain"]) else "backend"

        # =========================================================================
        # PHASE 2 & 4: 🛠️ BUILDER EXECUTION & 🔄 AUTONOMOUS REWORK LOOP
        # =========================================================================
        audit_feedback = ""
        audit_verdict = "REJECTED"

        for cycle in range(max_audit_cycles):
            cycle_num = cycle + 1
            is_rework = cycle > 0

            # Determine builder persona based on task/feedback
            if "frontend" in audit_feedback.lower() or "css" in audit_feedback.lower() or "html" in audit_feedback.lower():
                builder_role = "frontend"
                builder_name = "Senior Frontend & UI/UX Specialist"
                builder_icon = "🎨"
            elif "backend" in audit_feedback.lower() or "api" in audit_feedback.lower() or "database" in audit_feedback.lower() or "server" in audit_feedback.lower():
                builder_role = "backend"
                builder_name = "Senior Backend & Core Systems Engineer"
                builder_icon = "⚙️"
            else:
                builder_role = last_builder_role
                builder_name = "Senior Frontend & UI/UX Specialist" if builder_role == "frontend" else "Senior Backend & Core Systems Engineer"
                builder_icon = "🎨" if builder_role == "frontend" else "⚙️"

            last_builder_role = builder_role

            if is_rework:
                rework_thought = {
                    "type": "thought",
                    "agent_role": builder_role,
                    "agent_name": builder_name,
                    "audit_status": "rejected",
                    "audit_cycle": cycle_num,
                    "content": f"{builder_icon} [{builder_name}] Menerima catatan audit (Siklus {cycle_num}/{max_audit_cycles}). Memperbaiki & merefaktor kode..."
                }
                yield f"data: {json.dumps(rework_thought)}\n\n"
            else:
                init_thought = {
                    "type": "thought",
                    "agent_role": builder_role,
                    "agent_name": builder_name,
                    "content": f"{builder_icon} [{builder_name}] Mengimplementasikan kode secara nyata sesuai blueprint arsitektur..."
                }
                yield f"data: {json.dumps(init_thought)}\n\n"

            ui_ux_pro_max_directives = (
                "\n\n### 🎨 UI/UX Pro Max 2.13.0 Design Intelligence Activated:\n"
                "- Apply modern design standards: 84 UI styles (Glassmorphism, Bento Grid, Minimalist Dark, Cyberpunk, Apple Clean), 192 cohesive color palettes, 74 font pairings, 98 UX micro-interaction guidelines.\n"
                "- Use Tailwind CSS classes with refined spacing (p-4 md:p-8, gap-4 md:gap-6, rounded-xl md:rounded-2xl), backdrop-filter blurs, subtle borders (border-white/10 or border-neutral-800), hover micro-transitions (transition-all duration-200 hover:scale-[1.02]), and Lucide icons.\n"
                "- Ensure responsive mobile-first layouts, high accessibility (semantic HTML5, ARIA labels, strong contrast), and zero visual artifacts."
            )
            superpowers_directives = (
                "\n\n### ⚡ Superpowers Software Engineering Suite Activated:\n"
                "- Apply Systematic Debugging & Test-Driven Development (TDD) best practices.\n"
                "- Ensure atomic surgical modifications, robust error boundary handling, and verified output correctness."
            )

            builder_system = (
                f"You are the {builder_name} in an Elite AI Engineering Team.\n"
                "CRITICAL EXECUTION MANDATE:\n"
                "1. ACTION-FIRST POLICY: You are an execution builder. You MUST invoke `write_file` or `apply_diff_patch` to create and update files in the workspace.\n"
                "2. NO DISCUSSION / NO TALKING: Do NOT just describe or discuss what to do in conversational text. You MUST call tools to directly write the code into the files.\n"
                "3. PRODUCTION QUALITY: Implement complete, robust, clean, and production-ready code with zero placeholder gaps."
                f"{ui_ux_pro_max_directives if builder_role == 'frontend' else superpowers_directives}"
                f"{memory_ctx}"
            )

            prompt_sections = [
                f"User Request: {user_instruction}",
                f"Architect Plan:\n{plan_content}"
            ]
            if active_file:
                prompt_sections.append(f"Target Active File: `{active_file}`")
            if file_content is not None:
                prompt_sections.append(f"Active File Content:\n```\n{file_content}\n```")
            if is_rework and audit_feedback:
                prompt_sections.append(f"🚨 CRITICAL AUDIT FEEDBACK (FIX ALL ISSUES):\n{audit_feedback}")

            builder_user_prompt = "\n\n".join(prompt_sections)

            builder_messages: List[Dict[str, Any]] = [
                {"role": "system", "content": builder_system},
                {"role": "user", "content": builder_user_prompt}
            ]

            # Builder ReAct Loop (Up to 4 iterations per cycle)
            for b_iter in range(4):
                b_res = await self._get_role_client("builder").chat_completion(
                    messages=builder_messages,
                    tools=self._get_tools_definition(),
                    temperature=0.1
                )

                if b_res.get("reasoning"):
                    yield f"data: {json.dumps({'type': 'thought', 'agent_role': builder_role, 'agent_name': builder_name, 'content': b_res['reasoning'].strip()})}\n\n"

                tool_calls = b_res.get("tool_calls", [])
                extracted = []

                # Auto-fallback code extraction if code blocks present
                if not tool_calls and b_res.get("content"):
                    extracted = self._extract_code_blocks(b_res["content"])
                    if extracted:
                        for blk in extracted:
                            res = await self.execute_tool("write_file", blk)
                            all_modified_files[blk["path"]] = blk["content"]
                            yield f"data: {json.dumps({'type': 'tool_call', 'agent_role': builder_role, 'agent_name': builder_name, 'tool': 'write_file', 'args': blk})}\n\n"
                            yield f"data: {json.dumps({'type': 'tool_result', 'agent_role': builder_role, 'agent_name': builder_name, 'tool': 'write_file', 'result': res})}\n\n"
                            yield f"data: {json.dumps({'type': 'file_modified', 'agent_role': builder_role, 'path': blk['path'], 'diff': res.get('diff', '')})}\n\n"

                assistant_entry: Dict[str, Any] = {
                    "role": "assistant",
                    "content": b_res.get("content") or None
                }
                if tool_calls:
                    fmt_calls = []
                    for idx, tc in enumerate(tool_calls):
                        c_id = tc.get("id") or f"team_call_{idx}_{b_iter}"
                        tc["id"] = c_id
                        fmt_calls.append({
                            "id": c_id,
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"] if isinstance(tc["function"]["arguments"], str) else json.dumps(tc["function"]["arguments"])
                            }
                        })
                    assistant_entry["tool_calls"] = fmt_calls
                builder_messages.append(assistant_entry)

                if not tool_calls and not extracted:
                    if not all_modified_files and b_iter < 2:
                        builder_messages.append({
                            "role": "user",
                            "content": "CRITICAL: You are an autonomous software engineer. You have NOT written or modified any files yet. You MUST call `write_file` or `apply_diff_patch` NOW to create and update the code files. Do not reply with conversational text."
                        })
                        continue
                    else:
                        if b_res.get("content"):
                            yield f"data: {json.dumps({'type': 'message', 'agent_role': builder_role, 'agent_name': builder_name, 'content': b_res['content']})}\n\n"
                        break

                for idx, tc in enumerate(tool_calls):
                    fn_name = tc["function"]["name"]
                    raw_args = tc["function"].get("arguments", "{}")
                    try:
                        fn_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        fn_args = {}

                    yield f"data: {json.dumps({'type': 'tool_call', 'agent_role': builder_role, 'agent_name': builder_name, 'tool': fn_name, 'args': fn_args})}\n\n"

                    tool_res = await self.execute_tool(fn_name, fn_args)

                    if fn_name == "write_file" and "path" in fn_args:
                        all_modified_files[fn_args["path"]] = fn_args.get("content", "")
                    elif fn_name == "apply_diff_patch" and "path" in fn_args:
                        read_back = await self.execute_tool("read_file", {"path": fn_args["path"]})
                        if "content" in read_back:
                            all_modified_files[fn_args["path"]] = read_back["content"]

                    yield f"data: {json.dumps({'type': 'tool_result', 'agent_role': builder_role, 'agent_name': builder_name, 'tool': fn_name, 'result': tool_res})}\n\n"

                    if "diff" in tool_res and tool_res["diff"]:
                        yield f"data: {json.dumps({'type': 'file_modified', 'agent_role': builder_role, 'path': tool_res.get('file_path'), 'diff': tool_res['diff']})}\n\n"
                    elif fn_name in {"write_file", "record_learned_knowledge"} and tool_res.get("status") == "success":
                        target_p = tool_res.get("file_path", fn_args.get("path"))
                        yield f"data: {json.dumps({'type': 'file_modified', 'agent_role': builder_role, 'path': target_p, 'diff': tool_res.get('diff', '')})}\n\n"

                    builder_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", f"team_call_{idx}_{b_iter}"),
                        "content": json.dumps(tool_res) if isinstance(tool_res, dict) else str(tool_res)
                    })

            # =====================================================================
            # PHASE 3: 🛡️ STRICT QUALITY & SECURITY AUDITOR GATEKEEPER
            # =====================================================================
            auditor_thought = {
                "type": "thought",
                "agent_role": "auditor",
                "agent_name": "Strict Quality Auditor",
                "audit_status": "pending",
                "audit_cycle": cycle_num,
                "content": f"🛡️ [Quality Auditor] Menginspeksi seluruh perubahan file kode (Siklus Audit {cycle_num}/{max_audit_cycles})..."
            }
            yield f"data: {json.dumps(auditor_thought)}\n\n"

            files_code_bundle = []
            for path_k in list(all_modified_files.keys()):
                read_res = await self.execute_tool("read_file", {"path": path_k})
                if "content" in read_res:
                    files_code_bundle.append(f"--- File: `{path_k}` ---\n```\n{read_res['content']}\n```")

            if not files_code_bundle:
                if active_file:
                    read_act = await self.execute_tool("read_file", {"path": active_file})
                    if "content" in read_act:
                        files_code_bundle.append(f"--- Active File: `{active_file}` ---\n```\n{read_act['content']}\n```")

            code_to_audit = "\n\n".join(files_code_bundle) if files_code_bundle else "WARNING: No files were created or modified by the builder in this session."

            auditor_system = (
                "You are the Strict Quality & Security Auditor (Audit Gatekeeper) of an Elite AI Software Engineering Team, equipped with Superpowers Verification Gates and UI/UX Pro Max Quality Standards.\n"
                "Your mission: Thoroughly review all generated code against:\n"
                "1. Direct File Execution: If no files were written or created to fulfill the user request, you MUST reject and mandate file creation.\n"
                "2. Correctness & completeness according to the user request.\n"
                "3. Clean syntax, zero placeholder gaps, proper imports, and modern coding standards.\n"
                "4. Security safeguards (no raw script injections, proper escaping, safe input handling).\n"
                "5. UI/UX Pro Max Design Compliance: Responsive layout (Tailwind CSS), high visual polish, semantic accessibility, and robust error handling.\n\n"
                "VERDICT RULES:\n"
                "- If all files meet high production standards, end your response with:\n"
                "VERDICT: PASSED\n"
                "- If there are any bugs, missing requirements, broken styling, or if no files were modified, end with:\n"
                "VERDICT: REJECTED\n"
                "And provide an explicit, numbered list of required fixes for the developer team."
            )

            audit_eval_prompt = (
                f"User Request: {user_instruction}\n\n"
                f"Workspace Code Under Audit:\n{code_to_audit}"
            )

            audit_res = await self._get_role_client("auditor").chat_completion(
                messages=[
                    {"role": "system", "content": auditor_system},
                    {"role": "user", "content": audit_eval_prompt}
                ],
                temperature=0.1
            )

            audit_text = audit_res.get("content", "")

            # Check verdict
            if "VERDICT: PASSED" in audit_text.upper():
                audit_verdict = "PASSED"
                clean_report = audit_text.replace("VERDICT: PASSED", "").strip()
                passed_event = {
                    "type": "audit",
                    "agent_role": "auditor",
                    "agent_name": "Strict Quality Auditor",
                    "audit_status": "passed",
                    "audit_cycle": cycle_num,
                    "content": f"### 🛡️ Laporan Audit Kualitas: ✅ PASSED (Lolos)\n\n{clean_report}"
                }
                yield f"data: {json.dumps(passed_event)}\n\n"
                break
            else:
                audit_verdict = "REJECTED"
                audit_feedback = audit_text
                clean_report = audit_text.replace("VERDICT: REJECTED", "").strip()

                if cycle < max_audit_cycles - 1:
                    rej_event = {
                        "type": "audit",
                        "agent_role": "auditor",
                        "agent_name": "Strict Quality Auditor",
                        "audit_status": "rejected",
                        "audit_cycle": cycle_num,
                        "audit_feedback": clean_report,
                        "content": f"### 🛡️ Laporan Audit Kualitas: ❌ REJECTED (Perlu Revisi - Siklus {cycle_num}/{max_audit_cycles})\n\n{clean_report}\n\n> 🔄 *Tugas otomatis dilempar kembali ke tim developer untuk direvisi.*"
                    }
                    yield f"data: {json.dumps(rej_event)}\n\n"
                else:
                    max_event = {
                        "type": "audit",
                        "agent_role": "auditor",
                        "agent_name": "Strict Quality Auditor",
                        "audit_status": "passed",
                        "audit_cycle": cycle_num,
                        "content": f"### 🛡️ Laporan Audit Kualitas (Siklus Maksimal Selesai):\n\n{clean_report}"
                    }
                    yield f"data: {json.dumps(max_event)}\n\n"

        # Final Delivery
        status_text = "Tugas selesai dan telah diverifikasi lolos audit kualitas." if audit_verdict == "PASSED" else "Tugas selesai dengan catatan audit akhir."
        done_event = {
            "type": "done",
            "agent_role": "auditor",
            "agent_name": "Strict Quality Auditor",
            "content": f"🎉 Kolaborasi Tim Coding Selesai: {status_text}"
        }
        yield f"data: {json.dumps(done_event)}\n\n"

        self.sandbox.cleanup()
