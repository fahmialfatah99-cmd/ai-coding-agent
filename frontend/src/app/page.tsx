"use client";

import React, { useState, useEffect } from "react";
import {
  FileTree,
} from "@/components/filetree/FileTree";
import { MonacoEditor } from "@/components/editor/MonacoEditor";
import { MonacoInlineDiff } from "@/components/editor/MonacoInlineDiff";
import { WebPreview } from "@/components/preview/WebPreview";
import { SkillsModal } from "@/components/skills/SkillsModal";
import { ChatPanel, ChatMessage } from "@/components/chat/ChatPanel";
import { TerminalPanel, TerminalLog } from "@/components/terminal/TerminalPanel";
import {
  fetchFileTree,
  fetchWorkspaces,
  readFile,
  writeFile,
  fetchModels,
  executeSandboxCommand,
  streamAgentTask,
  syncProviderModels,
  FileNode,
  ModelProvider,
  AgentSSEEvent,
  DEFAULT_PROVIDERS,
} from "@/lib/api";
import { Code2, FolderGit2, CheckCircle2, AlertCircle, Edit3, Check, Eye, Columns, Brain, ChevronDown, FolderCheck, Sparkles, Github, Key, Trash2 } from "lucide-react";
import { GitHubModal } from "@/components/github/GitHubModal";
import { ApiKeyModal } from "@/components/settings/ApiKeyModal";
import { ClearHistoryModal } from "@/components/settings/ClearHistoryModal";

export default function Home() {
  const [workspacePath, setWorkspacePath] = useState("./workspace");
  const [availableWorkspaces, setAvailableWorkspaces] = useState<{ name: string; path: string; abs_path: string }[]>([]);
  const [isEditingWorkspace, setIsEditingWorkspace] = useState(false);
  const [isWorkspaceDropdownOpen, setIsWorkspaceDropdownOpen] = useState(false);
  const [tempWorkspaceInput, setTempWorkspaceInput] = useState("./workspace");
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [activeFile, setActiveFile] = useState<string>("");
  const [activeCode, setActiveCode] = useState<string>("");
  const [viewMode, setViewMode] = useState<"editor" | "preview" | "split">("editor");
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState(false);
  const [isGitHubModalOpen, setIsGitHubModalOpen] = useState(false);
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState(false);
  const [isClearHistoryModalOpen, setIsClearHistoryModalOpen] = useState(false);
  const [originalDiffCode, setOriginalDiffCode] = useState<string | null>(null);
  const [modifiedDiffCode, setModifiedDiffCode] = useState<string | null>(null);
  const [diffFilePath, setDiffFilePath] = useState<string>("");

  // LLM State with Persistence
  const [providers, setProviders] = useState<ModelProvider[]>(DEFAULT_PROVIDERS);
  const [selectedProvider, setSelectedProvider] = useState<string>("9router");
  const [selectedModel, setSelectedModel] = useState<string>("ag/gemini-3.7-flash-high");
  const [apiKey, setApiKey] = useState<string>("sk-3b791e4140c2fd0c-s2g2dt-fe07f69f");
  const [baseUrl, setBaseUrl] = useState<string>("");

  // Chat & Terminal State with Persistence
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [executionMode, setExecutionMode] = useState<"solo" | "team">("team");
  const [terminalLogs, setTerminalLogs] = useState<TerminalLog[]>([]);

  // 1. Initial LocalStorage Restore & Initialization
  useEffect(() => {
    const savedWorkspace = localStorage.getItem("ai_agent_workspace_path");
    if (savedWorkspace) {
      setWorkspacePath(savedWorkspace);
      setTempWorkspaceInput(savedWorkspace);
    }
    // Restore Saved Provider & Provider-Specific Settings
    const default9RouterKey = "sk-3b791e4140c2fd0c-s2g2dt-fe07f69f";
    const savedProviderId = localStorage.getItem("ai_agent_provider") || "9router";
    setSelectedProvider(savedProviderId);

    const savedProviderKey = localStorage.getItem(`ai_agent_key_${savedProviderId}`);
    const globalKey = localStorage.getItem("ai_agent_api_key");
    const activeKeyToUse = savedProviderKey !== null ? savedProviderKey : (globalKey || (savedProviderId === "9router" ? default9RouterKey : ""));
    setApiKey(activeKeyToUse);

    const savedProviderUrl = localStorage.getItem(`ai_agent_base_url_${savedProviderId}`);
    const globalUrl = localStorage.getItem("ai_agent_base_url");
    const activeUrlToUse = savedProviderUrl !== null ? savedProviderUrl : (globalUrl || "");
    setBaseUrl(activeUrlToUse);

    const savedMode = localStorage.getItem("ai_agent_execution_mode") as "solo" | "team" | null;
    if (savedMode) {
      setExecutionMode(savedMode);
    } else {
      setExecutionMode("team");
    }

    const savedModel = localStorage.getItem("ai_agent_model");
    if (savedModel && savedModel !== "all") {
      setSelectedModel(savedModel);
    } else {
      setSelectedModel("ag/gemini-3.7-flash-high");
    }

    const savedMessages = localStorage.getItem("ai_agent_messages");
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (e) {
        console.error("Failed to parse saved chat messages", e);
      }
    }

    async function init() {
      await refreshModelsList(activeKeyToUse, activeUrlToUse || undefined);
      const tree = await refreshFiles();

      // Restore last opened file
      const savedActiveFile = localStorage.getItem("ai_agent_active_file");
      if (savedActiveFile) {
        handleSelectFile(savedActiveFile);
      } else if (tree && tree.length > 0) {
        // Auto-open first file if available
        const firstFile = findFirstFile(tree);
        if (firstFile) handleSelectFile(firstFile);
      }
    }
    init();
  }, [workspacePath]);

  // Helper to find first code file in tree
  const findFirstFile = (nodes: FileNode[]): string | null => {
    for (const node of nodes) {
      if (!node.is_dir) return node.path;
      if (node.children && node.children.length > 0) {
        const sub = findFirstFile(node.children);
        if (sub) return sub;
      }
    }
    return null;
  };

  // 2. Persist Messages whenever updated
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("ai_agent_messages", JSON.stringify(messages.slice(-50)));
    }
  }, [messages]);

  const refreshModelsList = async (keyToUse?: string, urlToUse?: string) => {
    const activeKey = keyToUse ?? apiKey;
    const activeUrl = urlToUse ?? baseUrl;
    const modelList = await fetchModels(activeKey, activeUrl);
    if (modelList && modelList.length > 0) {
      setProviders(modelList);
      const targetProvider = localStorage.getItem("ai_agent_provider") || selectedProvider;
      const activeP = modelList.find((p) => p.id === targetProvider) || modelList[0];
      if (activeP) {
        setSelectedProvider(activeP.id);
        const savedM = localStorage.getItem("ai_agent_model");
        if (savedM && activeP.models.includes(savedM)) {
          setSelectedModel(savedM);
        } else if (activeP.models.length > 0 && !activeP.models.includes(selectedModel)) {
          setSelectedModel(activeP.models[0]);
        }
      }
    }
  };

  // Generic refresh: re-sync the currently-selected provider's model list live.
  const handleRefreshModels = async () => {
    const result = await syncProviderModels({
      provider: selectedProvider,
      api_key: apiKey || undefined,
      base_url: baseUrl || undefined,
    });
    if (result && result.models && result.models.length > 0) {
      setProviders((prev) =>
        prev.map((p) =>
          p.id === selectedProvider
            ? {
                ...p,
                models: result.models.includes(p.default_model)
                  ? result.models
                  : [p.default_model, ...result.models],
                default_model: p.default_model,
              }
            : p
        )
      );
    } else {
      // Fallback: re-pull the whole catalog.
      await refreshModelsList(apiKey);
    }
  };

  const refreshFiles = async (): Promise<FileNode[]> => {
    try {
      const [tree, ws] = await Promise.all([
        fetchFileTree(workspacePath),
        fetchWorkspaces(),
      ]);
      setFileTree(tree);
      if (ws && ws.length > 0) {
        setAvailableWorkspaces(ws);
      }
      return tree;
    } catch {
      return [];
    }
  };

  const handleSelectFile = async (filePath: string) => {
    try {
      const content = await readFile(workspacePath, filePath);
      setActiveFile(filePath);
      setActiveCode(content);
      setOriginalDiffCode(null);
      localStorage.setItem("ai_agent_active_file", filePath);
    } catch (err) {
      console.error("Failed to open file", err);
    }
  };

  const handleSaveFile = async () => {
    if (!activeFile) return;
    try {
      await writeFile(workspacePath, activeFile, activeCode);
      await refreshFiles();
    } catch (err) {
      console.error("Failed to save file", err);
    }
  };

  const handleCreateFile = async (fileName: string) => {
    try {
      await writeFile(workspacePath, fileName, "");
      await refreshFiles();
      await handleSelectFile(fileName);
    } catch (err) {
      console.error("Failed to create file", err);
    }
  };

  const handleTerminalExec = async (cmd: string) => {
    try {
      const res = await executeSandboxCommand(workspacePath, cmd);
      const newLog: TerminalLog = {
        id: Date.now().toString(),
        command: cmd,
        stdout: res.stdout || "",
        stderr: res.stderr || "",
        exitCode: res.exit_code,
        environment: res.environment,
        timestamp: new Date().toLocaleTimeString(),
      };
      setTerminalLogs((prev) => [...prev, newLog]);
    } catch (err: any) {
      const errLog: TerminalLog = {
        id: Date.now().toString(),
        command: cmd,
        stdout: "",
        stderr: err.message || "Failed to execute command",
        exitCode: -1,
        timestamp: new Date().toLocaleTimeString(),
      };
      setTerminalLogs((prev) => [...prev, errLog]);
    }
  };

  // ReAct SSE Agent Stream Trigger
  const handleSendMessage = async (prompt: string) => {
    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: prompt },
      {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        thoughts: [],
        toolCalls: [],
        modifiedFiles: [],
        isStreaming: true,
      },
    ]);

    setIsStreaming(true);

    try {
      await streamAgentTask(
        {
          instruction: prompt,
          active_file: activeFile || undefined,
          file_content: activeCode || undefined,
          workspace_path: workspacePath,
          mode: executionMode,
          provider: selectedProvider,
          model: selectedModel,
          api_key: apiKey || undefined,
          base_url: baseUrl || undefined,
        },
        (event: AgentSSEEvent) => {
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== assistantMsgId) return msg;

              const role = event.agent_role || msg.agentRole;
              const name = event.agent_name || msg.agentName;

              switch (event.type) {
                case "thought":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    thoughts: [...(msg.thoughts || []), event.content || ""],
                  };
                case "tool_call":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    toolCalls: [
                      ...(msg.toolCalls || []),
                      { tool: event.tool || "", args: event.args },
                    ],
                  };
                case "tool_result":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    toolCalls: (msg.toolCalls || []).map((tc) =>
                      tc.tool === event.tool ? { ...tc, result: event.result } : tc
                    ),
                  };
                case "file_modified":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    modifiedFiles: [
                      ...(msg.modifiedFiles || []),
                      { path: event.path || "", diff: event.diff || "" },
                    ],
                  };
                case "warning":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    warning: event.content,
                  };
                case "audit":
                  return {
                    ...msg,
                    agentRole: event.agent_role || "auditor",
                    agentName: event.agent_name || "Strict Quality Auditor",
                    auditStatus: event.audit_status,
                    auditCycle: event.audit_cycle,
                    auditFeedback: event.audit_feedback,
                    content: event.content
                      ? msg.content
                        ? `${msg.content}\n\n${event.content}`
                        : event.content
                      : msg.content,
                  };
                case "message":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    content: msg.content ? `${msg.content}\n\n${event.content}` : event.content || "",
                  };
                case "done":
                  return {
                    ...msg,
                    agentRole: role,
                    agentName: name,
                    content: msg.content || event.content || "Pemeriksaan dan eksekusi tugas telah selesai.",
                    isStreaming: false,
                  };
                case "error":
                  return {
                    ...msg,
                    content: (msg.content ? `${msg.content}\n\n` : "") + `⚠️ Error: ${event.content}`,
                    isStreaming: false,
                  };
                default:
                  return msg;
              }
            })
          );

          if (event.type === "done" || event.type === "error") {
            setIsStreaming(false);
          }

          // If file modified or created, automatically load it into Monaco Editor!
          if (event.type === "file_modified" && event.path) {
            const modifiedPath = event.path;
            refreshFiles();
            readFile(workspacePath, modifiedPath)
              .then((c) => {
                setActiveFile(modifiedPath);
                setActiveCode(c);
                localStorage.setItem("ai_agent_active_file", modifiedPath);
                if (event.diff) {
                  setDiffFilePath(modifiedPath);
                }
                // If HTML or SVG, automatically enable split preview!
                if (modifiedPath.endsWith(".html") || modifiedPath.endsWith(".htm") || modifiedPath.endsWith(".svg")) {
                  setViewMode("split");
                }
              })
              .catch(console.error);
          }
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? { ...msg, content: `Error: ${err.message}`, isStreaming: false }
            : msg
        )
      );
    } finally {
      setIsStreaming(false);
      refreshFiles();
    }
  };

  const handleReviewDiff = async (filePath: string, diff?: string) => {
    try {
      const current = await readFile(workspacePath, filePath);
      setActiveFile(filePath);
      setActiveCode(current);
      setDiffFilePath(filePath);
      setViewMode("editor");
      localStorage.setItem("ai_agent_active_file", filePath);

      if (diff && diff.trim()) {
        setOriginalDiffCode(activeCode && activeCode !== current ? activeCode : current);
        setModifiedDiffCode(current);
      } else {
        setOriginalDiffCode(null);
        setModifiedDiffCode(null);
      }
    } catch (e) {
      console.error("Failed to open or review diff for file", e);
    }
  };

  const handleAcceptDiff = async (newCode: string) => {
    if (diffFilePath) {
      await writeFile(workspacePath, diffFilePath, newCode);
      setActiveCode(newCode);
      setActiveFile(diffFilePath);
      localStorage.setItem("ai_agent_active_file", diffFilePath);
    }
    setOriginalDiffCode(null);
    setModifiedDiffCode(null);
    await refreshFiles();
  };

  const handleRejectDiff = () => {
    setOriginalDiffCode(null);
    setModifiedDiffCode(null);
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#121212] overflow-hidden">
      {/* Top Navbar */}
      <header className="flex items-center justify-between px-4 py-2 bg-[#181818] border-b border-neutral-800 text-xs select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 font-bold text-neutral-100 tracking-wide text-sm">
            <Code2 className="w-5 h-5 text-accent" />
            <span>AI CODING AGENT</span>
          </div>
          <span className="text-neutral-600">|</span>

          {/* 1-Click Workspace Folder Selector & Switcher */}
          <div className="relative">
            {isEditingWorkspace ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (tempWorkspaceInput.trim()) {
                    const cleaned = tempWorkspaceInput.trim();
                    setWorkspacePath(cleaned);
                    localStorage.setItem("ai_agent_workspace_path", cleaned);
                    setIsEditingWorkspace(false);
                    setIsWorkspaceDropdownOpen(false);
                    setActiveFile("");
                    setActiveCode("");
                    localStorage.removeItem("ai_agent_active_file");
                  }
                }}
                className="flex items-center gap-1.5 bg-neutral-900 px-2 py-1 rounded border border-accent"
              >
                <input
                  type="text"
                  value={tempWorkspaceInput}
                  onChange={(e) => setTempWorkspaceInput(e.target.value)}
                  placeholder="C:/path/to/folder or ./workspace"
                  autoFocus
                  className="bg-neutral-950 border border-accent rounded px-2 py-0.5 font-mono text-[11px] text-neutral-200 focus:outline-none w-64"
                />
                <button
                  type="submit"
                  className="p-1 bg-accent text-white rounded hover:bg-blue-600 transition"
                  title="Apply Local Folder"
                >
                  <Check className="w-3 h-3" />
                </button>
              </form>
            ) : (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsWorkspaceDropdownOpen(!isWorkspaceDropdownOpen)}
                  className="flex items-center gap-1.5 text-neutral-300 bg-neutral-900 hover:bg-neutral-800 cursor-pointer px-2.5 py-1 rounded border border-neutral-800 transition text-xs font-mono select-none"
                  title="Click to choose or switch project folder"
                >
                  <FolderGit2 className="w-3.5 h-3.5 text-amber-400" />
                  <span className="font-semibold">{workspacePath}</span>
                  <ChevronDown className="w-3 h-3 text-neutral-500" />
                </button>

                <button
                  onClick={() => {
                    setTempWorkspaceInput(workspacePath);
                    setIsEditingWorkspace(true);
                  }}
                  className="p-1 text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800 rounded transition"
                  title="Type custom path manually"
                >
                  <Edit3 className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Folder Selection Dropdown Popup */}
            {isWorkspaceDropdownOpen && !isEditingWorkspace && (
              <div className="absolute left-0 top-full mt-1.5 w-72 bg-[#181818] border border-neutral-700 rounded-lg shadow-2xl p-2 z-50 animate-fadeIn select-none">
                <div className="flex items-center justify-between px-2 py-1 text-[10px] font-semibold text-neutral-400 uppercase tracking-wider border-b border-neutral-800 mb-1">
                  <span>Available Project Folders</span>
                  <span className="text-[9px] text-neutral-500">1-Click Switch</span>
                </div>

                <div className="space-y-1 max-h-56 overflow-y-auto">
                  {(availableWorkspaces || []).map((ws) => {
                    const isSelected = workspacePath === ws.path || workspacePath === ws.name;
                    return (
                      <button
                        key={ws.path}
                        onClick={() => {
                          setWorkspacePath(ws.path);
                          setTempWorkspaceInput(ws.path);
                          localStorage.setItem("ai_agent_workspace_path", ws.path);
                          setIsWorkspaceDropdownOpen(false);
                          setActiveFile("");
                          setActiveCode("");
                          localStorage.removeItem("ai_agent_active_file");
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition text-left ${
                          isSelected
                            ? "bg-accent text-white font-medium shadow-sm"
                            : "text-neutral-300 hover:bg-neutral-800"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <FolderGit2 className={`w-3.5 h-3.5 shrink-0 ${isSelected ? "text-white" : "text-amber-400"}`} />
                          <span className="truncate">{ws.name}</span>
                        </div>
                        {isSelected && <FolderCheck className="w-3.5 h-3.5 shrink-0 text-white" />}
                      </button>
                    );
                  })}
                </div>

                <div className="pt-2 mt-1 border-t border-neutral-800">
                  <button
                    onClick={() => {
                      setIsEditingWorkspace(true);
                      setIsWorkspaceDropdownOpen(false);
                    }}
                    className="w-full flex items-center justify-center gap-1 px-2 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded text-[11px] font-medium transition"
                  >
                    <Edit3 className="w-3 h-3 text-neutral-400" />
                    <span>Enter Custom / External Path...</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Real-Time Agent Process vs Idle Indicator */}
          {isStreaming ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-purple-950/90 border border-purple-700 text-purple-200 text-xs font-semibold animate-pulse shadow-[0_0_12px_rgba(168,85,247,0.4)] select-none">
              <Sparkles className="w-3.5 h-3.5 text-purple-400 animate-spin" />
              <span className="text-[11px] font-bold">AGENT: PROSES (BEKERJA...)</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-neutral-900 border border-neutral-800 text-emerald-400 text-xs font-medium select-none">
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
              <span className="text-[11px]">AGENT: DIAM (SIAP)</span>
            </div>
          )}

          <button
            onClick={() => setIsApiKeyModalOpen(true)}
            className="flex items-center gap-1.5 bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white px-2.5 py-1 rounded border border-neutral-800 transition cursor-pointer text-xs select-none shadow-sm"
            title="Configure LLM API Keys (Google Gemini, 9Router, OpenAI, Claude, Groq, etc.)"
          >
            <Key className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-medium text-[11px]">API Keys</span>
          </button>

          <button
            onClick={() => setIsClearHistoryModalOpen(true)}
            className="flex items-center gap-1.5 bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-rose-300 px-2.5 py-1 rounded border border-neutral-800 transition cursor-pointer text-xs select-none shadow-sm"
            title="Bersihkan Riwayat Chat, Log Sandbox Terminal & Sesi Editor"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span className="font-medium text-[11px]">Bersihkan Riwayat</span>
          </button>

          <button
            onClick={() => setIsGitHubModalOpen(true)}
            className="flex items-center gap-1.5 bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white px-2.5 py-1 rounded border border-neutral-800 transition cursor-pointer text-xs select-none shadow-sm"
            title="Configure GitHub Token & Push Credentials"
          >
            <Github className="w-3.5 h-3.5 text-neutral-200" />
            <span className="font-medium text-[11px]">GitHub</span>
          </button>

          <button
            onClick={() => setIsSkillsModalOpen(true)}
            className="flex items-center gap-1.5 bg-neutral-900 hover:bg-neutral-800 text-neutral-300 hover:text-white px-2.5 py-1 rounded border border-neutral-800 transition cursor-pointer text-xs select-none shadow-sm"
            title="View Active Skills, Tools & Persistent Long-Term Memory"
          >
            <Brain className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-medium text-[11px]">Skills & Memory</span>
          </button>

          <div className="flex items-center gap-1.5 text-emerald-400 select-none">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span className="font-medium text-[11px]">Engine Connected</span>
          </div>
        </div>
      </header>

      {/* Main IDE Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: File Explorer (240px) */}
        <aside className="w-60 shrink-0 h-full">
          <FileTree
            tree={fileTree}
            activeFile={activeFile}
            onSelectFile={handleSelectFile}
            onDeselectFile={() => {
              setActiveFile("");
              setActiveCode("");
              localStorage.removeItem("ai_agent_active_file");
            }}
            onRefresh={refreshFiles}
            onCreateFile={handleCreateFile}
            availableWorkspaces={availableWorkspaces}
            currentWorkspace={workspacePath}
            onNewProject={(newPath) => {
              setWorkspacePath(newPath);
              setTempWorkspaceInput(newPath);
              localStorage.setItem("ai_agent_workspace_path", newPath);
              setActiveFile("");
              setActiveCode("");
              localStorage.removeItem("ai_agent_active_file");
            }}
          />
        </aside>

        {/* Center: Monaco Editor, Live Web Preview, & Terminal */}
        <main className="flex-1 flex flex-col h-full overflow-hidden">
          {/* View Mode Switcher Bar */}
          <div className="flex items-center justify-between px-3 py-1.5 bg-[#161616] border-b border-neutral-800 text-xs select-none">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] text-neutral-400 truncate max-w-[200px]">
                {activeFile ? activeFile : "Untitled"}
              </span>
              {activeFile && (activeFile.endsWith(".html") || activeFile.endsWith(".htm") || activeFile.endsWith(".svg")) && (
                <span className="bg-emerald-950/80 text-emerald-400 text-[10px] px-1.5 py-0.5 rounded border border-emerald-800/40">
                  Live Web Preview
                </span>
              )}
            </div>

            <div className="flex items-center gap-1 bg-neutral-900 p-0.5 rounded border border-neutral-800">
              <button
                onClick={() => setViewMode("editor")}
                className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium transition ${
                  viewMode === "editor"
                    ? "bg-accent text-white shadow-sm"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
                title="Code Editor View"
              >
                <Code2 className="w-3 h-3" />
                <span>Code</span>
              </button>

              <button
                onClick={() => setViewMode("split")}
                className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium transition ${
                  viewMode === "split"
                    ? "bg-accent text-white shadow-sm"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
                title="Split View: Editor & Live Web Preview"
              >
                <Columns className="w-3 h-3" />
                <span>Split</span>
              </button>

              <button
                onClick={() => setViewMode("preview")}
                className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium transition ${
                  viewMode === "preview"
                    ? "bg-accent text-white shadow-sm"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
                title="Full Live Web Preview"
              >
                <Eye className="w-3 h-3" />
                <span>Preview</span>
              </button>
            </div>
          </div>

          <div className="flex-1 flex overflow-hidden">
            {/* Left/Main: Editor */}
            {(viewMode === "editor" || viewMode === "split") && (
              <div className={`${viewMode === "split" ? "w-1/2 border-r border-neutral-800" : "w-full"} h-full overflow-hidden`}>
                {originalDiffCode !== null && modifiedDiffCode !== null ? (
                  <MonacoInlineDiff
                    filePath={diffFilePath}
                    originalCode={originalDiffCode}
                    modifiedCode={modifiedDiffCode}
                    onAccept={handleAcceptDiff}
                    onReject={handleRejectDiff}
                  />
                ) : (
                  <MonacoEditor
                    filePath={activeFile}
                    code={activeCode}
                    onChange={(val) => {
                      setActiveCode(val);
                    }}
                    onSave={handleSaveFile}
                  />
                )}
              </div>
            )}

            {/* Right/Main: Live Web Preview */}
            {(viewMode === "preview" || viewMode === "split") && (
              <div className={`${viewMode === "split" ? "w-1/2" : "w-full"} h-full overflow-hidden`}>
                <WebPreview
                  code={activeCode}
                  filePath={activeFile || "index.html"}
                  onRefresh={refreshFiles}
                />
              </div>
            )}
          </div>

          {/* Bottom: Terminal */}
          <TerminalPanel
            logs={terminalLogs}
            onExecuteCommand={handleTerminalExec}
            onClearLogs={() => setTerminalLogs([])}
          />
        </main>

        {/* Right: AI Chat Assistant (380px) */}
        <aside className="w-96 shrink-0 h-full">
          <ChatPanel
            providers={providers}
            selectedProvider={selectedProvider}
            onProviderChange={(p) => {
              setSelectedProvider(p);
              localStorage.setItem("ai_agent_provider", p);
              const provObj = providers.find((item) => item.id === p);
              if (provObj && provObj.models.length > 0) {
                const savedM = localStorage.getItem(`ai_agent_model_${p}`) || localStorage.getItem("ai_agent_model");
                if (savedM && provObj.models.includes(savedM)) {
                  setSelectedModel(savedM);
                } else {
                  setSelectedModel(provObj.models[0]);
                }
              }
              const default9Key = "sk-3b791e4140c2fd0c-s2g2dt-fe07f69f";
              const savedKey = localStorage.getItem(`ai_agent_key_${p}`);
              if (savedKey !== null) {
                setApiKey(savedKey);
              } else if (p === "9router") {
                setApiKey(localStorage.getItem("ai_agent_api_key") || default9Key);
              } else {
                setApiKey("");
              }

              const savedUrl = localStorage.getItem(`ai_agent_base_url_${p}`);
              if (savedUrl !== null) {
                setBaseUrl(savedUrl);
              } else {
                setBaseUrl("");
              }
            }}
            selectedModel={selectedModel}
            onModelChange={(m) => {
              setSelectedModel(m);
              localStorage.setItem("ai_agent_model", m);
              localStorage.setItem(`ai_agent_model_${selectedProvider}`, m);
            }}
            apiKey={apiKey}
            onApiKeyChange={(key) => {
              setApiKey(key);
              localStorage.setItem("ai_agent_api_key", key);
              localStorage.setItem(`ai_agent_key_${selectedProvider}`, key);
            }}
            baseUrl={baseUrl}
            onBaseUrlChange={(url) => {
              setBaseUrl(url);
              localStorage.setItem("ai_agent_base_url", url);
              localStorage.setItem(`ai_agent_base_url_${selectedProvider}`, url);
            }}
            mode={executionMode}
            onModeChange={(m) => {
              setExecutionMode(m);
              localStorage.setItem("ai_agent_execution_mode", m);
            }}
            messages={messages}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
            onReviewDiff={handleReviewDiff}
            onRefreshModels={handleRefreshModels}
            activeFile={activeFile}
            onClearActiveFile={() => {
              setActiveFile("");
              setActiveCode("");
              localStorage.removeItem("ai_agent_active_file");
            }}
            onClearChat={() => {
              setMessages([]);
              localStorage.removeItem("ai_agent_messages");
            }}
            onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
          />
        </aside>
      </div>

      {/* LLM Providers & API Keys Modal */}
      <ApiKeyModal
        isOpen={isApiKeyModalOpen}
        onClose={() => setIsApiKeyModalOpen(false)}
        providers={providers}
        selectedProvider={selectedProvider}
        onSelectProvider={(pId) => {
          setSelectedProvider(pId);
          localStorage.setItem("ai_agent_provider", pId);
          const provObj = providers.find((p) => p.id === pId);
          if (provObj && provObj.models.length > 0) {
            const savedM = localStorage.getItem(`ai_agent_model_${pId}`) || localStorage.getItem("ai_agent_model");
            if (savedM && provObj.models.includes(savedM)) {
              setSelectedModel(savedM);
            } else {
              setSelectedModel(provObj.models[0]);
            }
          }
        }}
        apiKey={apiKey}
        onSaveApiKey={(pId, key, url) => {
          setApiKey(key);
          localStorage.setItem("ai_agent_api_key", key);
          localStorage.setItem(`ai_agent_key_${pId}`, key);
          if (url !== undefined) {
            setBaseUrl(url);
            localStorage.setItem("ai_agent_base_url", url);
            localStorage.setItem(`ai_agent_base_url_${pId}`, url);
          }
        }}
        baseUrl={baseUrl}
        onRefreshModels={handleRefreshModels}
      />

      {/* Clear History & Reset Session Modal */}
      <ClearHistoryModal
        isOpen={isClearHistoryModalOpen}
        onClose={() => setIsClearHistoryModalOpen(false)}
        chatCount={messages.length}
        terminalCount={terminalLogs.length}
        onClearChat={() => {
          setMessages([]);
          localStorage.removeItem("ai_agent_messages");
        }}
        onClearTerminal={() => {
          setTerminalLogs([]);
        }}
        onClearEditorState={() => {
          setActiveFile("");
          setActiveCode("");
          setOriginalDiffCode(null);
          setModifiedDiffCode(null);
          setDiffFilePath("");
          localStorage.removeItem("ai_agent_active_file");
        }}
        onClearAll={() => {
          setMessages([]);
          localStorage.removeItem("ai_agent_messages");
          setTerminalLogs([]);
          setActiveFile("");
          setActiveCode("");
          setOriginalDiffCode(null);
          setModifiedDiffCode(null);
          setDiffFilePath("");
          localStorage.removeItem("ai_agent_active_file");
        }}
      />

      {/* Skills & Long-Term Memory Modal */}
      <SkillsModal
        isOpen={isSkillsModalOpen}
        onClose={() => setIsSkillsModalOpen(false)}
        workspacePath={workspacePath}
      />

      {/* GitHub Integration Modal */}
      <GitHubModal
        isOpen={isGitHubModalOpen}
        onClose={() => setIsGitHubModalOpen(false)}
        workspacePath={workspacePath}
      />
    </div>
  );
}
