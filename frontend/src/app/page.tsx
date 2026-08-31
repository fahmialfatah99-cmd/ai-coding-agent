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
  readFile,
  writeFile,
  fetchModels,
  executeSandboxCommand,
  streamAgentTask,
  FileNode,
  ModelProvider,
  AgentSSEEvent,
} from "@/lib/api";
import { Code2, FolderGit2, CheckCircle2, AlertCircle, Edit3, Check, Eye, Columns, Brain } from "lucide-react";

export default function Home() {
  const [workspacePath, setWorkspacePath] = useState("./workspace");
  const [isEditingWorkspace, setIsEditingWorkspace] = useState(false);
  const [tempWorkspaceInput, setTempWorkspaceInput] = useState("./workspace");
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [activeFile, setActiveFile] = useState<string>("");
  const [activeCode, setActiveCode] = useState<string>("");
  const [viewMode, setViewMode] = useState<"editor" | "preview" | "split">("editor");
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState(false);
  const [originalDiffCode, setOriginalDiffCode] = useState<string | null>(null);
  const [modifiedDiffCode, setModifiedDiffCode] = useState<string | null>(null);
  const [diffFilePath, setDiffFilePath] = useState<string>("");

  // LLM State with Persistence
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("9router");
  const [selectedModel, setSelectedModel] = useState<string>("all");
  const [apiKey, setApiKey] = useState<string>("sk-6414cfe3f30d0a5c-tpa041-d36f53fa");

  // Chat & Terminal State with Persistence
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<TerminalLog[]>([]);

  // 1. Initial LocalStorage Restore & Initialization
  useEffect(() => {
    const savedWorkspace = localStorage.getItem("ai_agent_workspace_path");
    if (savedWorkspace) {
      setWorkspacePath(savedWorkspace);
      setTempWorkspaceInput(savedWorkspace);
    }
    // Restore Saved Settings
    const savedKey = localStorage.getItem("ai_agent_api_key");
    if (savedKey) setApiKey(savedKey);

    const savedProvider = localStorage.getItem("ai_agent_provider");
    if (savedProvider) setSelectedProvider(savedProvider);

    const savedModel = localStorage.getItem("ai_agent_model");
    if (savedModel) setSelectedModel(savedModel);

    const savedMessages = localStorage.getItem("ai_agent_messages");
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (e) {
        console.error("Failed to parse saved chat messages", e);
      }
    }

    async function init() {
      await refreshModelsList(savedKey || apiKey);
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

  const refreshModelsList = async (keyToUse?: string) => {
    const modelList = await fetchModels(keyToUse || apiKey);
    if (modelList.length > 0) {
      setProviders(modelList);
      const activeP = modelList.find((p) => p.id === selectedProvider) || modelList[0];
      setSelectedProvider(activeP.id);
      if (activeP.models.length > 0 && !activeP.models.includes(selectedModel)) {
        setSelectedModel(activeP.models[0]);
      }
    }
  };

  const refreshFiles = async (): Promise<FileNode[]> => {
    const tree = await fetchFileTree(workspacePath);
    setFileTree(tree);
    return tree;
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
          provider: selectedProvider,
          model: selectedModel,
          api_key: apiKey || undefined,
        },
        (event: AgentSSEEvent) => {
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== assistantMsgId) return msg;

              switch (event.type) {
                case "thought":
                  return {
                    ...msg,
                    thoughts: [...(msg.thoughts || []), event.content || ""],
                  };
                case "tool_call":
                  return {
                    ...msg,
                    toolCalls: [
                      ...(msg.toolCalls || []),
                      { tool: event.tool || "", args: event.args },
                    ],
                  };
                case "tool_result":
                  return {
                    ...msg,
                    toolCalls: (msg.toolCalls || []).map((tc) =>
                      tc.tool === event.tool ? { ...tc, result: event.result } : tc
                    ),
                  };
                case "file_modified":
                  return {
                    ...msg,
                    modifiedFiles: [
                      ...(msg.modifiedFiles || []),
                      { path: event.path || "", diff: event.diff || "" },
                    ],
                  };
                case "warning":
                  return {
                    ...msg,
                    warning: event.content,
                  };
                case "message":
                  return {
                    ...msg,
                    content: event.content || "",
                  };
                case "done":
                  return {
                    ...msg,
                    isStreaming: false,
                  };
                default:
                  return msg;
              }
            })
          );

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

  const handleReviewDiff = async (filePath: string, diff: string) => {
    try {
      const current = await readFile(workspacePath, filePath);
      setDiffFilePath(filePath);
      setOriginalDiffCode(activeCode || current);
      setModifiedDiffCode(current);
    } catch (e) {
      console.error(e);
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
          {isEditingWorkspace ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (tempWorkspaceInput.trim()) {
                  const cleaned = tempWorkspaceInput.trim();
                  setWorkspacePath(cleaned);
                  localStorage.setItem("ai_agent_workspace_path", cleaned);
                  setIsEditingWorkspace(false);
                }
              }}
              className="flex items-center gap-1"
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
            <div
              onClick={() => {
                setTempWorkspaceInput(workspacePath);
                setIsEditingWorkspace(true);
              }}
              className="flex items-center gap-1.5 text-neutral-400 bg-neutral-900 hover:bg-neutral-800/80 cursor-pointer px-2.5 py-1 rounded border border-neutral-800 transition"
              title="Click to change local target folder"
            >
              <FolderGit2 className="w-3.5 h-3.5 text-neutral-500" />
              <span className="font-mono">{workspacePath}</span>
              <Edit3 className="w-3 h-3 text-neutral-500 hover:text-neutral-300 ml-1" />
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
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
                setSelectedModel(provObj.models[0]);
                localStorage.setItem("ai_agent_model", provObj.models[0]);
              }
            }}
            selectedModel={selectedModel}
            onModelChange={(m) => {
              setSelectedModel(m);
              localStorage.setItem("ai_agent_model", m);
            }}
            apiKey={apiKey}
            onApiKeyChange={(key) => {
              setApiKey(key);
              localStorage.setItem("ai_agent_api_key", key);
              refreshModelsList(key);
            }}
            messages={messages}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
            onReviewDiff={handleReviewDiff}
            onRefreshModels={() => refreshModelsList(apiKey)}
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
          />
        </aside>
      </div>

      {/* Skills & Long-Term Memory Modal */}
      <SkillsModal
        isOpen={isSkillsModalOpen}
        onClose={() => setIsSkillsModalOpen(false)}
        workspacePath={workspacePath}
      />
    </div>
  );
}
