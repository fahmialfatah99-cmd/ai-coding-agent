# AI Coding Agent Core Platform - Architectural Design Specification

- **Date**: 2026-08-31
- **Status**: Approved
- **Scope**: Backend Refactor & Consolidation, Multi-Provider LLM Integration, Database Unification, Docker Containerization, and Full Next.js 14 Monaco Web IDE Implementation.

---

## 1. System Architecture Overview

```
+---------------------------------------------------------------------------------------+
|                               FRONTEND (Next.js 14 Web IDE)                          |
|  +---------------------+  +--------------------------------+  +---------------------+  |
|  | File Tree & History |  | Monaco Editor Workspace        |  | AI Assistant Panel  |  |
|  | - Virtual Workspace |  | - Code Editing + Highlighting  |  | - Provider/Model Sel|  |
|  | - Session Manager   |  | - Inline Diff Accept/Reject    |  | - SSE ReAct Stream  |  |
|  +---------------------+  +--------------------------------+  | - Tools & Diff View |  |
|  +---------------------------------------------------------+  +---------------------+  |
|  | Terminal Console (Interactive Execution Logs & Sandbox Stream)                     |  |
|  +----------------------------------------------------------------------------------+  |
+-------------------------------------------+-------------------------------------------+
                                            | REST API & Server-Sent Events (SSE)
                                            v
+---------------------------------------------------------------------------------------+
|                               FASTAPI AGENT BACKEND                                   |
|  +--------------------------+  +--------------------------+  +---------------------+  |
|  | Multi-Provider LLM Client|  | ReAct Agent Orchestrator |  | Context Engine (AST)|  |
|  | (OpenAI/Claude/Gemini/Oll)|  | (Plan->Act->Test->Heal)  |  | (Tree-sitter Parser)|  |
|  +--------------------------+  +--------------------------+  +---------------------+  |
|  +---------------------------------------------------------------------------------+  |
|  | Isolated Sandbox Runner (Docker Container + Local Subprocess Fallback)          |  |
|  +---------------------------------------------------------------------------------+  |
+---------------------+-------------------------------------+---------------------------+
                      |                                     |
                      v                                     v
+-------------------------------------+  +----------------------------------------------+
|     POSTGRESQL 16 + PGVECTOR        |  |           DOCKER SANDBOX RUNNER              |
|  - code_chunks (HNSW Vector Index)  |  |  - Isolated memory (512MB) & CPU limit       |
|  - agent_sessions & message history |  |  - Ephemeral test & command execution        |
+-------------------------------------+  +----------------------------------------------+
```

---

## 2. Backend Consolidation & Multi-Provider Architecture

### 2.1 Multi-Provider LLM Adapter (`backend/app/engine/llm_adapter.py`)
Provides unified asynchronous completion and streaming across providers:
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini` (via standard OpenAI API key or custom `base_url`).
- **Google Gemini**: `gemini-2.0-flash`, `gemini-1.5-pro` (via OpenAI-compatible endpoint or Gemini SDK).
- **Anthropic**: `claude-3-7-sonnet`, `claude-3-5-sonnet` (via OpenAI-compatible bridge or Native SDK).
- **Local/Ollama**: `deepseek-r1`, `qwen2.5-coder`, `llama3.3` (via OpenAI-compatible `http://localhost:11434/v1`).

Standardizes Tool Definitions and Tool Calls into JSON Schema compatible schemas across all models.

### 2.2 ReAct Orchestration Engine (`backend/app/engine/orchestrator.py`)
- **Tools Supported**:
  1. `read_file(path)`: Reads target workspace file.
  2. `write_file(path, content)`: Creates or completely updates file.
  3. `apply_diff_patch(path, target_string, replacement_string)`: Atomic search-and-replace edit.
  4. `run_sandbox_command(command)`: Executes terminal command in isolated container.
  5. `search_ast_symbols(query, path)`: Extracts symbol signatures using Tree-sitter.
- **Self-Healing Loop**: If `run_sandbox_command` fails with non-zero exit code or compiler error, the stderr output is automatically injected into the message context for recursive self-correction (up to `max_iterations`).
- **Real-Time Streaming**: Emits Server-Sent Events (`data: {"type": "thought" | "tool_call" | "tool_result" | "warning" | "message" | "done", ...}`).

### 2.3 AST Context Engine (`backend/app/engine/ast_parser.py`)
- Multi-language support (Python, JS, TS, TSX, Go, Rust) via Tree-sitter.
- Fallback sliding-window line chunking for syntax errors or unsupported extensions.
- SHA-256 content checksums for incremental caching and pgvector sync.

### 2.4 Isolated Sandbox (`backend/app/engine/docker_sandbox.py`)
- Spawns disposable container with RAM constraint (`512MB`), CPU quota (`1.0 CPU`), and network isolation options.
- Transparent fallback to safe local subprocess execution if Docker engine is unavailable in the environment.

---

## 3. Database Schema & Vector Indexing

Unified in `backend/schema.sql`:
- `workspaces`: Project root and metadata.
- `code_chunks`: 1536-dimensional vector embedding, file path, symbol name, symbol type, start/end lines, content hash.
- `idx_code_chunks_embedding_hnsw`: HNSW index (`m=16, ef_construction=64`) for <10ms similarity queries.
- `agent_sessions` & `agent_messages`: Session and multi-turn message history tracking.
- `tool_execution_logs`: Execution audit log.

---

## 4. Frontend Architecture (Next.js 14)

### 4.1 UI Layout Breakdown
1. **Header Toolbar**: Model selector (OpenAI / Gemini / Claude / Ollama), Workspace switcher, Run / Save actions.
2. **Left Panel (File Explorer)**: Virtual file tree, create/delete file, active file selection.
3. **Center Panel (Monaco Editor & Diff Inspector)**:
   - Monaco Editor with multi-tab support and syntax highlighting.
   - Inline Diff Inspector with green/red gutter decoration and Accept/Reject buttons.
4. **Right Panel (AI Agent Chat)**:
   - Multi-turn conversational interface.
   - Real-time ReAct stream visualization (Thought badges, Tool invocation cards with status indicator, Agent output).
5. **Bottom Panel (Terminal / Logs)**:
   - Collapsible terminal viewer for command outputs, build logs, and test results.

### 4.2 Frontend Tech Stack
- Next.js 14 (App Router)
- React 18, TypeScript
- Tailwind CSS
- Lucide React (Icons)
- `@monaco-editor/react`

---

## 5. Verification & Testing Plan

1. **Backend Unit Tests**: Expand `backend/test_core.py` to test:
   - Tree-sitter AST Chunker (Python, JS/TS).
   - Multi-provider LLM Adapter mock and tool call parsing.
   - Sandbox execution & local fallback.
   - Orchestrator tool dispatching & self-healing error catch.
2. **API Endpoint Verification**:
   - `GET /`: Health check.
   - `GET /api/v1/models`: List available providers and models.
   - `POST /api/v1/agent/run`: Streaming SSE test.
3. **Frontend Build Verification**:
   - Next.js project build and lint test.
