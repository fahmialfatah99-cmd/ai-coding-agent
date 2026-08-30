"use client";

import React, { useState, useRef, useEffect } from "react";
import { Terminal, ChevronUp, ChevronDown, Trash2, Play } from "lucide-react";

export interface TerminalLog {
  id: string;
  command: string;
  stdout: string;
  stderr: string;
  exitCode: number;
  environment?: string;
  timestamp: string;
}

interface TerminalPanelProps {
  logs: TerminalLog[];
  onExecuteCommand: (command: string) => Promise<void>;
  onClearLogs: () => void;
}

export const TerminalPanel: React.FC<TerminalPanelProps> = ({
  logs,
  onExecuteCommand,
  onClearLogs,
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [cmdInput, setCmdInput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cmdInput.trim() || isRunning) return;
    const command = cmdInput.trim();
    setCmdInput("");
    setIsRunning(true);
    try {
      await onExecuteCommand(command);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div
      className={`flex flex-col bg-[#141414] border-t border-neutral-800 transition-all duration-200 ${
        isOpen ? "h-48" : "h-9"
      }`}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#101010] border-b border-neutral-800 text-xs select-none">
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 cursor-pointer text-neutral-400 hover:text-neutral-200"
        >
          <Terminal className="w-3.5 h-3.5 text-accent" />
          <span className="font-mono font-medium text-[11px]">SANDBOX TERMINAL</span>
          {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
        </div>

        {isOpen && (
          <div className="flex items-center gap-2">
            <button
              onClick={onClearLogs}
              className="p-1 text-neutral-500 hover:text-neutral-300 transition"
              title="Clear Terminal"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Terminal Body */}
      {isOpen && (
        <div className="flex-1 flex flex-col overflow-hidden font-mono text-xs">
          <div className="flex-1 overflow-y-auto p-3 space-y-2 text-neutral-300">
            {logs.length === 0 ? (
              <div className="text-neutral-600 text-[11px]">
                Sandbox ready. Run tests or terminal commands below.
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="space-y-1">
                  <div className="flex items-center gap-2 text-neutral-400">
                    <span className="text-accent font-bold">$</span>
                    <span className="text-neutral-200 font-semibold">{log.command}</span>
                    <span
                      className={`text-[10px] px-1.5 rounded ${
                        log.exitCode === 0
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-rose-950 text-rose-400 border border-rose-800"
                      }`}
                    >
                      exit: {log.exitCode}
                    </span>
                    {log.environment && (
                      <span className="text-[10px] text-neutral-500">[{log.environment}]</span>
                    )}
                  </div>

                  {log.stdout && (
                    <pre className="text-neutral-300 whitespace-pre-wrap pl-4 text-[11px] leading-relaxed">
                      {log.stdout}
                    </pre>
                  )}

                  {log.stderr && (
                    <pre className="text-rose-400 whitespace-pre-wrap pl-4 text-[11px] leading-relaxed">
                      {log.stderr}
                    </pre>
                  )}
                </div>
              ))
            )}
            <div ref={terminalEndRef} />
          </div>

          {/* Interactive Command Input */}
          <form onSubmit={handleSubmit} className="flex items-center px-3 py-1.5 bg-[#0d0d0d] border-t border-neutral-800">
            <span className="text-accent font-bold mr-2 select-none">$</span>
            <input
              type="text"
              placeholder="e.g. pytest, python sample.py, npm test"
              value={cmdInput}
              onChange={(e) => setCmdInput(e.target.value)}
              disabled={isRunning}
              className="flex-1 bg-transparent text-xs text-neutral-200 focus:outline-none placeholder-neutral-600 font-mono"
            />
            <button
              type="submit"
              disabled={!cmdInput.trim() || isRunning}
              className={`px-2 py-0.5 rounded text-[11px] font-mono transition flex items-center gap-1 ${
                cmdInput.trim()
                  ? "bg-accent/80 hover:bg-accent text-white"
                  : "bg-neutral-800 text-neutral-600 cursor-not-allowed"
              }`}
            >
              <Play className="w-3 h-3" />
              <span>Run</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
