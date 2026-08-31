# AI Coding Agent Platform Architecture

## 1. Arsitektur Sistem

Platform ini terdiri dari beberapa komponen utama yang bekerja secara terintegrasi:

1.  **Frontend (Next.js + Monaco Editor)**
    *   **Web IDE:** Menggunakan Monaco Editor untuk pengalaman coding yang kaya (syntax highlighting, intellisense).
    *   **Chat Interface:** Panel chat untuk berinteraksi dengan AI Agent.
    *   **Inline Edit:** UI untuk menerima/menolak perubahan kode (diff view) langsung di dalam editor.

2.  **Backend (Python / FastAPI)**
    *   **API Gateway:** Menangani request dari frontend (WebSocket untuk real-time streaming, REST untuk CRUD).
    *   **Agentic Orchestrator:** Otak dari sistem, mengelola state, memori, dan alur kerja agen (ReAct).
    *   **Context Engine:** Menggabungkan RAG (Retrieval-Augmented Generation) menggunakan pgvector dan AST Parsing (Tree-sitter) untuk memahami struktur dan semantik kode.

3.  **Secure Sandbox (Docker / E2B)**
    *   Lingkungan terisolasi untuk mengeksekusi kode, menjalankan test suite, linter, dan perintah terminal lainnya.
    *   Mencegah eksekusi kode berbahaya di server utama.

4.  **Database (PostgreSQL + pgvector)**
    *   Menyimpan data pengguna, proyek, sesi chat, dan memori agen.
    *   Menyimpan vector embeddings dari codebase untuk pencarian semantik (RAG).

## 2. Alur Kerja Agen (Agent Loop - ReAct Pattern)

Agen beroperasi menggunakan pola **ReAct (Reasoning + Acting)** dengan kemampuan *self-correction*:

1.  **User Input:** Pengguna memberikan instruksi (misal: "Buatkan fitur login").
2.  **Context Retrieval (Observe):**
    *   Agen mencari konteks yang relevan menggunakan Vector Search (RAG) dan AST Parsing (mencari definisi fungsi/kelas terkait).
3.  **Reasoning (Think):**
    *   LLM menganalisis instruksi dan konteks, lalu merencanakan langkah-langkah penyelesaian.
4.  **Tool Execution (Act):**
    *   Agen memanggil *tools* (misal: `read_file`, `write_file`, `apply_diff_patch`).
5.  **Verification (Execute & Self-Correct):**
    *   Agen menjalankan perintah di Secure Sandbox (misal: `pytest`, `npm run build`).
    *   Jika gagal (error), agen membaca output error, kembali ke fase *Think*, dan melakukan perbaikan kode (*Self-Healing*).
6.  **Final Output:** Agen memberikan respons ke pengguna beserta perubahan kode (diff) di editor.

## 3. Struktur Direktori Proyek

```text
ai-coding-agent/
├── frontend/                 # Next.js Frontend
│   ├── components/
│   │   ├── editor/           # Monaco Editor wrapper & Inline Diff
│   │   ├── chat/             # Chat UI components
│   │   └── terminal/         # Xterm.js terminal emulator
│   ├── pages/
│   └── styles/
├── backend/                  # Python FastAPI Backend
│   ├── api/                  # REST & WebSocket endpoints
│   ├── agent/
│   │   ├── orchestrator.py   # Core ReAct Agent Loop
│   │   ├── tools.py          # Tool definitions (read, write, run_cmd)
│   │   └── memory.py         # Session & conversation memory management
│   ├── context/
│   │   ├── rag.py            # Vector embedding & retrieval (pgvector)
│   │   └── ast_parser.py     # Tree-sitter integration
│   ├── sandbox/
│   │   └── docker_manager.py # E2B / Docker execution wrapper
│   ├── main.py               # FastAPI application entry point
│   └── schema.sql            # Database schema
├── docker-compose.yml        # Local development setup
└── README.md
```