"use client";

import React, { useRef } from "react";
import Editor, { Monaco, OnMount } from "@monaco-editor/react";
import { Save, Code2 } from "lucide-react";

interface MonacoEditorProps {
  filePath?: string;
  code: string;
  onChange: (value: string) => void;
  onSave?: () => void;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
  filePath,
  code,
  onChange,
  onSave,
}) => {
  const editorRef = useRef<any>(null);

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
      case "html":
        return "html";
      case "css":
        return "css";
      case "sql":
        return "sql";
      case "md":
        return "markdown";
      case "go":
        return "go";
      case "rs":
        return "rust";
      case "yml":
      case "yaml":
        return "yaml";
      default:
        return "plaintext";
    }
  };

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Add Ctrl+S / Cmd+S shortcut for saving
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      if (onSave) {
        onSave();
      }
    });
  };

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] border-r border-neutral-800">
      {/* Editor Header / Tab Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#181818] border-b border-neutral-800 text-xs">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-accent" />
          <span className="font-mono text-neutral-300 font-medium">
            {filePath || "Untitled"}
          </span>
        </div>
        {onSave && (
          <button
            onClick={onSave}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded text-xs transition"
            title="Save file (Ctrl+S)"
          >
            <Save className="w-3.5 h-3.5 text-neutral-400" />
            <span>Save</span>
          </button>
        )}
      </div>

      {/* Monaco Container */}
      <div className="flex-1 w-full overflow-hidden">
        <Editor
          height="100%"
          language={getLanguage(filePath)}
          theme="vs-dark"
          value={code}
          onChange={(val) => onChange(val || "")}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: true, scale: 0.75 },
            fontSize: 13,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            tabSize: 4,
            automaticLayout: true,
            wordWrap: "on",
          }}
        />
      </div>
    </div>
  );
};
