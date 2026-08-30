"use client";

import React, { useRef, useState } from "react";
import { DiffEditor, Monaco } from "@monaco-editor/react";
import { Check, X, Split, Layers } from "lucide-react";

interface InlineDiffProps {
  filePath?: string;
  originalCode: string;
  modifiedCode: string;
  onAccept: (newCode: string) => void;
  onReject: () => void;
}

export const MonacoInlineDiff: React.FC<InlineDiffProps> = ({
  filePath,
  originalCode,
  modifiedCode,
  onAccept,
  onReject,
}) => {
  const [renderSideBySide, setRenderSideBySide] = useState(true);
  const diffEditorRef = useRef<any>(null);

  const getLanguage = (path?: string): string => {
    if (!path) return "plaintext";
    const ext = path.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "py":
        return "python";
      case "js":
      case "jsx":
        return "javascript";
      case "ts":
      case "tsx":
        return "typescript";
      case "json":
        return "json";
      case "sql":
        return "sql";
      case "md":
        return "markdown";
      default:
        return "plaintext";
    }
  };

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    diffEditorRef.current = editor;
  };

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] border-r border-neutral-800">
      {/* Header Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#181818] border-b border-neutral-800 text-xs">
        <div className="flex items-center gap-3">
          <span className="font-mono text-neutral-300 font-semibold">
            Diff Review: {filePath || "Active File"}
          </span>
          <button
            onClick={() => setRenderSideBySide(!renderSideBySide)}
            className="flex items-center gap-1 text-neutral-400 hover:text-neutral-200 px-2 py-0.5 rounded bg-neutral-800 transition"
            title="Toggle Inline / Side-by-Side Diff"
          >
            {renderSideBySide ? <Layers className="w-3.5 h-3.5" /> : <Split className="w-3.5 h-3.5" />}
            <span>{renderSideBySide ? "Inline Mode" : "Side-by-Side"}</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAccept(modifiedCode)}
            className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium transition shadow-sm"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Accept Changes</span>
          </button>
          <button
            onClick={onReject}
            className="flex items-center gap-1.5 px-3 py-1 bg-rose-700 hover:bg-rose-600 text-white rounded font-medium transition shadow-sm"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject</span>
          </button>
        </div>
      </div>

      {/* Monaco Diff Container */}
      <div className="flex-1 w-full overflow-hidden">
        <DiffEditor
          height="100%"
          language={getLanguage(filePath)}
          theme="vs-dark"
          original={originalCode}
          modified={modifiedCode}
          onMount={handleEditorDidMount}
          options={{
            readOnly: true,
            renderSideBySide: renderSideBySide,
            fontSize: 13,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            diffWordWrap: "on",
          }}
        />
      </div>
    </div>
  );
};
