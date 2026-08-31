"use client";

import React, { useState, useEffect } from "react";
import {
  FileTree,
} from "@/components/filetree/FileTree";
import { MonacoEditor } from "@/components/editor/MonacoEditor";
import { MonacoInlineDiff } from "@/components/editor/MonacoInlineDiff";
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
import { Code2, FolderGit2, CheckCircle2, AlertCircle } from "lucide-react";

export default function Home() {
  const [workspacePath, setWorkspacePath] = useState("./workspace");
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [activeFile, setActiveFile] = useState<string>("");
  const [activeCode, setActiveCode] = useState<string>("");
  const [originalDiffCode, setOriginalDiffCode] = useState<string | null>(null);
  const [modifiedDiffCode, setModifiedDiffCode] = useState<string | null>(null);
  const [diffFilePath, setDiffFilePath] = useState<string>("");

  // LLM State
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("9router");
  const [selectedModel, setSelectedModel] = useState<string>("claude-3-7-sonnet");
  const [apiKey, setApiKey] = useState<string>("sk-6414cfe3f30d0a5c-tpa041-d36f53fa");

  // Chat & Terminal State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<TerminalLog[]>([]);

  // Load Models and File Tree on mount
  useEffect(() => {
    async function init() {
      const modelList = await fetchModels();
      if (modelList.length > 0) {
        setProviders(modelList);
        setSelectedProvider(modelList[0].id);
        setSelectedModel(modelList[0].default_model);
      }
      await refreshFiles();
    }
    init();
  }, [workspacePath]);

  const refreshFiles = async () => {
    const tree = await fetchFileTree(workspacePath);
    setFileTree(tree);
  };

  const handleSelectFile = async (filePath: string) => {
    try {
      const content = await readFile(workspacePath, filePath);
      setActiveFile(filePath);
      setActiveCode(content);
      // Exit diff view if we switch files
      setOriginalDiffCode(null);
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

          // If file modified, automatically update active file if it matches
          if (event.type === "file_modified" && event.path) {
            refreshFiles();
            if (event.path === activeFile) {
              readFile(workspacePath, event.path).then((c) => {
                setOriginalDiffCode(activeCode);
                setModifiedDiffCode(c);
                setDiffFilePath(event.path || "");
              });
            }
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
          <div className="flex items-center gap-1.5 text-neutral-400 bg-neutral-900 px-2.5 py-1 rounded border border-neutral-800">
            <FolderGit2 className="w-3.5 h-3.5 text-neutral-500" />
            <span className="font-mono">{workspacePath}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-emerald-400">
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
            onRefresh={refreshFiles}
            onCreateFile={handleCreateFile}
          />
        </aside>

        {/* Center: Monaco Editor & Terminal */}
        <main className="flex-1 flex flex-col h-full overflow-hidden">
          <div className="flex-1 overflow-hidden">
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
                onChange={setActiveCode}
                onSave={handleSaveFile}
              />
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
              const provObj = providers.find((item) => item.id === p);
              if (provObj && provObj.models.length > 0) {
                setSelectedModel(provObj.models[0]);
              }
            }}
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
            apiKey={apiKey}
            onApiKeyChange={setApiKey}
            messages={messages}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
            onReviewDiff={handleReviewDiff}
          />
        </aside>
      </div>
    </div>
  );
}
