# ⚡ AI Coding Agent Platform (Cursor-Grade Web IDE)

> **Platform AI Software Engineer Otonom** berbasis Web IDE (Monaco Editor), Multi-Provider LLM & **9Router AI Gateway** (Auto-Detect 32+ Model & Combos), 9 Router Modular FastAPI Backend, Tree-sitter Semantic AST Parser, ReAct Agent Orchestrator dengan *Self-Healing Feedback*, dan Isolated Docker Sandbox Runner.

---

## 🌟 Fitur Unggulan

- **9Router AI Gateway & Multi-Provider LLM**: 
  - Auto-deteksi real-time seluruh model & combo kustom dari 9Router (`http://localhost:20128/v1`), Claude 3.7 Sonnet / Opus Thinking, Gemini 3.7 Flash, DeepSeek V4 Pro, OpenAI GPT-4o, dan Ollama Local.
  - Sinkronisasi dinamis 32+ combo dengan 1 tombol di UI (🔄).
- **Arsitektur 9 Router Modular**:
  - `/agent`: ReAct autonomous loop & SSE streaming.
  - `/workspaces`: Manajemen multi-project & isolasi root.
  - `/files`: File tree explorer, read, write, delete dengan auto-save lokal.
  - `/context`: AST parsing & semantic symbol extraction.
  - `/vector`: PostgreSQL pgvector HNSW similarity search (<10ms).
  - `/sandbox`: Eksekusi container terisolasi & status command.
  - `/models`: Dynamic model catalog & live gateway sync.
  - `/sessions`: Multi-turn chat persistence & thread management.
  - `/diff`: Unified diff synthesizer & atomic patcher.
- **Monaco Web IDE Interaktif**:
  - Multi-language syntax highlighting, shortcut `Ctrl+S`, dan inline diff reviewer (*Accept / Reject* per baris).
  - Auto-open file saat AI membuat atau mengedit kode.
  - Navigasi & pemilihan target folder lokal langsung dari top navbar.
  - Auto-persistence (*LocalStorage*) untuk session chat, tab file aktif, dan konfigurasi API key saat halaman di-refresh.
- **Autonomous ReAct Loop & Self-Healing**:
  - Siklus otonom: *Thought -> Inspect AST -> Direct Code Writing (`write_file`) -> Sandbox Test -> Self-Correction jika terjadi error*.
- **100% Linux & Windows Native**:
  - Dioptimalkan untuk performa tinggi di Linux (native Docker socket, epoll `uvloop`, namespaces) dan Windows (PowerShell/CMD).

---

## 📂 Struktur Proyek

```
ai_coding_agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routers/               # 9 Modular Domain Routers
│   │   │       ├── agent.py           # ReAct loop & SSE streaming
│   │   │       ├── workspaces.py      # Workspace management
│   │   │       ├── files.py           # Local file CRUD & Explorer
│   │   │       ├── context.py         # AST symbol queries
│   │   │       ├── vector.py          # pgvector memory & HNSW search
│   │   │       ├── sandbox.py         # Container execution
│   │   │       ├── models.py          # Dynamic model catalog & 9Router sync
│   │   │       ├── sessions.py        # Chat session persistence
│   │   │       └── diff.py            # Unified diff generator & patcher
│   │   ├── engine/
│   │   │   ├── llm_adapter.py         # Multi-Provider & 9Router SSE parser
│   │   │   ├── orchestrator.py        # ReAct loop + self-healing + tool runner
│   │   │   ├── ast_parser.py          # Tree-sitter multi-language chunker
│   │   │   └── docker_sandbox.py      # Isolated container sandbox
│   │   └── main.py                    # FastAPI entrypoint mounting all 9 routers
│   ├── Dockerfile.agent               # Backend container image
│   ├── requirements.txt               # Backend Python dependencies
│   ├── schema.sql                     # Unified PostgreSQL pgvector schema
│   └── test_core.py                   # Automated core test suite
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root dark-theme layout
│   │   │   ├── page.tsx               # 3-panel IDE workspace layout
│   │   │   └── globals.css            # Dark mode styles & custom scrollbars
│   │   ├── components/
│   │   │   ├── editor/
│   │   │   │   ├── MonacoEditor.tsx   # Monaco code editor
│   │   │   │   └── MonacoInlineDiff.tsx # Side-by-side / inline diff review
│   │   │   ├── chat/
│   │   │   │   └── ChatPanel.tsx      # Assistant chat, thoughts & model picker
│   │   │   ├── filetree/
│   │   │   │   └── FileTree.tsx       # Interactive workspace file tree
│   │   │   └── terminal/
│   │   │       └── TerminalPanel.tsx  # Sandbox execution terminal
│   │   └── lib/
│   │       └── api.ts                 # SSE stream reader & REST API client
│   ├── Dockerfile                     # Frontend Next.js container image
│   └── package.json                   # Next.js 14 & Tailwind dependencies
│
├── workspace/                         # 📁 Direktori penyimpanan lokal kode Anda
├── docker-compose.yml                 # Full stack container orchestration
├── .gitignore                         # Comprehensive security gitignore
└── README.md                          # Dokumentasi lengkap
```

---

## 🐧 Panduan Instalasi & Menjalankan di Linux (Ubuntu / Debian / Arch / Fedora)

Platform ini berjalan sangat cepat dan mulus di Linux berkat native Docker socket dan asynchronous `uvloop`.

### Prasyarat di Linux:
* Python 3.10+ (`sudo apt install python3 python3-pip python3-venv`)
* Node.js 18+ (`sudo apt install nodejs npm` atau via `nvm`)
* Docker & Docker Compose (Opsional, untuk container sandbox)

---

### Opsi A: 1-Click Docker Compose (Paling Direkomendasikan di Linux/Server)

Jalankan seluruh stack (Database Vector + FastAPI Backend + Next.js IDE) hanya dengan 1 perintah:

```bash
# 1. Clone repository
git clone https://github.com/fahmialfatah99-cmd/ai-coding-agent.git
cd ai-coding-agent

# 2. Salin dan konfigurasikan file .env (opsional jika sudah ada default)
cp .env.example .env

# 3. Jalankan semua container di background
docker compose up -d --build
```

Setelah selesai, buka di browser:
* 🌐 **Web IDE**: `http://localhost:3000`
* ⚡ **Backend Engine API**: `http://localhost:8000`
* 📖 **Swagger API Docs (9 Routers)**: `http://localhost:8000/docs`

Untuk menghentikan:
```bash
docker compose down
```

---

### Opsi B: Menjalankan Secara Manual (Development Mode di Linux)

#### 1. Jalankan Backend (FastAPI)
```bash
cd backend

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependensi
pip install -r requirements.txt

# Jalankan server FastAPI
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Jalankan Frontend (Next.js 14)
Buka tab terminal baru:
```bash
cd frontend

# Install packages
npm install

# Jalankan Next.js dev server
npm run dev
```
Buka browser di **`http://localhost:3000`**.

---

### Opsi C: Menjalankan 9Router AI Gateway di Linux

Jika Anda menggunakan 9Router di mesin Linux:
```bash
# Install 9Router secara global via npm
npm install -g 9router

# Jalankan 9router gateway
9router
```
9Router akan aktif di `http://localhost:20128/v1`. Backend dan Web IDE AI Coding Agent akan **otomatis mendeteksi semua combo & model 9Router Anda**.

---

## 🪟 Panduan Menjalankan di Windows

```powershell
# 1. Clone repository
git clone https://github.com/fahmialfatah99-cmd/ai-coding-agent.git
cd ai-coding-agent

# 2. Jalankan Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Di PowerShell baru: Jalankan Frontend
cd frontend
npm install
npm run dev
```

---

## 🧪 Menjalankan Automated Verification Suite

Uji seluruh komponen (Tree-sitter AST, Docker Sandbox, LLM SSE Parser, ReAct Loop, dan 9 Router Endpoints):

```bash
cd backend
python3 test_core.py   # Linux
python test_core.py    # Windows
```

Output yang diharapkan:
```text
[-] AST Parser Python test passed.
[-] AST Parser JavaScript test passed.
[-] Sandbox execution test passed.
[-] LLM Adapter multi-provider definition test passed.
[-] Orchestrator tools and diff patching test passed.
[-] All 9 Modular Router endpoints tested and PASSED successfully.

=> ALL 9-ROUTER SUITE TESTS PASSED 100% SUCCESSFULLY!
```

---

## 💡 Cara Penggunaan Web IDE

1. **Buka Web IDE** di browser: `http://localhost:3000`.
2. **Pilih Provider & Model**:
   - Pilih **`9Router (Auto-Detected Combos)`** di kanan atas.
   - Pilih combo yang Anda inginkan (misal: `all`, `ag/claude-sonnet-4-6`, `ag/gemini-3.7-flash-high`, dll.).
   - Klik tombol **🔄** kapan pun Anda ingin memperbarui daftar combo live dari 9Router.
3. **Kirim Instruksi Coding**:
   - Contoh: *"Buatkan modul authentication JWT lengkap di file `auth.py` dan tuliskan unit testnya di `test_auth.py`."*
4. **Perhatikan Monaco Editor & File Tree**:
   - File baru langsung muncul di panel kiri (Explorer).
   - Monaco Editor di tengah otomatis menampilkan kode yang dibuat.
   - Hasil eksekusi test di sandbox muncul di terminal bawah.
5. **Ganti Folder Target Lokal**:
   - Klik path folder di navbar atas (contoh: `📁 ./workspace ✏️`), lalu masukkan direktori lokal yang ingin Anda kelola.

---

## 🔒 Keamanan & Lisensi

- File sensitif seperti `.env` dan API Key dilindungi dan di-exclude dalam [`.gitignore`](.gitignore).
- Dilindungi di bawah lisensi MIT. Bebas dimodifikasi dan dikembangkan untuk keperluan pribadi atau produksi.
