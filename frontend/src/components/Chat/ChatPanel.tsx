"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Bot,
  User,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Terminal,
  FileCode,
  AlertTriangle,
  CheckCircle,
  Key,
  Cpu,
  StopCircle,
  RefreshCw,
} from "lucide-react";
import { ModelProvider, AgentSSEEvent } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  thoughts?: string[];
  toolCalls?: {
    tool: string;
    args: any;
    result?: any;
  }[];
  modifiedFiles?: {
    path: string;
    diff: string;
  }[];
  warning?: string;
  isStreaming?: boolean;
}

interface ChatPanelProps {
  providers: ModelProvider[];
  selectedProvider: string;
  onProviderChange: (providerId: string) => void;
  selectedModel: string;
  onModelChange: (model: string) => void;
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  messages: ChatMessage[];
  isStreaming: boolean;
  onSendMessage: (prompt: string) => void;
  onStopStreaming?: () => void;
  onReviewDiff?: (filePath: string, diff: string) => void;
  onRefreshModels?: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  providers,
  selectedProvider,
  onProviderChange,
  selectedModel,
  onModelChange,
  apiKey,
  onApiKeyChange,
  messages,
  isStreaming,
  onSendMessage,
  onStopStreaming,
  onReviewDiff,
  onRefreshModels,
}) => {
  const [inputPrompt, setInputPrompt] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [expandedThoughts, setExpandedThoughts] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeProviderObj = providers.find((p) => p.id === selectedProvider) || providers[0];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim() || isStreaming) return;
    onSendMessage(inputPrompt);
    setInputPrompt("");
  };

  const toggleThought = (msgId: string) => {
    setExpandedThoughts((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="flex flex-col h-full bg-[#181818] border-l border-neutral-800 text-neutral-200">
      {/* Top Header Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#141414] border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span className="font-semibold text-xs tracking-wide">AI AGENT ASSISTANT</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Provider / Model Selector */}
          <select
            value={selectedProvider}
            onChange={(e) => onProviderChange(e.target.value)}
            className="bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent"
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <select
            value={selectedModel}
            onChange={(e) => onModelChange(e.target.value)}
            className="bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs rounded px-2 py-1 focus:outline-none focus:border-accent"
          >
            {activeProviderObj?.models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>

          {onRefreshModels && (
            <button
              onClick={onRefreshModels}
              className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded transition"
              title="Auto-Detect & Sync 9Router Combos/Models"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-1.5 rounded transition ${
              showSettings ? "bg-accent text-white" : "text-neutral-400 hover:bg-neutral-800"
            }`}
            title="Configure API Key"
          >
            <Key className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Settings / API Key Popdown */}
      {showSettings && (
        <div className="p-3 bg-neutral-900 border-b border-neutral-800 text-xs flex flex-col gap-2 animate-fadeIn">
          <label className="text-neutral-400 font-medium">
            API Key for {activeProviderObj?.name || selectedProvider}:
          </label>
          <input
            type="password"
            placeholder="sk-... / AIzaSy..."
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            className="w-full bg-neutral-950 border border-neutral-700 rounded px-2.5 py-1.5 text-xs text-neutral-200 focus:outline-none focus:border-accent"
          />
          <span className="text-[10px] text-neutral-500">
            Stored locally in session memory. Ollama does not require an API key.
          </span>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-neutral-500 py-12">
            <Bot className="w-10 h-10 mb-3 text-neutral-600 animate-pulse" />
            <p className="text-sm font-medium text-neutral-400">How can I help you code today?</p>
            <p className="text-xs max-w-xs mt-1 text-neutral-600">
              Ask me to build a feature, refactor code, run sandbox tests, or fix bugs autonomously.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col gap-2 ${
              msg.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`flex items-start gap-2.5 max-w-[92%] ${
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-purple-600 text-white"
                }`}
              >
                {msg.role === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              <div className="flex flex-col gap-2 w-full">
                {/* User Message Bubble */}
                {msg.role === "user" ? (
                  <div className="p-3 bg-blue-600/20 border border-blue-500/30 rounded-lg text-xs leading-relaxed text-blue-100 whitespace-pre-wrap">
                    {msg.content}
                  </div>
                ) : (
                  <div className="space-y-2 w-full">
                    {/* Thought Expander */}
                    {msg.thoughts && msg.thoughts.length > 0 && (
                      <div className="bg-neutral-900/90 border border-neutral-800 rounded-md overflow-hidden text-xs">
                        <button
                          onClick={() => toggleThought(msg.id)}
                          className="w-full flex items-center justify-between px-3 py-1.5 bg-neutral-900 hover:bg-neutral-800/80 text-neutral-400 text-[11px] font-mono transition"
                        >
                          <span className="flex items-center gap-1.5">
                            <Cpu className="w-3 h-3 text-purple-400" />
                            Thought Process ({msg.thoughts.length} steps)
                          </span>
                          {expandedThoughts[msg.id] ? (
                            <ChevronDown className="w-3 h-3" />
                          ) : (
                            <ChevronRight className="w-3 h-3" />
                          )}
                        </button>
                        {expandedThoughts[msg.id] && (
                          <div className="p-2.5 space-y-1.5 border-t border-neutral-800/50 bg-[#121212] font-mono text-[11px] text-neutral-400">
                            {msg.thoughts.map((t, idx) => (
                              <div key={idx} className="flex gap-2">
                                <span className="text-neutral-600 select-none">›</span>
                                <span>{t}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Tool Calls */}
                    {msg.toolCalls && msg.toolCalls.map((tc, idx) => (
                      <div
                        key={idx}
                        className="bg-neutral-900 border border-neutral-800 rounded-md p-2 text-xs font-mono"
                      >
                        <div className="flex items-center justify-between text-purple-300 font-semibold mb-1">
                          <span className="flex items-center gap-1.5">
                            <Terminal className="w-3 h-3 text-purple-400" />
                            Tool: {tc.tool}
                          </span>
                          <span className="text-[10px] text-neutral-500">Executed</span>
                        </div>
                        <div className="text-[11px] text-neutral-400 bg-black/40 p-1.5 rounded overflow-x-auto">
                          {JSON.stringify(tc.args, null, 2)}
                        </div>
                      </div>
                    ))}

                    {/* File Modified Badge / Diff Review trigger */}
                    {msg.modifiedFiles && msg.modifiedFiles.map((mf, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 bg-emerald-950/30 border border-emerald-800/40 rounded text-xs text-emerald-300"
                      >
                        <div className="flex items-center gap-1.5">
                          <FileCode className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Modified: {mf.path}</span>
                        </div>
                        {onReviewDiff && (
                          <button
                            onClick={() => onReviewDiff(mf.path, mf.diff)}
                            className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-medium transition"
                          >
                            Review Diff
                          </button>
                        )}
                      </div>
                    ))}

                    {/* Warning / Self-Correction Note */}
                    {msg.warning && (
                      <div className="flex items-start gap-1.5 p-2 bg-amber-950/30 border border-amber-800/40 rounded text-xs text-amber-300">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                        <span>{msg.warning}</span>
                      </div>
                    )}

                    {/* Assistant Text Response */}
                    {msg.content && (
                      <div className="p-3 bg-neutral-900 border border-neutral-800 rounded-lg text-xs leading-relaxed text-neutral-200 whitespace-pre-wrap">
                        {msg.content}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-purple-400 animate-pulse font-mono pl-8">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Agent reasoning and executing tools...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="p-3 bg-[#141414] border-t border-neutral-800">
        <div className="relative flex items-center">
          <textarea
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Ask agent to edit, test, or generate code..."
            rows={2}
            className="w-full bg-[#1e1e1e] border border-neutral-700 rounded-lg pl-3 pr-20 py-2 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-accent resize-none"
          />

          <div className="absolute right-2.5 bottom-2.5 flex items-center gap-1.5">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className="p-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded transition"
                title="Stop execution"
              >
                <StopCircle className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!inputPrompt.trim()}
                className={`p-1.5 rounded transition ${
                  inputPrompt.trim()
                    ? "bg-accent hover:bg-blue-600 text-white shadow-sm"
                    : "bg-neutral-800 text-neutral-600 cursor-not-allowed"
                }`}
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};
