# AI Coding Agent Platform (Cursor-Class Web Architecture)

## 1. System Architecture & Agent Loop Workflow

### High-Level Architecture Overview
```
+-----------------------------------------------------------------------------------+
|                            FRONTEND (Next.js 14 App Router)                       |
|  +---------------------------+  +-----------------------------------------------+  |
|  | Monaco Editor Workspace   |  | AI Agent Workspace (Side Panel + Floating Cmd)|  |
|  | - Virtual File Tree       |  | - SSE / WebSocket Stream Client               |  |
|  | - Inline Diff Decorator   |  | - Multi-turn Prompt Box & Chat History        |  |
|  | - AST Symbol Highlighting |  | - Terminal xterm.js Sandbox Stream            |  |
|  +---------------------------+  +-----------------------------------------------+  |
+------------------------------------------+----------------------------------------+
                                           | HTTP / WebSocket / SSE
                                           v
+-----------------------------------------------------------------------------------+
|                        FASTAPI AGENT BACKEND (Python 3.11+)                       |
|  +-----------------------------------------------------------------------------+  |
|  | Context Engine                                                              |  |
|  |  * Tree-Sitter AST Parser (Chunking by Function/Class/Scope)                |  |
|  |  * Hybrid Search: Dense (pgvector HNSW) + Sparse (BM25 lexical search)       |  |
|  |  * Real-Time File Watcher & Incremental Ingestion Cache                     |  |
|  +-----------------------------------------------------------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  | Agentic Orchestrator (ReAct + Tool Calling Loop)                            |  |
|  |  * Planner / Reasoner (Gemini 1.5 Pro / Claude 3.5 Sonnet / GPT-4o)         |  |
|  |  * Multi-File Edit Engine with Precise Unified-Diff Synthesizer             |  |
|  |  * Self-Correction Loop (Execute -> Catch Error -> Patch AST -> Verify)     |  |
|  +-----------------------------------------------------------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  | Secure Sandbox Client                                                       |  |
|  |  * Docker Isolated Container per Session / E2B MicroVM                      |  |
|  |  * Ephemeral Linux Shell, Compiler, Test Runner, PTY Bridge                 |  |
|  +-----------------------------------------------------------------------------+  |
+-------------------+---------------------------------------+-----------------------+
                    |                                       |
                    v                                       v
+---------------------------------------+  +----------------------------------------+
|          POSTGRESQL + PGVECTOR        |  |          ISOLATED DOCKER SANDBOX       |
|  * projects & sessions                |  |  * Dedicated Container per workspace   |
|  * codebase_chunks (1536-dim vector)  |  |  * Cgroup CPU/Memory quota             |
|  * agent_memory (Episodic + Semantic) |  |  * Read/Write File Mounting            |
|  * diff_history & checkpoints         |  |  * Network policy isolated sandbox     |
+---------------------------------------+  +----------------------------------------+
```

### Agent Loop Lifecycle (ReAct + Reflection)
1. **User Prompt Ingestion**: User requests a feature (e.g., `Refactor auth middleware and add test cases`).
2. **Context Assembly**:
   - Query pgvector + BM25 with prompt keywords.
   - Parse active file AST to retrieve exact symbol definitions & dependencies.
   - Build Token-Budgeted Prompt Context (< 32k tokens).
3. **Reasoning & Tool Selection (ReAct)**:
   - Thought: Analyze file tree and determine required changes.
   - Action: Call tools (`read_file`, `find_symbol`, `apply_diff`, `execute_terminal`).
4. **Execution & Sandboxing**:
   - Modifies files in memory / disk worktree.
   - Runs `pytest` / `npm test` inside Docker container sandbox.
5. **Self-Correction & Feedback**:
   - If tests fail, the stderr output is fed back into the agent context for dynamic self-healing.
6. **Streaming Result**:
   - Streams unified diffs to Monaco Editor with inline green/red gutter decorations.
