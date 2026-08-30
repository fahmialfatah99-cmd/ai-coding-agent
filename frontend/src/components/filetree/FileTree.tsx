"use client";

import React, { useState } from "react";
import {
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  Plus,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Layers,
} from "lucide-react";
import { FileNode } from "@/lib/api";

interface FileTreeProps {
  tree: FileNode[];
  activeFile?: string;
  onSelectFile: (filePath: string) => void;
  onRefresh: () => void;
  onCreateFile: (fileName: string) => void;
}

export const FileTree: React.FC<FileTreeProps> = ({
  tree,
  activeFile,
  onSelectFile,
  onRefresh,
  onCreateFile,
}) => {
  const [openFolders, setOpenFolders] = useState<Record<string, boolean>>({});
  const [isCreating, setIsCreating] = useState(false);
  const [newFileName, setNewFileName] = useState("");

  const toggleFolder = (path: string) => {
    setOpenFolders((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFileName.trim()) {
      onCreateFile(newFileName.trim());
      setNewFileName("");
      setIsCreating(false);
    }
  };

  const renderNode = (node: FileNode, level: number = 0) => {
    const isFolder = node.is_dir;
    const isOpen = !!openFolders[node.path];
    const isSelected = activeFile === node.path;

    return (
      <div key={node.path} className="select-none text-xs">
        <div
          onClick={() => {
            if (isFolder) {
              toggleFolder(node.path);
            } else {
              onSelectFile(node.path);
            }
          }}
          style={{ paddingLeft: `${level * 12 + 12}px` }}
          className={`flex items-center gap-1.5 py-1.5 pr-3 cursor-pointer rounded-sm transition ${
            isSelected
              ? "bg-accent/20 text-accent font-medium"
              : "text-neutral-300 hover:bg-neutral-800/60"
          }`}
        >
          {isFolder ? (
            <>
              {isOpen ? (
                <ChevronDown className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
              )}
              {isOpen ? (
                <FolderOpen className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              ) : (
                <Folder className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5 shrink-0" />
              <FileCode className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
            </>
          )}

          <span className="truncate">{node.name}</span>
        </div>

        {isFolder && isOpen && node.children && (
          <div>{node.children.map((child) => renderNode(child, level + 1))}</div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-[#181818] border-r border-neutral-800 text-neutral-300">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 bg-[#141414] border-b border-neutral-800 text-xs">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-neutral-400" />
          <span className="font-semibold text-neutral-400 text-[11px] tracking-wider uppercase">
            Explorer
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="p-1 rounded text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition"
            title="New File"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onRefresh}
            className="p-1 rounded text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition"
            title="Refresh Files"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* New File Inline Form */}
      {isCreating && (
        <form onSubmit={handleCreateSubmit} className="p-2 border-b border-neutral-800 bg-neutral-900">
          <input
            type="text"
            placeholder="filename.py / src/app.js"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            autoFocus
            className="w-full bg-neutral-950 border border-accent rounded px-2 py-1 text-xs text-neutral-200 focus:outline-none"
          />
        </form>
      )}

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto py-2">
        {tree.length === 0 ? (
          <div className="text-center text-neutral-600 py-8 text-xs">No files in workspace</div>
        ) : (
          tree.map((node) => renderNode(node, 0))
        )}
      </div>
    </div>
  );
};
