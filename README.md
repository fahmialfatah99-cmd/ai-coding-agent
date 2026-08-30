# AI Coding Agent Core Platform (Cursor-Class Web IDE)

Platform AI Coding Agent otonom berbasis Web IDE (Monaco Editor), Multi-Provider LLM Engine (OpenAI, Google Gemini, Anthropic Claude, Ollama/Local), Tree-sitter AST Chunker, ReAct Orchestrator dengan Self-Healing Feedback, dan Isolated Docker Sandbox Runner.

---

## Fitur Utama

- **Multi-Provider LLM**: Dukungan penuh untuk OpenAI (GPT-4o), Google Gemini (Gemini 2.0 Flash / Pro), Anthropic (Claude 3.7 Sonnet), dan Local/Ollama (DeepSeek R1, Qwen 2.5 Coder).
- **Tree-sitter AST Chunker**: Ekstraksi semantic symbol boundaries (Functions, Classes, Methods) untuk Python, JavaScript, TypeScript, Go, dan Rust.
- **ReAct Agent Loop & Self-Correction**: Eksekusi otonom (Thought -> Action -> Tool -> Sandbox Test -> Self-Healing jika gagal).
- **Monaco Inline Diff Reviewer**: Visualisasi diff modifikasi kode interaktif dengan kontrol *Accept* dan *Reject*.
- **Isolated Docker Sandbox**: Runner eksekusi perintah terminal dengan limit memori 512MB dan 1 CPU (dengan automatic local subprocess fallback).
- **Vector Memory**: PostgreSQL 16 + pgvector dengan HNSW Indexing (<10ms retrieval).

---

## Struktur Proyek

```
ai_coding_agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py              # REST API & SSE streaming endpoints
│   │   ├── engine/
│   │   │   ├── llm_adapter.py         # Multi-Provider LLM client
│   │   │   ├── orchestrator.py        # ReAct agent loop + self-healing
│   │   │   ├── ast_parser.py          # Tree-sitter AST code chunker
│   │   │   └── docker_sandbox.py      # Docker isolated sandbox runner
│   │   └── main.py                    # FastAPI application entrypoint
│   ├── Dockerfile.agent               # Backend container image
│   ├── requirements.txt               # Backend Python dependencies
│   ├── schema.sql                     # Unified pgvector database schema
│   └── test_core.py                   # Automated core test suite
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root dark-theme layout
│   │   │   ├── page.tsx               # Main 3-panel IDE workspace
│   │   │   └── globals.css            # Dark mode styles & custom scrollbars
│   │   ├── components/
│   │   │   ├── editor/
│   │   │   │   ├── MonacoEditor.tsx   # Code editor component
│   │   │   │   └── MonacoInlineDiff.tsx # Inline diff review component
│   │   │   ├── chat/
│   │   │   │   └── ChatPanel.tsx      # Multi-turn streaming chat + model picker
│   │   │   ├── filetree/
│   │   │   │   └── FileTree.tsx       # Workspace file explorer
│   │   │   └── terminal/
│   │   │       └── TerminalPanel.tsx  # Sandbox execution terminal
│   │   └── lib/
│   │       └── api.ts                 # SSE stream reader & REST API client
│   ├── Dockerfile                     # Frontend container image
│   └── package.json                   # Next.js 14 & Tailwind dependencies
│
├── docs/
│   └── superpowers/
│       ├── specs/                     # Architecture design documents
│       └── plans/                     # Step-by-step implementation plans
│
├── docker-compose.yml                 # Full stack container orchestration
├── ARCHITECTURE.md                    # Technical architecture diagram
└── README.md                          # Project documentation
```

---

## Cara Menjalankan

### 1. Menjalankan dengan Docker Compose (Full Stack)
```bash
docker compose up --build
```
- **Frontend IDE**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL pgvector**: `localhost:5432`

### 2. Menjalankan Backend Secara Lokal
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Menjalankan Frontend Secara Lokal
```bash
cd frontend
npm install
npm run dev
```

### 4. Menjalankan Automated Core Tests
```bash
cd backend
python test_core.py
```
