"use client";

import React, { useState } from "react";
import {
  Trash2,
  X,
  Check,
  AlertTriangle,
  MessageSquare,
  Terminal,
  FileCode,
  RotateCcw,
  CheckCircle2,
} from "lucide-react";

interface ClearHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  chatCount: number;
  terminalCount: number;
  onClearChat: () => void;
  onClearTerminal: () => void;
  onClearEditorState: () => void;
  onClearAll: () => void;
}

export const ClearHistoryModal: React.FC<ClearHistoryModalProps> = ({
  isOpen,
  onClose,
  chatCount,
  terminalCount,
  onClearChat,
  onClearTerminal,
  onClearEditorState,
  onClearAll,
}) => {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAction = (actionName: string, callback: () => void) => {
    callback();
    setSuccessMessage(`${actionName} berhasil dibersihkan!`);
    setTimeout(() => {
      setSuccessMessage(null);
    }, 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-[#181818] border border-neutral-700 rounded-xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-800 bg-[#141414]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400">
              <Trash2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-neutral-100 flex items-center gap-2">
                <span>Bersihkan Riwayat & Sesi</span>
              </h2>
              <p className="text-[11px] text-neutral-400">
                Pilih riwayat data atau log yang ingin Anda bersihkan dari memori aplikasi.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Success Alert */}
        {successMessage && (
          <div className="mx-5 mt-4 p-2.5 bg-emerald-950/60 border border-emerald-700/60 rounded-lg flex items-center gap-2 text-emerald-300 text-xs animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Action Options List */}
        <div className="p-5 space-y-3">
          {/* Option 1: Clear Chat History */}
          <div className="p-3 bg-neutral-900 border border-neutral-800 rounded-lg flex items-center justify-between hover:border-neutral-700 transition">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-purple-950/50 border border-purple-800/60 text-purple-400">
                <MessageSquare className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-200 flex items-center gap-2">
                  <span>Riwayat Percakapan AI</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-400">
                    {chatCount} Pesan
                  </span>
                </div>
                <div className="text-[11px] text-neutral-400">
                  Menghapus seluruh percakapan, instruksi, dan riwayat ReAct agent.
                </div>
              </div>
            </div>
            <button
              onClick={() => handleAction("Riwayat Percakapan", onClearChat)}
              disabled={chatCount === 0}
              className="px-3 py-1.5 bg-neutral-800 hover:bg-rose-950 hover:text-rose-300 hover:border-rose-800 text-neutral-300 border border-neutral-700 rounded-md text-xs font-medium transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              Hapus Chat
            </button>
          </div>

          {/* Option 2: Clear Terminal Logs */}
          <div className="p-3 bg-neutral-900 border border-neutral-800 rounded-lg flex items-center justify-between hover:border-neutral-700 transition">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-blue-950/50 border border-blue-800/60 text-blue-400">
                <Terminal className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-200 flex items-center gap-2">
                  <span>Log Sandbox Terminal</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-neutral-800 text-neutral-400">
                    {terminalCount} Entri
                  </span>
                </div>
                <div className="text-[11px] text-neutral-400">
                  Menghapus output eksekusi bash, status exit code, dan riwayat command.
                </div>
              </div>
            </div>
            <button
              onClick={() => handleAction("Log Sandbox Terminal", onClearTerminal)}
              disabled={terminalCount === 0}
              className="px-3 py-1.5 bg-neutral-800 hover:bg-rose-950 hover:text-rose-300 hover:border-rose-800 text-neutral-300 border border-neutral-700 rounded-md text-xs font-medium transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              Hapus Log
            </button>
          </div>

          {/* Option 3: Clear Active File & Diff State */}
          <div className="p-3 bg-neutral-900 border border-neutral-800 rounded-lg flex items-center justify-between hover:border-neutral-700 transition">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-amber-950/50 border border-amber-800/60 text-amber-400">
                <FileCode className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-neutral-200">
                  <span>Sesi Editor & Review Diff</span>
                </div>
                <div className="text-[11px] text-neutral-400">
                  Menutup file aktif yang terbuka dan membersihkan perbandingan inline diff kode.
                </div>
              </div>
            </div>
            <button
              onClick={() => handleAction("Sesi Editor & Diff", onClearEditorState)}
              className="px-3 py-1.5 bg-neutral-800 hover:bg-amber-950 hover:text-amber-300 hover:border-amber-800 text-neutral-300 border border-neutral-700 rounded-md text-xs font-medium transition cursor-pointer"
            >
              Reset File
            </button>
          </div>

          {/* Option 4: Clear All History / Reset All */}
          <div className="p-3.5 bg-rose-950/20 border border-rose-900/50 rounded-lg flex items-center justify-between mt-2">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-md bg-rose-900/40 text-rose-400">
                <RotateCcw className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-rose-200">
                  <span>Bersihkan Semua Riwayat (Reset Sesi)</span>
                </div>
                <div className="text-[11px] text-rose-300/70">
                  Membersihkan chat, log terminal, dan sesi editor sekaligus. (File kode tidak akan dihapus).
                </div>
              </div>
            </div>
            <button
              onClick={() => handleAction("Semua Riwayat & Sesi", onClearAll)}
              className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-md text-xs font-bold transition shadow-sm cursor-pointer whitespace-nowrap"
            >
              Bersihkan Semua
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-neutral-800 bg-[#141414] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg text-xs font-medium transition"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
