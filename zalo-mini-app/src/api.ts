/**
 * API client for Zalo Mini App — backend via HTTP, auth via Zalo OAuth.
 */
const API = "__API_URL__"; // Replaced at build time with actual API URL

let _token = "";
let _refreshToken = "";

export function setToken(token: string, refresh?: string) {
  _token = token;
  if (refresh) _refreshToken = refresh;
}

export function getToken() { return _token; }

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(_token ? { Authorization: `Bearer ${_token}` } : {}),
      ...opts.headers,
    },
  });
  if (res.status === 401 && _refreshToken) {
    // Try refresh
    const r = await fetch(`${API}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: _refreshToken }),
    });
    if (r.ok) {
      const data = await r.json();
      setToken(data.access_token, data.refresh_token);
      return request<T>(path, opts);
    }
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  // Auth
  zaloLogin: (code: string) =>
    request<{ access_token: string; refresh_token: string }>(
      "/auth/zalo-miniapp", { method: "POST", body: JSON.stringify({ code }) }
    ),
  // Chat (HTTP, no WS)
  chat: (content: string) =>
    request<{ response: string; conversation_id: string }>(
      "/chat", { method: "POST", body: JSON.stringify({ content }) }
    ),
  // Voice
  transcribe: async (blob: Blob): Promise<string> => {
    const form = new FormData();
    form.append("audio", blob, "recording.webm");
    const res = await fetch(`${API}/voice/transcribe`, {
      method: "POST",
      headers: { Authorization: `Bearer ${_token}` },
      body: form,
    });
    if (!res.ok) throw new Error("Transcribe failed");
    const data = await res.json();
    return data.text || "";
  },
  speakUrl: (text: string) =>
    `${API}/voice/speak?text=${encodeURIComponent(text.slice(0, 2000))}&voice=vi-VN`,
  // Tasks
  listTasks: (status = "all") =>
    request<Array<{ id: string; title: string; status: string; priority: string; due_date: string | null }>>(
      `/tasks/?status=${status}`
    ),
  createTask: (title: string, priority = "medium") =>
    request<{ id: string }>("/tasks/", { method: "POST", body: JSON.stringify({ title, priority }) }),
  updateTask: (id: string, data: Record<string, string>) =>
    request<{ ok: boolean }>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  // Calendar
  listEvents: () =>
    request<Array<{ id: string; title: string; start_time: string; location: string }>>("/calendar/"),
  // Notifications
  notifications: () =>
    request<Array<{ id: string; type: string; content: string; read: boolean; created_at: string }>>(
      "/notifications"
    ),
  markRead: (id: string) =>
    request<{ ok: boolean }>(`/notifications/${id}/read`, { method: "PATCH" }),
};
