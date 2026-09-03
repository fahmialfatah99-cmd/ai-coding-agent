#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo -e "\n🛑 Menghentikan semua layanan (Backend & Frontend)..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "✅ Semua layanan telah dihentikan."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "=========================================="
echo "  🚀 AI Coding Agent - Unified Launcher   "
echo "=========================================="

# 1. Jalankan Backend (FastAPI)
echo "⚡ Menjalankan Backend di http://localhost:8000 ..."
cd "$ROOT_DIR/backend"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 2. Jalankan Frontend (Next.js)
echo "🌐 Menjalankan Frontend di http://localhost:3000 ..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ Semua layanan berhasil dijalankan:"
echo "   - Web IDE  : http://localhost:3000"
echo "   - API Docs : http://localhost:8000/docs"
echo ""
echo "Tekan [Ctrl+C] untuk menghentikan semua layanan."
echo "=========================================="

wait
