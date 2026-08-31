export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
  children?: FileNode[];
}

export interface ModelProvider {
  id: string;
  name: string;
  models: string[];
  default_model: string;
}

export interface AgentSSEEvent {
  type: "thought" | "tool_call" | "tool_result" | "file_modified" | "warning" | "message" | "error" | "done";
  content?: string;
  tool?: string;
  args?: Record<string, any>;
  result?: any;
  path?: string;
  diff?: string;
}

export async function fetchModels(apiKey?: string): Promise<ModelProvider[]> {
  try {
    const url = apiKey ? `${API_BASE}/models?api_key=${encodeURIComponent(apiKey)}` : `${API_BASE}/models`;
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    return data.providers || [];
  } catch (err) {
    console.error("Failed to fetch models", err);
    return [];
  }
}

export async function sync9RouterModels(apiKey?: string): Promise<string[]> {
  try {
    const url = apiKey ? `${API_BASE}/models/sync-9router?api_key=${encodeURIComponent(apiKey)}` : `${API_BASE}/models/sync-9router`;
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    return data.models || [];
  } catch (err) {
    console.error("Failed to sync 9router models", err);
    return [];
  }
}

export async function fetchWorkspaces(): Promise<{ name: string; path: string; abs_path: string }[]> {
  try {
    const res = await fetch(`${API_BASE}/files/workspaces`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.workspaces || [];
  } catch (err) {
    console.error("Failed to fetch workspaces", err);
    return [];
  }
}

export async function fetchFileTree(workspacePath: string = "./workspace"): Promise<FileNode[]> {
  try {
    const res = await fetch(`${API_BASE}/files?workspace_path=${encodeURIComponent(workspacePath)}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.tree || [];
  } catch (err) {
    console.error("Failed to fetch file tree", err);
    return [];
  }
}

export async function readFile(workspacePath: string, filePath: string): Promise<string> {
  const res = await fetch(`${API_BASE}/files/read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_path: workspacePath, file_path: filePath }),
  });
  if (!res.ok) throw new Error("Failed to read file");
  const data = await res.json();
  return data.content;
}

export async function writeFile(workspacePath: string, filePath: string, content: string): Promise<void> {
  const res = await fetch(`${API_BASE}/files/write`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_path: workspacePath, file_path: filePath, content }),
  });
  if (!res.ok) throw new Error("Failed to write file");
}

export async function executeSandboxCommand(workspacePath: string, command: string) {
  const res = await fetch(`${API_BASE}/sandbox/exec`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_path: workspacePath, command }),
  });
  if (!res.ok) throw new Error("Failed to execute command");
  return await res.json();
}

export async function streamAgentTask(
  params: {
    instruction: string;
    active_file?: string;
    file_content?: string;
    workspace_path: string;
    provider: string;
    model?: string;
    api_key?: string;
    base_url?: string;
  },
  onEvent: (event: AgentSSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Agent request failed: ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const chunk of lines) {
      const trimmed = chunk.trim();
      if (trimmed.startsWith("data:")) {
        try {
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          const parsed: AgentSSEEvent = JSON.parse(jsonStr);
          onEvent(parsed);
        } catch (e) {
          console.error("SSE parse error", e);
        }
      }
    }
  }
}

export interface GitHubConfigResponse {
  status: string;
  username: string;
  name: string;
  avatar_url: string;
  email: string;
  scopes: string;
}

export async function configureGitHub(params: {
  token: string;
  username?: string;
  email?: string;
  remote_url?: string;
  workspace_path?: string;
}): Promise<GitHubConfigResponse> {
  const res = await fetch(`${API_BASE}/sandbox/github-config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to configure GitHub token");
  }
  return res.json();
}

export async function getGitHubStatus(): Promise<{
  configured: boolean;
  user_name: string;
  user_email: string;
  remote: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/sandbox/github-status`);
    if (!res.ok) return { configured: false, user_name: "", user_email: "", remote: "" };
    return res.json();
  } catch {
    return { configured: false, user_name: "", user_email: "", remote: "" };
  }
}
