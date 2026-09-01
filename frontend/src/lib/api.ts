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
  description?: string;
  requires_api_key?: boolean;
  api_style?: "openai" | "anthropic";
}

export interface SyncProviderParams {
  provider: string;
  api_key?: string;
  base_url?: string;
}

export interface SyncProviderResponse {
  status: string;
  provider: string;
  total_models: number;
  models: string[];
}

export interface AgentSSEEvent {
  type: "thought" | "tool_call" | "tool_result" | "file_modified" | "warning" | "message" | "audit" | "error" | "done";
  content?: string;
  agent_role?: "architect" | "frontend" | "backend" | "auditor";
  agent_name?: string;
  audit_status?: "pending" | "passed" | "rejected";
  audit_cycle?: number;
  audit_feedback?: string;
  tool?: string;
  args?: Record<string, any>;
  result?: any;
  path?: string;
  diff?: string;
}

export const DEFAULT_PROVIDERS: ModelProvider[] = [
  {
    id: "9router",
    name: "9Router (Auto-Detect Combos)",
    default_model: "ag/gemini-3.7-flash-high",
    models: [
      "all",
      "ag/gemini-3.7-flash-high",
      "ag/gemini-3.7-flash-thinking",
      "ag/gemini-3.7-flash",
      "ag/gemini-3.5-flash-lite",
      "ag/gemini-3.1-pro-preview",
      "ag/gemini-2.5-pro",
      "ag/gemini-2.5-flash",
      "ag/gemini-2.5-flash-lite",
      "ag/claude-opus-4-1",
      "ag/claude-sonnet-4-5",
      "ag/claude-sonnet-4-6",
      "ag/claude-opus-4-6-thinking",
      "ag/claude-3-7-sonnet",
      "ag/claude-3-5-sonnet",
      "ag/claude-3-5-haiku",
      "gemini/gemini-3.7-flash-high",
      "gemini/gemini-3.7-flash",
      "gemini/gemini-3.5-flash-lite",
      "gemini/gemini-3.1-pro-preview",
      "gemini/gemini-2.5-pro",
      "gemini/gemini-2.5-flash",
      "gemini/gemini-2.5-flash-lite",
      "gemini/gemma-4-31b-it",
      "gemini/gemma-4-26b-a4b-it",
      "nvidia/deepseek-ai/deepseek-v3",
      "nvidia/deepseek-ai/deepseek-r1",
      "openai/gpt-4o",
      "openai/gpt-4o-mini",
      "openai/gpt-5",
      "openai/o1",
      "openai/o3-mini",
    ],
    requires_api_key: false,
    description: "Local AI Gateway with auto-detected combos (Claude, Gemini, DeepSeek, GPT, Ollama).",
    api_style: "openai",
  },
  {
    id: "openai",
    name: "OpenAI",
    default_model: "gpt-4o",
    models: [
      "gpt-4o",
      "gpt-4o-mini",
      "gpt-4-turbo",
      "gpt-4.1",
      "gpt-4.1-mini",
      "gpt-4.1-nano",
      "gpt-5",
      "gpt-5-mini",
      "gpt-5-nano",
      "o1",
      "o1-mini",
      "o3-mini",
    ],
    requires_api_key: true,
    description: "OpenAI GPT-4o, GPT-5, o1/o3 reasoning models.",
    api_style: "openai",
  },
  {
    id: "gemini",
    name: "Google Gemini",
    default_model: "gemini-3.7-flash",
    models: [
      "gemini-3.7-flash",
      "gemini-3.7-flash-high",
      "gemini-3.7-flash-thinking",
      "gemini-3.5-flash-lite",
      "gemini-3.1-pro-preview",
      "gemini-3-pro-image-preview",
      "gemini-3.1-flash-image-preview",
      "gemini-3.1-flash-lite-image-preview",
      "gemini-2.5-pro",
      "gemini-2.5-flash",
      "gemini-2.5-flash-lite",
      "gemma-4-31b-it",
      "gemma-4-26b-a4b-it",
    ],
    requires_api_key: true,
    description: "Google Gemini 3.7 / 3.5 / 2.5 / Gemma 4 family via OpenAI-compatible endpoint.",
    api_style: "openai",
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    default_model: "claude-3-7-sonnet-latest",
    models: [
      "claude-opus-4-1-20250805",
      "claude-sonnet-4-5-20250929",
      "claude-3-7-sonnet-latest",
      "claude-3-5-sonnet-latest",
      "claude-3-5-haiku-latest",
    ],
    requires_api_key: true,
    description: "Anthropic Claude 4.x / 3.x with native API + extended thinking.",
    api_style: "anthropic",
  },
  {
    id: "ollama",
    name: "Ollama (Local)",
    default_model: "deepseek-r1:latest",
    models: [
      "llama3.3:latest",
      "llama3.2:latest",
      "llama3.1:70b",
      "qwen2.5-coder:32b",
      "qwen2.5:72b",
      "deepseek-r1:latest",
      "deepseek-coder-v2:latest",
      "codellama:34b",
      "mistral:latest",
    ],
    requires_api_key: false,
    description: "Ollama local models (Llama, Qwen, DeepSeek, Mistral, Gemma, Phi).",
    api_style: "openai",
  },
  {
    id: "groq",
    name: "Groq",
    default_model: "llama-3.3-70b-versatile",
    models: [
      "llama-3.3-70b-versatile",
      "llama-3.1-8b-instant",
      "llama-3.2-90b-vision-preview",
      "mixtral-8x7b-32768",
      "deepseek-r1-distill-llama-70b",
      "qwen-2.5-32b",
    ],
    requires_api_key: true,
    description: "Groq ultra-fast inference (LPU) for Llama, Mixtral, Gemma, Qwen, DeepSeek.",
    api_style: "openai",
  },
  {
    id: "mistral",
    name: "Mistral AI",
    default_model: "mistral-large-latest",
    models: [
      "mistral-large-latest",
      "mistral-medium-latest",
      "mistral-small-latest",
      "codestral-latest",
      "pixtral-large-latest",
    ],
    requires_api_key: true,
    description: "Mistral Large, Medium, Small, Codestral, Pixtral — all OpenAI-compatible.",
    api_style: "openai",
  },
  {
    id: "cohere",
    name: "Cohere",
    default_model: "command-r-plus",
    models: [
      "command-r-plus",
      "command-r",
      "command",
      "c4ai-aya-expanse-32b",
    ],
    requires_api_key: true,
    description: "Cohere Command R+ / R / Aya Expanse via OpenAI-compatible endpoint.",
    api_style: "openai",
  },
  {
    id: "together",
    name: "Together AI",
    default_model: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    models: [
      "meta-llama/Llama-3.3-70B-Instruct-Turbo",
      "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
      "Qwen/Qwen2.5-Coder-32B-Instruct",
      "deepseek-ai/DeepSeek-R1",
      "deepseek-ai/DeepSeek-V3",
    ],
    requires_api_key: true,
    description: "Together AI — open models (Llama, Qwen, DeepSeek, Mixtral, Gemma) at low cost.",
    api_style: "openai",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    default_model: "deepseek-chat",
    models: [
      "deepseek-chat",
      "deepseek-reasoner",
      "deepseek-coder",
    ],
    requires_api_key: true,
    description: "DeepSeek V3 (chat) and R1 (reasoner) — OpenAI-compatible API.",
    api_style: "openai",
  },
  {
    id: "openrouter",
    name: "OpenRouter (All Models)",
    default_model: "anthropic/claude-3.7-sonnet",
    models: [
      "anthropic/claude-3.7-sonnet",
      "anthropic/claude-3.5-sonnet",
      "openai/gpt-4o",
      "google/gemini-3.7-flash",
      "google/gemini-2.5-pro",
      "google/gemini-2.5-flash",
      "meta-llama/llama-3.3-70b-instruct",
      "deepseek/deepseek-r1",
    ],
    requires_api_key: true,
    description: "OpenRouter — 100+ models from all major providers through one API key.",
    api_style: "openai",
  },
];

export async function fetchModels(apiKey?: string, baseUrl?: string): Promise<ModelProvider[]> {
  try {
    const params = new URLSearchParams();
    if (apiKey) params.set("api_key", apiKey);
    if (baseUrl) params.set("base_url", baseUrl);
    const queryString = params.toString();
    const url = queryString ? `${API_BASE}/models?${queryString}` : `${API_BASE}/models`;
    const res = await fetch(url);
    if (!res.ok) return DEFAULT_PROVIDERS;
    const data = await res.json();
    return data.providers && data.providers.length > 0 ? data.providers : DEFAULT_PROVIDERS;
  } catch (err) {
    console.error("Failed to fetch models, using fallback providers", err);
    return DEFAULT_PROVIDERS;
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

/**
 * Generic provider sync — works for every provider in the catalog
 * (9Router, OpenAI, Gemini, Anthropic, Ollama, Groq, Mistral, Cohere,
 * Together, DeepSeek, OpenRouter).
 */
export async function syncProviderModels(params: SyncProviderParams): Promise<SyncProviderResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/models/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error(`Failed to sync models for ${params.provider}`, err);
    return null;
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
    mode?: "solo" | "team";
    provider: string;
    model?: string;
    api_key?: string;
    base_url?: string;
    max_iterations?: number;
    max_audit_cycles?: number;
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
