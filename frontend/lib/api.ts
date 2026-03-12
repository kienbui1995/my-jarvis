const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, opts: RequestInit = {}, _retried = false): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...opts.headers },
  });

  // Auto-refresh on 401
  if (res.status === 401 && !_retried) {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        const r = await fetch(`${API}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (r.ok) {
          const data = await r.json();
          localStorage.setItem("token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          return request<T>(path, opts, true);
        }
      } catch {}
    }
    // Refresh failed — clear tokens
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    if (typeof window !== "undefined") window.location.href = "/login";
  }

  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) => request<{ access_token: string; refresh_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, name: string) => request<{ access_token: string; refresh_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, name }) }),
  googleAuth: (credential: string) => request<{ access_token: string; refresh_token: string }>("/auth/google", { method: "POST", body: JSON.stringify({ credential }) }),
  // User
  me: () => request<{ id: string; name: string; email: string; tier: string; timezone: string }>("/users/me"),
  updateProfile: (data: { name?: string; timezone?: string; preferences?: Record<string, unknown> }) => request<{ ok: boolean }>("/users/me", { method: "PATCH", body: JSON.stringify(data) }),
  // Connections
  connections: () => request<{ connections: Array<{ channel: string; connected: boolean; bot_username?: string; oa_id?: string }> }>("/users/me/connections"),
  createLinkCode: () => request<{ code: string; expires_in: number }>("/users/me/connections/link", { method: "POST" }),
  unlinkChannel: (channel: string) => request<{ ok: boolean }>("/users/me/connections/unlink", { method: "POST", body: JSON.stringify({ channel }) }),
  // Conversations
  listConversations: () => request<Array<{ id: string; channel: string; summary: string | null; started_at: string; message_count: number; rolling_summary?: string; total_turns?: number }>>("/conversations/"),
  createConversation: () => request<{ id: string }>("/conversations/", { method: "POST" }),
  getMessages: (convId: string, limit = 50) => request<Array<{ id: string; role: string; content: string; created_at: string }>>(`/conversations/${convId}/messages?limit=${limit}`),
  // Tasks
  listTasks: (status = "all") => request<Array<{ id: string; title: string; status: string; priority: string; due_date: string | null }>>(`/tasks/?status=${status}`),
  createTask: (title: string, priority = "medium", due_date?: string) => request<{ id: string; title: string }>("/tasks/", { method: "POST", body: JSON.stringify({ title, priority, due_date }) }),
  updateTask: (id: string, data: { status?: string; title?: string; priority?: string; due_date?: string | null }) => request<{ ok: boolean }>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTask: (id: string) => request<{ ok: boolean }>(`/tasks/${id}`, { method: "DELETE" }),
  // Calendar
  listEvents: () => request<Array<{ id: string; title: string; start_time: string; location: string }>>("/calendar/"),
  createEvent: (title: string, start_time: string, end_time?: string, location?: string) => request<{ id: string }>("/calendar/", { method: "POST", body: JSON.stringify({ title, start_time, end_time, location }) }),
  // Analytics
  usage: () => request<{ messages_today: number; tokens_today: number; cost_today: number }>("/analytics/usage"),
  weekly: () => request<Array<{ date: string; messages: number; cost: number }>>("/analytics/weekly"),
  // Proactive settings
  proactiveSettings: () => request<Array<{ id: string; trigger_type: string; schedule: string; enabled: boolean }>>("/settings/proactive"),
  toggleProactive: (id: string, enabled: boolean) => request<{ ok: boolean }>(`/settings/proactive/${id}`, { method: "PATCH", body: JSON.stringify({ enabled }) }),
  // Notifications
  notifications: (unread_only = false) => request<Array<{ id: string; type: string; content: string; read: boolean; created_at: string }>>(`/notifications?unread_only=${unread_only}`),
  markRead: (id: string) => request<{ ok: boolean }>(`/notifications/${id}/read`, { method: "PATCH" }),
  // V3: Preferences
  getPreferences: () => request<{ tone: string; verbosity: string; language: string; interests: string[]; custom_rules: string[] }>("/settings/preferences"),
  updatePreferences: (data: Record<string, unknown>) => request<{ ok: boolean }>("/settings/preferences", { method: "PATCH", body: JSON.stringify(data) }),
  // V3: Tool Permissions
  getToolPermissions: () => request<Array<{ tool_name: string; enabled: boolean }>>("/settings/tools"),
  updateToolPermission: (name: string, enabled: boolean) => request<{ ok: boolean }>(`/settings/tools/${name}`, { method: "PATCH", body: JSON.stringify({ enabled }) }),
  // V3: Audit
  getAuditLogs: (params?: { conversation_id?: string; event_type?: string }) => {
    const q = new URLSearchParams();
    if (params?.conversation_id) q.set("conversation_id", params.conversation_id);
    if (params?.event_type) q.set("event_type", params.event_type);
    return request<Array<{ id: string; event_type: string; node: string; tool_name: string | null; model_used: string | null; duration_ms: number; cost: number; timestamp: string; error: string | null }>>(`/audit?${q}`);
  },
};
