"use client";

import React, { useState } from "react";
import {
  Folder,
  FolderOpen,
  FolderPlus,
  FileCode,
  Plus,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Layers,
  Globe,
  FolderGit2,
  FolderCheck,
} from "lucide-react";
import { FileNode } from "@/lib/api";

interface FileTreeProps {
  tree: FileNode[];
  activeFile?: string;
  onSelectFile: (filePath: string) => void;
  onDeselectFile?: () => void;
  onRefresh: () => void;
  onCreateFile: (fileName: string) => void;
  onNewProject?: (projectPath: string) => void;
  availableWorkspaces?: { name: string; path: string; abs_path: string }[];
  currentWorkspace?: string;
}

export const FileTree: React.FC<FileTreeProps> = ({
  tree,
  activeFile,
  onSelectFile,
  onDeselectFile,
  onRefresh,
  onCreateFile,
  onNewProject,
  availableWorkspaces = [],
  currentWorkspace = "./workspace",
}) => {
  const [openFolders, setOpenFolders] = useState<Record<string, boolean>>({});
  const [isCreating, setIsCreating] = useState(false);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [newProjectName, setNewProjectName] = useState("");

  const toggleFolder = (path: string) => {
    setOpenFolders((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const handleClearSelection = () => {
    if (onDeselectFile) {
      onDeselectFile();
    } else {
      onSelectFile("");
    }
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFileName.trim()) {
      onCreateFile(newFileName.trim());
      setNewFileName("");
      setIsCreating(false);
    }
  };

  const handleCreateProjectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newProjectName.trim() && onNewProject) {
      const clean = newProjectName.trim().startsWith("./") || newProjectName.trim().includes(":") || newProjectName.trim().startsWith("/")
        ? newProjectName.trim()
        : `./${newProjectName.trim()}`;
      onNewProject(clean);
      setNewProjectName("");
      setIsCreatingProject(false);
    }
  };

  const handleQuickSwitch = (targetPath: string) => {
    if (onNewProject) {
      onNewProject(targetPath);
      setIsCreatingProject(false);
    }
  };

  const renderNode = (node: FileNode, level: number = 0) => {
    const isFolder = node.is_dir;
    const isOpen = !!openFolders[node.path];
    const isSelected = activeFile === node.path;

    return (
      <div key={node.path} className="select-none text-xs">
        <div
          onClick={(e) => {
            e.stopPropagation();
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
    <div
      onClick={handleClearSelection}
      className="flex flex-col h-full bg-[#181818] border-r border-neutral-800 text-neutral-300"
    >
      {/* Header */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex items-center justify-between px-3 py-2.5 bg-[#141414] border-b border-neutral-800 text-xs"
      >
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-neutral-400" />
          <span className="font-semibold text-neutral-400 text-[11px] tracking-wider uppercase">
            Explorer
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setIsCreatingProject(!isCreatingProject);
              setIsCreating(false);
            }}
            className={`flex items-center gap-1 px-1.5 py-1 rounded transition text-[11px] ${
              isCreatingProject ? "bg-accent text-white" : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
            }`}
            title="Switch / Pick Folder or Create New Project"
          >
            <FolderPlus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Pick Folder</span>
          </button>
          <button
            onClick={() => {
              setIsCreating(!isCreating);
              setIsCreatingProject(false);
            }}
            className={`p-1 rounded transition ${
              isCreating ? "bg-accent text-white" : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
            }`}
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

      {/* Target Workspace Banner / Project Switcher Button */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="px-3 py-2 bg-[#121212] border-b border-neutral-800/80 flex items-center justify-between text-xs"
      >
        <div className="flex items-center gap-2 min-w-0">
          <FolderGit2 className="w-4 h-4 text-accent shrink-0" />
          <div className="min-w-0">
            <div className="text-[10px] text-neutral-400 font-medium uppercase tracking-wider">
              Target Folder
            </div>
            <div
              className="font-mono text-xs text-neutral-200 font-semibold truncate max-w-[170px]"
              title={currentWorkspace}
            >
              {currentWorkspace ? currentWorkspace.split("/").pop() || currentWorkspace : "./workspace"}
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsCreatingProject(!isCreatingProject)}
          className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition ${
            isCreatingProject
              ? "bg-accent text-white shadow-sm"
              : "bg-neutral-800 hover:bg-neutral-700 text-neutral-300"
          }`}
          title="Pick an existing project folder or create a new workspace"
        >
          <FolderPlus className="w-3 h-3" />
          <span>Pick Folder</span>
        </button>
      </div>

      {/* Deselect / Scope Indicator */}
      <div className="px-3 py-1.5 bg-[#141414] border-b border-neutral-800/60 flex items-center justify-between text-[11px] text-neutral-400 select-none">
        <span className="text-[10px] font-mono uppercase text-neutral-500">
          {activeFile ? "File Mode" : "Project Mode"}
        </span>
        {activeFile ? (
          <span className="text-[10px] text-blue-400 font-mono truncate max-w-[150px]">
            Target: {activeFile}
          </span>
        ) : (
          <span className="text-[10px] text-emerald-400 font-mono">
            Target: Entire Project
          </span>
        )}
      </div>

      {/* 1-Click Folder Switcher & New Project Panel */}
      {isCreatingProject && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="p-2.5 border-b border-neutral-800 bg-[#121212] flex flex-col gap-2 animate-fadeIn select-none"
        >
          <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
            Select Existing Folder:
          </span>

          {/* Quick Click Folder Chips */}
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
            {(availableWorkspaces || []).map((ws) => {
              const isCurrent = currentWorkspace === ws.path || currentWorkspace === ws.name;
              return (
                <button
                  key={ws.path}
                  onClick={() => handleQuickSwitch(ws.path)}
                  className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition ${
                    isCurrent
                      ? "bg-accent text-white font-medium shadow-sm"
                      : "bg-neutral-800 hover:bg-neutral-700 text-neutral-300"
                  }`}
                >
                  <FolderGit2 className="w-3 h-3 text-amber-400" />
                  <span>{ws.name}</span>
                  {isCurrent && <FolderCheck className="w-3 h-3 text-white ml-0.5" />}
                </button>
              );
            })}
          </div>

          {/* Custom Path / New Folder Input */}
          <form onSubmit={handleCreateProjectSubmit} className="flex flex-col gap-1 mt-1">
            <label className="text-[10px] text-neutral-500">Or enter custom / new folder path:</label>
            <input
              type="text"
              placeholder="./my_app or C:/Projects/App"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              autoFocus
              className="w-full bg-neutral-950 border border-neutral-700 focus:border-accent rounded px-2 py-1 text-xs text-neutral-200 focus:outline-none"
            />
          </form>
        </div>
      )}

      {/* New File Inline Form */}
      {isCreating && (
        <form
          onClick={(e) => e.stopPropagation()}
          onSubmit={handleCreateSubmit}
          className="p-2 border-b border-neutral-800 bg-neutral-900 flex flex-col gap-1 animate-fadeIn"
        >
          <label className="text-[10px] text-neutral-400 font-medium">New File Name:</label>
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

      {/* Tree Content - Clicking empty space deselects file */}
      <div className="flex-1 overflow-y-auto py-1">
        {(!tree || tree.length === 0) ? (
          <div className="text-center text-neutral-600 py-8 text-xs">
            Empty folder workspace.<br />Click <b>Pick Folder</b> above to switch to another folder.
          </div>
        ) : (
          (tree || []).map((node) => renderNode(node, 0))
        )}
      </div>
    </div>
  );
};
