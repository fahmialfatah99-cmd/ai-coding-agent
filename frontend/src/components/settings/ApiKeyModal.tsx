"use client";

import React, { useState, useEffect } from "react";
import {
  Key,
  X,
  Check,
  Eye,
  EyeOff,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { ModelProvider } from "@/lib/api";

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ModelProvider[];
  selectedProvider: string;
  onSelectProvider: (providerId: string) => void;
  apiKey: string;
  onSaveApiKey: (providerId: string, key: string, baseUrl?: string) => void;
  baseUrl: string;
  onRefreshModels?: () => void;
}

const PROVIDER_DOCS: Record<string, { url: string; label: string; placeholder: string }> = {
  gemini: {
    url: "https://aistudio.google.com/app/apikey",
    label: "Get Google Gemini Key (AI Studio)",
    placeholder: "AIzaSy...",
  },
  "9router": {
    url: "https://github.com/fahmialfatah99-cmd/ai-coding-agent",
    label: "9Router Gateway Docs",
    placeholder: "sk-3b791e4140c2fd0c-s2g2dt-fe07f69f",
  },
  openai: {
    url: "https://platform.openai.com/api-keys",
    label: "Get OpenAI API Key",
    placeholder: "sk-proj-...",
  },
  anthropic: {
    url: "https://console.anthropic.com/settings/keys",
    label: "Get Anthropic API Key",
    placeholder: "sk-ant-...",
  },
  groq: {
    url: "https://console.groq.com/keys",
    label: "Get Groq API Key (Free / Ultra-fast)",
    placeholder: "gsk_...",
  },
  openrouter: {
    url: "https://openrouter.ai/keys",
    label: "Get OpenRouter API Key",
    placeholder: "sk-or-...",
  },
  deepseek: {
    url: "https://platform.deepseek.com/api_keys",
    label: "Get DeepSeek API Key",
    placeholder: "sk-...",
  },
  together: {
    url: "https://api.together.ai/settings/api-keys",
    label: "Get Together AI Key",
    placeholder: "...",
  },
  mistral: {
    url: "https://console.mistral.ai/api-keys/",
    label: "Get Mistral AI Key",
    placeholder: "...",
  },
  cohere: {
    url: "https://dashboard.cohere.com/api-keys",
    label: "Get Cohere API Key",
    placeholder: "...",
  },
  ollama: {
    url: "https://ollama.com/",
    label: "Ollama Local Setup",
    placeholder: "(No key required for local Ollama)",
  },
};

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  providers,
  selectedProvider,
  onSelectProvider,
  apiKey,
  onSaveApiKey,
  baseUrl,
  onRefreshModels,
}) => {
  const [activeTab, setActiveTab] = useState<string>(selectedProvider || "gemini");
  const [currentKeyInput, setCurrentKeyInput] = useState<string>("");
  const [currentUrlInput, setCurrentUrlInput] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      const p = selectedProvider || "9router";
      setActiveTab(p);
      loadProviderValues(p);
    }
  }, [isOpen, selectedProvider]);

  const loadProviderValues = (pId: string) => {
    const default9Key = "sk-3b791e4140c2fd0c-s2g2dt-fe07f69f";
    const savedKey = localStorage.getItem(`ai_agent_key_${pId}`);
    if (savedKey !== null) {
      setCurrentKeyInput(savedKey);
    } else if (pId === "9router") {
      setCurrentKeyInput(localStorage.getItem("ai_agent_api_key") || default9Key);
    } else if (pId === selectedProvider) {
      setCurrentKeyInput(apiKey || "");
    } else {
      setCurrentKeyInput("");
    }

    const savedUrl = localStorage.getItem(`ai_agent_base_url_${pId}`);
    if (savedUrl !== null) {
      setCurrentUrlInput(savedUrl);
    } else if (pId === selectedProvider) {
      setCurrentUrlInput(baseUrl || "");
    } else {
      setCurrentUrlInput("");
    }
  };

  const handleTabChange = (pId: string) => {
    setActiveTab(pId);
    loadProviderValues(pId);
    setSavedSuccess(false);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onSelectProvider(activeTab);
    onSaveApiKey(activeTab, currentKeyInput, currentUrlInput);
    setSavedSuccess(true);
    if (onRefreshModels) {
      setTimeout(() => onRefreshModels(), 100);
    }
    setTimeout(() => {
      setSavedSuccess(false);
    }, 2000);
  };

  if (!isOpen) return null;

  const currentProviderObj = providers.find((p) => p.id === activeTab);
  const docInfo = PROVIDER_DOCS[activeTab] || {
    url: "",
    label: "Provider API Keys",
    placeholder: "sk-...",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-[#181818] border border-neutral-700 rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-800 bg-[#141414]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-neutral-100 flex items-center gap-2">
                <span>LLM Providers & API Keys Configuration</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950/80 border border-purple-700/60 text-purple-300 font-normal">
                  Antigravity Ready
                </span>
              </h2>
              <p className="text-[11px] text-neutral-400">
                Konfigurasi API key langsung untuk Google Gemini, 9Router, OpenAI, Claude, dan provider lainnya.
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

        {/* Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar: Provider List */}
          <div className="w-52 border-r border-neutral-800 bg-[#141414]/50 p-2 space-y-1 overflow-y-auto">
            <div className="text-[10px] uppercase font-semibold text-neutral-500 px-2 py-1 tracking-wider">
              Pilih Provider
            </div>
            {providers.map((p) => {
              const isSelected = activeTab === p.id;
              const hasKey = !!localStorage.getItem(`ai_agent_key_${p.id}`) || (p.id === "9router");
              return (
                <button
                  key={p.id}
                  onClick={() => handleTabChange(p.id)}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition text-left ${
                    isSelected
                      ? "bg-accent text-white shadow-sm"
                      : "text-neutral-300 hover:bg-neutral-800 hover:text-white"
                  }`}
                >
                  <div className="truncate">
                    <span>{p.name}</span>
                  </div>
                  {hasKey && (
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        isSelected ? "bg-white" : "bg-emerald-400"
                      }`}
                      title="API Key configured"
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Right Area: Form Configuration */}
          <div className="flex-1 p-5 overflow-y-auto bg-[#181818]">
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <h3 className="text-sm font-bold text-neutral-100">
                    {currentProviderObj?.name || activeTab}
                  </h3>
                  {currentProviderObj?.requires_api_key === false ? (
                    <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-700/60 rounded px-2 py-0.5 font-medium">
                      No API Key Required
                    </span>
                  ) : (
                    docInfo.url && (
                      <a
                        href={docInfo.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-[11px] text-accent hover:underline"
                      >
                        <span>{docInfo.label}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )
                  )}
                </div>
                {currentProviderObj?.description && (
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    {currentProviderObj.description}
                  </p>
                )}
              </div>

              {/* API Key Input */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-neutral-300 flex items-center justify-between">
                  <span>API Key</span>
                  {currentKeyInput && (
                    <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-normal">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>Key Terisi</span>
                    </span>
                  )}
                </label>
                <div className="relative flex items-center">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={currentKeyInput}
                    onChange={(e) => setCurrentKeyInput(e.target.value)}
                    placeholder={docInfo.placeholder}
                    className="w-full bg-neutral-950 border border-neutral-700 rounded-lg px-3 py-2 text-xs text-neutral-100 font-mono focus:outline-none focus:border-accent pr-10"
                  />
                  {currentKeyInput && (
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 text-neutral-400 hover:text-neutral-200 transition"
                      title={showPassword ? "Hide API Key" : "Show API Key"}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  )}
                </div>
                <p className="text-[11px] text-neutral-500">
                  Tersimpan aman di browser localStorage. Tidak dikirim ke server selain untuk memproses request AI.
                </p>
              </div>

              {/* Base URL Override */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-neutral-300">
                  Base URL (Opsional / Override)
                </label>
                <input
                  type="text"
                  value={currentUrlInput}
                  onChange={(e) => setCurrentUrlInput(e.target.value)}
                  placeholder={
                    activeTab === "9router"
                      ? "http://127.0.0.1:20128/v1"
                      : activeTab === "ollama"
                      ? "http://127.0.0.1:11434/v1"
                      : "https://generativelanguage.googleapis.com/v1beta/openai"
                  }
                  className="w-full bg-neutral-950 border border-neutral-700 rounded-lg px-3 py-2 text-xs text-neutral-100 font-mono focus:outline-none focus:border-accent"
                />
                <p className="text-[11px] text-neutral-500">
                  Gunakan kolom ini jika Anda menjalankan local proxy, custom gateway, atau port khusus.
                </p>
              </div>

              {/* Available Models Preview */}
              {currentProviderObj?.models && currentProviderObj.models.length > 0 && (
                <div className="pt-2 border-t border-neutral-800/80">
                  <div className="text-[11px] font-semibold text-neutral-400 mb-1.5 flex items-center justify-between">
                    <span>Model Tersedia ({currentProviderObj.models.length}):</span>
                    {onRefreshModels && (
                      <button
                        type="button"
                        onClick={onRefreshModels}
                        className="text-[10px] text-accent hover:underline flex items-center gap-1"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Live Sync</span>
                      </button>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto p-1 bg-neutral-950/60 rounded-lg border border-neutral-800">
                    {currentProviderObj.models.slice(0, 15).map((m) => (
                      <span
                        key={m}
                        className="px-2 py-0.5 bg-neutral-900 border border-neutral-800 rounded text-[10px] font-mono text-neutral-300"
                      >
                        {m}
                      </span>
                    ))}
                    {currentProviderObj.models.length > 15 && (
                      <span className="px-2 py-0.5 bg-neutral-900 border border-neutral-800 rounded text-[10px] font-mono text-neutral-500">
                        +{currentProviderObj.models.length - 15} lainnya
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-4 border-t border-neutral-800 flex items-center justify-between">
                <div className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
                  {savedSuccess && (
                    <>
                      <Check className="w-4 h-4" />
                      <span>Berhasil disimpan & diaktifkan!</span>
                    </>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-3.5 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-xs font-medium transition"
                  >
                    Tutup
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-accent hover:bg-blue-600 text-white rounded-lg text-xs font-semibold shadow-md transition flex items-center gap-1.5"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Simpan & Gunakan Provider Ini</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
