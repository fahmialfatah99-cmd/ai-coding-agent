"""
AI Coding Agent - Agentic Orchestrator (ReAct + Tool Calling)
Core loop: Observe (RAG+AST) -> Think (LLM) -> Act (Tool) -> Verify (Sandbox) -> Self-Correct
"""
import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI

from context.rag import RAGContextEngine
from context.ast_parser import ASTParser
from agent.tools import TOOL_DEFINITIONS, TOOL_EXECUTORS
from sandbox.docker_manager import SandboxManager
from agent.memory import AgentMemory

SYSTEM_PROMPT = """Kamu adalah AI Coding Agent expert setara Cursor.
Kamu memiliki akses ke seluruh codebase via tools.

ATURAN KERJA (ReAct):
1. THOUGHT: Selalu reasoning langkah demi langkah sebelum bertindak.
2. ACTION: Gunakan tool untuk multi-file editing. Jangan halusinasi kode tanpa read_file dulu.
3. OBSERVATION: Analisa hasil tool. Jika error dari sandbox, lakukan self-correction.
4. Selesaikan tugas secara iteratif hingga test/lint pass.

TOOLS TERSEDIA:
- read_file, write_file, apply_diff_patch
- search_ast_symbols (Tree-sitter)
- run_sandbox_command (Docker/E2B isolated)

Gaya: Precise, autonomous, minimal chat, maksimal aksi kode.
"""

class AgentState(str, Enum):
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    DONE = "done"
    ERROR = "error"

@dataclass
class AgentStep:
    thought: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    state: AgentState

class AgenticOrchestrator:
    """
    Orchestrator utama yang mengimplementasikan ReAct Loop
    dengan Context Retrieval (RAG + AST) dan Self-Correction via Sandbox
    """
    def __init__(
        self,
        model: str = "gpt-4o",
        max_iterations: int = 15,
        rag_engine: Optional[RAGContextEngine] = None,
        ast_parser: Optional[ASTParser] = None,
        sandbox: Optional[SandboxManager] = None,
        memory: Optional[AgentMemory] = None
    ):
        self.client = AsyncOpenAI()
        self.model = model
        self.max_iterations = max_iterations
        self.rag = rag_engine or RAGContextEngine()
        self.ast = ast_parser or ASTParser()
        self.sandbox = sandbox or SandboxManager()
        self.memory = memory

    async def _retrieve_context(self, project_id: str, user_query: str, session_id: str) -> str:
        """
        Context Engine: Hybrid Retrieval
        1. RAG Vector Search (pgvector) - semantic
        2. AST Symbol Search (Tree-sitter) - structural
        """
        # Parallel retrieval
        rag_task = self.rag.hybrid_search(
            project_id=project_id,
            query=user_query,
            top_k=8
        )
        ast_task = self.ast.search_relevant_symbols(
            query=user_query,
            project_id=project_id
        )
        memory_task = self.memory.get_relevant_history(session_id) if self.memory else asyncio.sleep(0, result="")

        rag_context, ast_context, memory_context = await asyncio.gather(rag_task, ast_task, memory_task)

        # Construct context block dengan token budgeting
        context_block = f"""
<CODEBASE_CONTEXT>
## RAG Retrieved Chunks (Semantic):
{rag_context}

## AST Symbols (Structural):
{ast_context}

## Conversation Memory:
{memory_context}
</CODEBASE_CONTEXT>
"""
        return context_block

    async def run(
        self, 
        user_message: str, 
        project_id: str, 
        session_id: str,
        workspace_path: str = "/workspace"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main Agent Loop - Streaming ReAct
        Yields events untuk frontend (chat + inline-edit + terminal)
        """
        # 1. OBSERVE: Retrieve context
        yield {"type": "status", "state": AgentState.OBSERVING, "message": "🔍 Menganalisa codebase (RAG + AST)..."}
        context_block = await self._retrieve_context(project_id, user_message, session_id)
        
        # 2. Build messages dengan memory
        history = await self.memory.get_history(session_id) if self.memory else []
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": context_block},
            *history,
            {"role": "user", "content": user_message}
        ]

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            yield {"type": "status", "state": AgentState.THINKING, "message": f"🧠 Thinking iteration {iteration}..."}

            # 3. THINK + ACT: LLM call dengan tool-calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.2,
                stream=False
            )
            msg = response.choices[0].message

            # Jika ada reasoning content
            if msg.content:
                yield {"type": "thought", "content": msg.content}
                messages.append({"role": "assistant", "content": msg.content})

            # Jika tidak ada tool call -> selesai
            if not msg.tool_calls:
                yield {"type": "final", "content": msg.content or "Selesai."}
                if self.memory:
                    await self.memory.save_turn(session_id, user_message, msg.content)
                yield {"type": "status", "state": AgentState.DONE, "message": "✅ Task selesai"}
                return

            # 4. ACT: Eksekusi tools secara paralel
            yield {"type": "status", "state": AgentState.ACTING, "message": f"🛠️ Executing {len(msg.tool_calls)} tools..."}
            
            # Append assistant tool_calls ke history
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
            })

            tool_results = []
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                yield {"type": "tool_start", "tool": fn_name, "args": fn_args, "id": tool_call.id}
                
                executor = TOOL_EXECUTORS.get(fn_name)
                if not executor:
                    result = {"error": f"Tool {fn_name} tidak ditemukan"}
                else:
                    try:
                        # Inject workspace_path untuk sandbox tools
                        if fn_name == "run_sandbox_command":
                            fn_args["workspace_path"] = workspace_path
                            fn_args["sandbox"] = self.sandbox
                        if fn_name == "search_ast_symbols":
                            fn_args["ast_parser"] = self.ast
                        if fn_name in ["read_file", "write_file", "apply_diff_patch"]:
                            fn_args["workspace_path"] = workspace_path
                        
                        result_content = await executor(**fn_args)
                        result = {"success": True, "output": result_content}
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                        # Self-correction signal
                        yield {"type": "tool_error", "tool": fn_name, "error": str(e)}

                tool_results.append(result)
                yield {"type": "tool_result", "tool": fn_name, "result": result, "id": tool_call.id}

                # Append tool result ke messages untuk next iteration
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            # 5. VERIFY & SELF-CORRECTION: Jika ada run_sandbox_command yang gagal, LLM akan otomatis retry di iterasi berikutnya
            # Kita juga bisa trigger auto-verify jika ada file changes
            has_file_edit = any(tc.function.name in ["write_file", "apply_diff_patch"] for tc in msg.tool_calls)
            if has_file_edit:
                yield {"type": "status", "state": AgentState.VERIFYING, "message": "🧪 Verifikasi perubahan..."}
                # Opsional: auto-run lint/test jika agent belum melakukannya
                # Biarkan LLM yang memutuskan, tapi kita beri hint via system message injection
                messages.append({
                    "role": "system",
                    "content": "Hint: Kamu baru saja mengubah file. Pertimbangkan untuk menjalankan `run_sandbox_command` dengan `npm run build` atau `pytest` untuk verifikasi sebelum selesai."
                })

        yield {"type": "status", "state": AgentState.ERROR, "message": "⚠️ Max iterations tercapai. Perlu intervensi manual."}


# Contoh penggunaan FastAPI WebSocket
# async for event in orchestrator.run("Buatkan fitur auth JWT", project_id="proj_123", session_id="sess_abc"):
#     await websocket.send_json(event)
