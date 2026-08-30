# AI Coding Agent Core Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate backend modules, integrate Multi-Provider LLM adapter, build ReAct self-healing agent loop, create Dockerfile containerization, unify pgvector schema, and construct a full Next.js 14 Monaco Web IDE.

**Architecture:** A unified FastAPI backend with Tree-sitter AST Chunker, Multi-Provider LLM Adapter (OpenAI, Gemini, Claude, Ollama), Isolated Docker Sandbox runner, and ReAct SSE streaming orchestrator connected to a Next.js 14 App Router frontend featuring Monaco Editor, Inline Diff review, Chat panel, File Tree, and Terminal log viewer.

**Tech Stack:** Python 3.11+, FastAPI, Tree-sitter, Docker SDK, Next.js 14, React 18, TypeScript, Tailwind CSS, Monaco Editor (`@monaco-editor/react`), Lucide React, PostgreSQL 16 + pgvector.

**Spec:** `docs/superpowers/specs/2026-08-31-ai-coding-agent-platform-design.md`

## Global Constraints
- Unified module layout under `backend/app/engine/` and `backend/app/api/`.
- No duplicate legacy files in `context/`, `context_engine/`, `sandbox/`, or `agent/`.
- Multi-provider LLM support via standard function calling schemas and streaming.
- Docker sandbox must include transparent fallback to safe local subprocess execution when Docker daemon is not active.
- Frontend must be a fully working Next.js 14 App Router with Tailwind CSS dark theme.

---

### Task 1: Backend Dependencies & Multi-Provider LLM Adapter

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/engine/llm_adapter.py`
- Test: `backend/test_core.py`

**Interfaces:**
- Produces: `UnifiedLLMClient(provider: str, api_key: str, base_url: Optional[str] = None)`
  - `async def complete(messages: List[Dict], tools: List[Dict], model: str) -> Dict`
  - `async def stream_chat(messages: List[Dict], tools: List[Dict], model: str) -> AsyncGenerator[Dict, None]`

- [ ] **Step 1: Update requirements.txt with multi-provider and core dependencies**
- [ ] **Step 2: Implement UnifiedLLMClient in `backend/app/engine/llm_adapter.py`**
- [ ] **Step 3: Add test cases for LLM adapter tool schema translation in `test_core.py`**

---

### Task 2: Tree-Sitter Multi-Language AST Chunker

**Files:**
- Modify: `backend/app/engine/ast_parser.py`
- Test: `backend/test_core.py`

**Interfaces:**
- Produces: `ASTCodeChunker`
  - `def chunk_file(file_path: str, content: str) -> List[Dict[str, Any]]`
  - `def search_symbols(file_path: str, content: str, query: str) -> List[Dict[str, Any]]`

- [ ] **Step 1: Refactor `ast_parser.py` with multi-language Tree-sitter support and symbol search**
- [ ] **Step 2: Test AST chunking across Python, JavaScript, and TypeScript in `test_core.py`**

---

### Task 3: Isolated Docker Sandbox & Local Fallback Runner

**Files:**
- Modify: `backend/app/engine/docker_sandbox.py`
- Test: `backend/test_core.py`

**Interfaces:**
- Produces: `DockerSandboxManager(workspace_path: str, container_image: str = "python:3.11-slim")`
  - `def execute_command(cmd: str, timeout_sec: int = 30) -> Dict[str, Any]`
  - `def cleanup()`

- [ ] **Step 1: Enhance `docker_sandbox.py` with automatic docker-to-local fallback and resource limits**
- [ ] **Step 2: Test execution of bash commands and exit code captures in `test_core.py`**

---

### Task 4: ReAct Orchestrator & Self-Correction Engine

**Files:**
- Modify: `backend/app/engine/orchestrator.py`
- Test: `backend/test_core.py`

**Interfaces:**
- Produces: `AgentOrchestrator(workspace_path: str, provider: str = "openai", api_key: str = "", model: str = "gpt-4o", base_url: Optional[str] = None)`
  - `async def execute_tool(tool_name: str, args: Dict[str, Any]) -> str`
  - `async def run_agent_loop(user_instruction: str, active_file: str, file_content: str, max_iterations: int = 5) -> AsyncGenerator[str, None]`

- [ ] **Step 1: Implement full tool set (`read_file`, `write_file`, `apply_diff_patch`, `run_sandbox_command`, `search_ast_symbols`)**
- [ ] **Step 2: Implement ReAct streaming loop with self-healing feedback when sandbox fails**
- [ ] **Step 3: Test ReAct tool dispatching and patch application in `test_core.py`**

---

### Task 5: FastAPI REST Routes & Main Application

**Files:**
- Create: `backend/app/api/routes.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces:
  - `GET /`: Health check
  - `GET /api/v1/models`: List available providers & default models
  - `POST /api/v1/agent/run`: SSE stream endpoint
  - `GET /api/v1/files`: List workspace file tree
  - `POST /api/v1/files/read`: Read workspace file
  - `POST /api/v1/files/write`: Write workspace file

- [ ] **Step 1: Create `backend/app/api/routes.py` with file management & model endpoints**
- [ ] **Step 2: Update `backend/app/main.py` to mount routes and CORS**

---

### Task 6: Backend Containerization & Directory Cleanup

**Files:**
- Create: `backend/Dockerfile.agent`
- Modify: `backend/schema.sql`
- Modify: `docker-compose.yml`
- Remove: `backend/app/agent/`, `backend/app/context/`, `backend/app/context_engine/`, `backend/app/sandbox/`, `backend/context_engine.py`, `database/schema.sql`

- [ ] **Step 1: Create `backend/Dockerfile.agent` with Python 3.11, Docker CLI, Tree-sitter binaries**
- [ ] **Step 2: Unify schema in `backend/schema.sql` and update `docker-compose.yml`**
- [ ] **Step 3: Remove duplicate/deprecated legacy directories**

---

### Task 7: Comprehensive Automated Backend Tests

**Files:**
- Modify: `backend/test_core.py`

- [ ] **Step 1: Write and run comprehensive unit tests for AST parser, Sandbox runner, LLM adapter, and Orchestrator**
- [ ] **Step 2: Verify all tests pass with exit code 0**

---

### Task 8: Next.js 14 Monaco Web IDE Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/next.config.js`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/editor/MonacoEditor.tsx`
- Modify: `frontend/src/components/editor/MonacoInlineDiff.tsx`
- Create: `frontend/src/components/chat/ChatPanel.tsx`
- Create: `frontend/src/components/filetree/FileTree.tsx`
- Create: `frontend/src/components/terminal/TerminalPanel.tsx`

- [ ] **Step 1: Setup frontend configuration (`package.json`, `tsconfig.json`, `tailwind.config.ts`, `next.config.js`)**
- [ ] **Step 2: Implement SSE client helper in `frontend/src/lib/api.ts`**
- [ ] **Step 3: Implement Editor, Diff, Chat, FileTree, and Terminal UI components**
- [ ] **Step 4: Connect main IDE layout in `frontend/src/app/page.tsx`**

---

### Task 9: Verification & Documentation

- [ ] **Step 1: Execute `backend/test_core.py`**
- [ ] **Step 2: Update README.md and ARCHITECTURE.md with updated usage instructions**
