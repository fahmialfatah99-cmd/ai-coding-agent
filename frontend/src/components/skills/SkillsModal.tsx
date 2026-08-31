"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  Brain,
  Wrench,
  X,
  FileCode,
  CheckCircle,
  Terminal,
  Search,
  BookOpen,
  Layers,
  ShieldCheck,
  Cpu,
  Palette,
} from "lucide-react";
import { readFile, writeFile } from "@/lib/api";

interface SkillsModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspacePath: string;
}

export const SkillsModal: React.FC<SkillsModalProps> = ({
  isOpen,
  onClose,
  workspacePath,
}) => {
  const [activeTab, setActiveTab] = useState<"skills" | "memory" | "architecture">("skills");
  const [memoryContent, setMemoryContent] = useState<string>("");
  const [isEditingMemory, setIsEditingMemory] = useState(false);
  const [editedMemory, setEditedMemory] = useState("");
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadMemoryFile();
    }
  }, [isOpen, workspacePath]);

  const loadMemoryFile = async () => {
    try {
      const content = await readFile(workspacePath, "MEMORY.md");
      setMemoryContent(content);
      setEditedMemory(content);
    } catch {
      const defaultText = "# 🧠 Project Knowledge & Learned Conventions\n\nNo custom rules recorded yet. Tell the AI 'Ingat aturan...' to record new persistent conventions!";
      setMemoryContent(defaultText);
      setEditedMemory(defaultText);
    }
  };

  const handleSaveMemory = async () => {
    try {
      await writeFile(workspacePath, "MEMORY.md", editedMemory);
      setMemoryContent(editedMemory);
      setIsEditingMemory(false);
      setSaveStatus("Saved successfully!");
      setTimeout(() => setSaveStatus(null), 2000);
    } catch (e: any) {
      setSaveStatus(`Failed to save: ${e.message}`);
    }
  };

  if (!isOpen) return null;

  const skillsList = [
    {
      id: "write_file",
      name: "Direct Code Synthesizer",
      category: "Code Creation",
      icon: FileCode,
      color: "text-emerald-400 bg-emerald-950/50 border-emerald-800/50",
      description: "Menulis, menyusun, dan membuat file kode baru langsung di workspace komputer Anda secara otomatis.",
      trigger: "Otomatis dipanggil saat membuat file, fungsi, atau fitur baru."
    },
    {
      id: "apply_diff_patch",
      name: "Atomic Surgical Patcher",
      category: "Refactoring",
      icon: Wrench,
      color: "text-blue-400 bg-blue-950/50 border-blue-800/50",
      description: "Menerapkan perbaikan search-and-replace presisi tanpa merusak struktur file yang sudah ada.",
      trigger: "Otomatis dipanggil saat refactor, fix bug, atau edit baris tertentu."
    },
    {
      id: "search_ast_symbols",
      name: "Tree-sitter AST Semantic Parser",
      category: "Code Intelligence",
      icon: Search,
      color: "text-purple-400 bg-purple-950/50 border-purple-800/50",
      description: "Menganalisis definisi Class, Function, Interface, dan AST symbol boundaries di Python, JS, TS, Go, dan Rust.",
      trigger: "Otomatis dipanggil saat AI membedah arsitektur codebase."
    },
    {
      id: "run_sandbox_command",
      name: "Isolated Sandbox & Compiler Runner",
      category: "Verification & Testing",
      icon: Terminal,
      color: "text-amber-400 bg-amber-950/50 border-amber-800/50",
      description: "Menjalankan perintah terminal, test suite (pytest/npm test), linter, dan git clone di sandbox terisolasi.",
      trigger: "Otomatis dipanggil untuk menguji kode dan self-healing."
    },
    {
      id: "list_workspace_files",
      name: "Full Codebase Discovery",
      category: "Project Navigation",
      icon: Layers,
      color: "text-cyan-400 bg-cyan-950/50 border-cyan-800/50",
      description: "Memindai seluruh direktori dan file di project Anda untuk audit menyeluruh (*Codebase-Wide*).",
      trigger: "Otomatis dipanggil saat disuruh cek/audit seluruh project."
    },
    {
      id: "record_learned_knowledge",
      name: "Persistent Long-Term Memory",
      category: "Continuous Learning",
      icon: Brain,
      color: "text-rose-400 bg-rose-950/50 border-rose-800/50",
      description: "Mencatat aturan kustom, preferensi coding, dan arsitektur ke dalam file MEMORY.md permanen.",
      trigger: "Otomatis dipanggil saat Anda memberi instruksi aturan / 'Ingat bahwa...'."
    },
    {
      id: "ui_ux_pro_max",
      name: "UI/UX Pro Max Design Intelligence",
      category: "UI/UX Design Engine",
      icon: Palette,
      color: "text-fuchsia-400 bg-fuchsia-950/50 border-fuchsia-800/50",
      description: "AI design system terintegrasi: 84 UI styles, 192 color palettes, 74 font pairings, 98 UX micro-interaction guidelines, dan responsive glassmorphism/dark mode standard (NextLevelBuilder).",
      trigger: "Otomatis aktif saat mendesain UI, Tailwind CSS, landing page, dan komponen frontend."
    },
    {
      id: "superpowers_suite",
      name: "Superpowers Engineering Suite",
      category: "Advanced Quality & TDD",
      icon: ShieldCheck,
      color: "text-amber-400 bg-amber-950/50 border-amber-800/50",
      description: "Suite kemampuan software engineering tingkat lanjut: Systematic Debugging (analisis root-cause sebelum coding), Test-Driven Development (TDD), Verification Gates, dan Multi-Agent Planning (Obra).",
      trigger: "Otomatis aktif pada alur investigasi bug, perencanaan arsitektur, dan audit gatekeeper."
    }
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn select-none">
      <div className="bg-[#181818] border border-neutral-800 rounded-xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#141414] border-b border-neutral-800">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <div>
              <h2 className="font-bold text-sm text-neutral-100">Agent Capabilities & Long-Term Memory</h2>
              <p className="text-[11px] text-neutral-400">Daftar skill aktif dan status memori permanen AI Coding Agent</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-5 py-2 bg-[#161616] border-b border-neutral-800 text-xs">
          <button
            onClick={() => setActiveTab("skills")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === "skills"
                ? "bg-accent text-white shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
            }`}
          >
            <Wrench className="w-3.5 h-3.5" />
            <span>Active Skills & Intelligence ({skillsList.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("memory")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === "memory"
                ? "bg-accent text-white shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Persistent Memory (MEMORY.md)</span>
          </button>

          <button
            onClick={() => setActiveTab("architecture")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === "architecture"
                ? "bg-accent text-white shadow-sm"
                : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>3-Tier Memory Architecture</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {/* TAB 1: SKILLS LIST */}
          {activeTab === "skills" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {skillsList.map((s) => {
                const IconComponent = s.icon;
                return (
                  <div
                    key={s.id}
                    className="p-3.5 bg-neutral-900/90 border border-neutral-800/80 rounded-lg flex flex-col justify-between gap-2.5 hover:border-neutral-700 transition"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <div className={`p-1.5 rounded-md border ${s.color}`}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <span className="font-semibold text-xs text-neutral-100">{s.name}</span>
                        </div>
                        <span className="text-[10px] bg-neutral-800 text-neutral-400 px-1.5 py-0.5 rounded font-mono">
                          {s.id}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-300 leading-relaxed mt-1">{s.description}</p>
                    </div>

                    <div className="pt-2 border-t border-neutral-800/60 flex items-center justify-between text-[11px] text-neutral-500">
                      <span>{s.category}</span>
                      <span className="text-emerald-400 font-medium flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Ready
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: PERSISTENT MEMORY */}
          {activeTab === "memory" && (
            <div className="flex flex-col h-full space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-semibold text-neutral-200">Isi File MEMORY.md di Workspace</h3>
                  <p className="text-[11px] text-neutral-400">Semua aturan di bawah ini otomatis selalu diingat oleh AI</p>
                </div>

                <div className="flex items-center gap-2">
                  {saveStatus && (
                    <span className="text-[11px] text-emerald-400 animate-fadeIn">{saveStatus}</span>
                  )}
                  {isEditingMemory ? (
                    <button
                      onClick={handleSaveMemory}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition"
                    >
                      Save Memory
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditingMemory(true)}
                      className="px-3 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded text-xs font-medium transition"
                    >
                      Edit Manual
                    </button>
                  )}
                </div>
              </div>

              {isEditingMemory ? (
                <textarea
                  value={editedMemory}
                  onChange={(e) => setEditedMemory(e.target.value)}
                  rows={14}
                  className="w-full bg-[#121212] border border-neutral-700 rounded-lg p-3 font-mono text-xs text-neutral-200 focus:outline-none focus:border-accent resize-none"
                />
              ) : (
                <div className="bg-[#121212] border border-neutral-800 rounded-lg p-4 font-mono text-xs text-neutral-300 whitespace-pre-wrap max-h-[380px] overflow-y-auto leading-relaxed">
                  {memoryContent}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: 3-TIER MEMORY ARCHITECTURE */}
          {activeTab === "architecture" && (
            <div className="space-y-4 text-xs">
              <div className="p-3.5 bg-neutral-900 border border-neutral-800 rounded-lg flex items-start gap-3">
                <div className="p-2 bg-blue-950/60 border border-blue-800/50 rounded-lg text-blue-400 shrink-0">
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-neutral-100 text-sm mb-1">Tier 1: Active Context & AST Working Memory</h4>
                  <p className="text-neutral-300 leading-relaxed">
                    Menyimpan riwayat percakapan sesi aktif, isi file yang sedang diedit, dan indeks AST symbol function/class. Berjalan di context window LLM (hingga 128k-1M token via 9Router & Claude 3.7).
                  </p>
                </div>
              </div>

              <div className="p-3.5 bg-neutral-900 border border-neutral-800 rounded-lg flex items-start gap-3">
                <div className="p-2 bg-purple-950/60 border border-purple-800/50 rounded-lg text-purple-400 shrink-0">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-neutral-100 text-sm mb-1">Tier 2: Permanent Rules & MEMORY.md</h4>
                  <p className="text-neutral-300 leading-relaxed">
                    Tersimpan permanen di file `MEMORY.md` dan `.agent/rules.md`. Setiap kali Anda membuka Web IDE atau me-restart server, aturan ini langsung dimuat otomatis ke sistem AI.
                  </p>
                </div>
              </div>

              <div className="p-3.5 bg-neutral-900 border border-neutral-800 rounded-lg flex items-start gap-3">
                <div className="p-2 bg-emerald-950/60 border border-emerald-800/50 rounded-lg text-emerald-400 shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-neutral-100 text-sm mb-1">Tier 3: PostgreSQL + pgvector HNSW Semantic Search</h4>
                  <p className="text-neutral-300 leading-relaxed">
                    Menyimpan embedding potongan kode untuk jutaan baris kode dengan kecepatan retrieval sub-10ms, memungkinkan AI mengingat relasi modul bahkan di project enterprise yang sangat besar.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
