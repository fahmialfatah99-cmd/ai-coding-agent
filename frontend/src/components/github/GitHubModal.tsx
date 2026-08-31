"use client";

import React, { useState, useEffect } from "react";
import {
  Github,
  CheckCircle,
  AlertCircle,
  X,
  ExternalLink,
  Key,
  UploadCloud,
  Check,
  ShieldCheck,
  User,
  Mail,
  GitBranch,
} from "lucide-react";
import { configureGitHub, getGitHubStatus, executeSandboxCommand, GitHubConfigResponse } from "@/lib/api";

interface GitHubModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspacePath: string;
}

export const GitHubModal: React.FC<GitHubModalProps> = ({
  isOpen,
  onClose,
  workspacePath,
}) => {
  const [token, setToken] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [remoteUrl, setRemoteUrl] = useState("https://github.com/fahmialfatah99-cmd/ai-coding-agent.git");
  const [commitMessage, setCommitMessage] = useState("update code via AI Agent");
  const [branch, setBranch] = useState("main");
  const [isLoading, setIsLoading] = useState(false);
  const [statusResult, setStatusResult] = useState<GitHubConfigResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pushOutput, setPushOutput] = useState<string | null>(null);
  const [isPushing, setIsPushing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const savedToken = localStorage.getItem("ai_agent_github_token") || "";
      const savedUser = localStorage.getItem("ai_agent_github_user") || "";
      const savedEmail = localStorage.getItem("ai_agent_github_email") || "";
      const savedRemote = localStorage.getItem("ai_agent_github_remote") || "";

      if (savedToken) setToken(savedToken);
      if (savedUser) setUsername(savedUser);
      if (savedEmail) setEmail(savedEmail);
      if (savedRemote) setRemoteUrl(savedRemote);

      loadStatus();
    }
  }, [isOpen]);

  const loadStatus = async () => {
    const stat = await getGitHubStatus();
    if (stat.configured && stat.user_name) {
      setUsername(stat.user_name);
      setEmail(stat.user_email);
      if (stat.remote) {
        setRemoteUrl(stat.remote.split(" ")[0]);
      }
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setErrorMessage("Please enter a valid GitHub Personal Access Token (PAT).");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setPushOutput(null);

    try {
      const res = await configureGitHub({
        token: token.trim(),
        username: username.trim() || undefined,
        email: email.trim() || undefined,
        remote_url: remoteUrl.trim() || undefined,
        workspace_path: workspacePath,
      });

      setStatusResult(res);
      setUsername(res.username);
      setEmail(res.email);

      localStorage.setItem("ai_agent_github_token", token.trim());
      localStorage.setItem("ai_agent_github_user", res.username);
      localStorage.setItem("ai_agent_github_email", res.email);
      if (remoteUrl) localStorage.setItem("ai_agent_github_remote", remoteUrl.trim());
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to connect to GitHub");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDirectPush = async () => {
    setIsPushing(true);
    setPushOutput(null);
    setErrorMessage(null);

    try {
      // Execute git add, commit, and push
      await executeSandboxCommand(workspacePath, "git add .");
      const commitRes = await executeSandboxCommand(
        workspacePath,
        `git commit -m "${commitMessage || "update from AI Agent"}"`
      );
      const pushRes = await executeSandboxCommand(
        workspacePath,
        `git push origin ${branch || "main"}`
      );

      const combined = `${commitRes.stdout || ""}\n${pushRes.stdout || ""}\n${pushRes.stderr || ""}`;
      setPushOutput(combined.trim() || "Git Push finished successfully!");
    } catch (err: any) {
      setErrorMessage(`Push failed: ${err.message}`);
    } finally {
      setIsPushing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn select-none">
      <div className="bg-[#181818] border border-neutral-800 rounded-xl w-full max-w-xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#141414] border-b border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-neutral-900 border border-neutral-700 rounded-lg">
              <Github className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-neutral-100">GitHub Integration & Push Credentials</h2>
              <p className="text-[11px] text-neutral-400">Sambungkan akun GitHub agar AI Agent bisa langsung push kode</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Status Banner */}
          {statusResult ? (
            <div className="p-3 bg-emerald-950/60 border border-emerald-800/60 rounded-lg flex items-center justify-between text-emerald-300">
              <div className="flex items-center gap-2.5">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                <div>
                  <span className="font-semibold text-xs">Connected as @{statusResult.username}</span>
                  <p className="text-[10px] text-emerald-400/80">{statusResult.email}</p>
                </div>
              </div>
              <span className="text-[10px] bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded font-mono font-medium">
                Active
              </span>
            </div>
          ) : (
            <div className="p-3 bg-neutral-900 border border-neutral-800 rounded-lg flex items-start gap-2.5 text-neutral-300">
              <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-neutral-200">Gunakan Personal Access Token (PAT) dari GitHub</p>
                <p className="text-[11px] text-neutral-400 mt-0.5">
                  Token disimpan aman secara lokal dan digunakan saat AI menjalankan git commit & push otomatis.
                </p>
                <a
                  href="https://github.com/settings/tokens"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-400 hover:underline mt-1.5 font-medium"
                >
                  <span>Buat token di GitHub (Pilih scope &apos;repo&apos;)</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 bg-rose-950/60 border border-rose-800/60 rounded-lg flex items-center gap-2 text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span className="text-xs">{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleConnect} className="space-y-3">
            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                GitHub Personal Access Token (PAT):
              </label>
              <div className="relative flex items-center">
                <Key className="w-3.5 h-3.5 absolute left-3 text-neutral-500" />
                <input
                  type="password"
                  placeholder="ghp_... atau github_pat_..."
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full bg-[#121212] border border-neutral-700 rounded-lg pl-9 pr-3 py-2 text-xs text-neutral-200 focus:outline-none focus:border-accent"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-neutral-300 font-medium mb-1">Git User Name (Opsional):</label>
                <div className="relative flex items-center">
                  <User className="w-3.5 h-3.5 absolute left-3 text-neutral-500" />
                  <input
                    type="text"
                    placeholder="e.g. fahmialfatah99-cmd"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-[#121212] border border-neutral-700 rounded-lg pl-9 pr-3 py-2 text-xs text-neutral-200 focus:outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-neutral-300 font-medium mb-1">Git Email (Opsional):</label>
                <div className="relative flex items-center">
                  <Mail className="w-3.5 h-3.5 absolute left-3 text-neutral-500" />
                  <input
                    type="email"
                    placeholder="e.g. user@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-[#121212] border border-neutral-700 rounded-lg pl-9 pr-3 py-2 text-xs text-neutral-200 focus:outline-none focus:border-accent"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-neutral-300 font-medium mb-1">
                Remote Repository URL (origin):
              </label>
              <div className="relative flex items-center">
                <GitBranch className="w-3.5 h-3.5 absolute left-3 text-neutral-500" />
                <input
                  type="text"
                  placeholder="https://github.com/username/repository.git"
                  value={remoteUrl}
                  onChange={(e) => setRemoteUrl(e.target.value)}
                  className="w-full bg-[#121212] border border-neutral-700 rounded-lg pl-9 pr-3 py-2 text-xs text-neutral-200 focus:outline-none focus:border-accent font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !token.trim()}
              className={`w-full py-2 rounded-lg font-medium transition flex items-center justify-center gap-1.5 ${
                token.trim()
                  ? "bg-accent hover:bg-blue-600 text-white shadow-sm"
                  : "bg-neutral-800 text-neutral-500 cursor-not-allowed"
              }`}
            >
              {isLoading ? (
                <span>Menghubungkan ke GitHub API...</span>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Simpan & Sambungkan Kredensial GitHub</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Push Section */}
          <div className="pt-3 border-t border-neutral-800 space-y-2">
            <h3 className="font-semibold text-neutral-200 text-xs">Uji Coba Push Langsung:</h3>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Pesan commit..."
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                className="flex-1 bg-[#121212] border border-neutral-700 rounded-lg px-3 py-1.5 text-xs text-neutral-200 focus:outline-none focus:border-accent"
              />
              <button
                type="button"
                onClick={handleDirectPush}
                disabled={isPushing}
                className="px-4 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg font-medium transition flex items-center gap-1.5 text-xs shrink-0"
              >
                <UploadCloud className="w-3.5 h-3.5 text-blue-400" />
                <span>{isPushing ? "Pushing..." : "Push Sekarang"}</span>
              </button>
            </div>

            {pushOutput && (
              <div className="p-2.5 bg-black/60 border border-neutral-800 rounded-lg font-mono text-[11px] text-neutral-300 whitespace-pre-wrap max-h-28 overflow-y-auto">
                {pushOutput}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
