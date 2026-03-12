/**
 * API client for Zalo Mini App — same backend, auth via Zalo OAuth token.
 */
const API = "__API_URL__"; // Replaced at build time

let _token = "";

export function setToken(token: string) { _token = token; }

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(_token ? { Authorization: `Bearer ${_token}` } : {}),
      ...opts.headers,
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  // Auth — exchange Zalo OAuth code for JWT
  zaloLogin: (code: string) =>
    request<{ access_token: string }>("/auth/zalo", { method: "POST", body: JSON.stringify({ code }) }),
  // Tasks
  listTasks: (status = "all") =>
    request<Array<{ id: string; title: string; status: string; priority: string; due_date: string | null }>>(`/tasks/?status=${status}`),
  createTask: (title: string, priority = "medium") =>
    request<{ id: string }>("/tasks/", { method: "POST", body: JSON.stringify({ title, priority }) }),
  // Calendar
  listEvents: () =>
    request<Array<{ id: string; title: string; start_time: string; location: string }>>("/calendar/"),
  // Notifications
  notifications: () =>
    request<Array<{ id: string; type: string; content: string; read: boolean; created_at: string }>>("/notifications"),
  markRead: (id: string) =>
    request<{ ok: boolean }>(`/notifications/${id}/read`, { method: "PATCH" }),
};
