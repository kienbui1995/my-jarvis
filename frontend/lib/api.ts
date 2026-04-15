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
  // Feedback
  submitFeedback: (messageId: string, rating: string) => request<{ ok: boolean }>("/feedback", { method: "POST", body: JSON.stringify({ message_id: messageId, rating }) }),
  // Triggers
  listTriggers: () => request<Array<{ id: string; trigger_type: string; config: Record<string, unknown>; enabled: boolean }>>("/triggers/"),
  createTrigger: (trigger_type: string, config: Record<string, unknown> = {}) => request<{ id: string }>("/triggers/", { method: "POST", body: JSON.stringify({ trigger_type, config }) }),
  updateTrigger: (id: string, data: { config?: Record<string, unknown>; enabled?: boolean }) => request<{ ok: boolean }>(`/triggers/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  // Analytics (V5)
  weeklyDigest: () => request<{ messages: number; tools_used: number; cost: number; top_tools: Array<{ name: string; count: number }> }>("/analytics/digest"),
  // Memories
  listMemories: (type = "", limit = 20) => request<{ memories: Array<{ id: string; type: string; content: string; importance: number; metadata: Record<string, unknown> | null; created_at: string }>; total: number }>(`/memories/?memory_type=${type}&limit=${limit}`),
  searchMemories: (q: string) => request<{ memories: Array<{ id: string; type: string; content: string; importance: number; metadata: Record<string, unknown> | null; created_at: string }> }>(`/memories/search?q=${encodeURIComponent(q)}`),
  deleteMemory: (id: string) => request<{ deleted: boolean }>(`/memories/${id}`, { method: "DELETE" }),
  // MCP Gateway
  mcpRegistry: () => request<Array<{ id: string; name: string; description: string; icon: string; category: string; required_fields: string[] }>>("/mcp/registry"),
  mcpServers: () => request<Array<{ id: string; name: string; transport: string; config: Record<string, unknown>; enabled: boolean; curated_id: string | null }>>("/mcp/"),
  mcpConnect: (curatedId: string, apiKey: string) => request<{ id: string; name: string }>(`/mcp/connect/${curatedId}`, { method: "POST", body: JSON.stringify({ api_key: apiKey }) }),
  mcpAddCustom: (name: string, transport: string, config: Record<string, unknown>) => request<{ id: string }>("/mcp/custom", { method: "POST", body: JSON.stringify({ name, transport, config }) }),
  mcpToggle: (id: string, enabled: boolean) => request<{ ok: boolean }>(`/mcp/${id}?enabled=${enabled}`, { method: "PATCH" }),
  mcpDelete: (id: string) => request<{ ok: boolean }>(`/mcp/${id}`, { method: "DELETE" }),
  mcpTools: (id: string) => request<{ tools: Array<{ name: string; description: string }> }>(`/mcp/${id}/tools`),
  mcpHealth: (id: string) => request<{ status: string; tools_count?: number; error?: string }>(`/mcp/${id}/health`),
};

  // V9: Finance
  financeDashboard: () => request<{ month_total: number; by_category: Record<string, number>; subscriptions_monthly: number }>("/finance/dashboard"),
  listBills: () => request<{ data: Array<{ id: string; name: string; amount: number; due_day: number; category: string; enabled: boolean }> }>("/finance/bills"),
  createBill: (data: { name: string; amount?: number; due_day: number; category?: string }) => request<{ id: string }>("/finance/bills", { method: "POST", body: JSON.stringify(data) }),
  deleteBill: (id: string) => request<{ ok: boolean }>(`/finance/bills/${id}`, { method: "DELETE" }),
  listSubs: () => request<{ data: Array<{ id: string; name: string; amount: number; frequency: string; category: string; active: boolean }> }>("/finance/subscriptions"),
  createSub: (data: { name: string; amount: number; frequency?: string }) => request<{ id: string }>("/finance/subscriptions", { method: "POST", body: JSON.stringify(data) }),
  deleteSub: (id: string) => request<{ ok: boolean }>(`/finance/subscriptions/${id}`, { method: "DELETE" }),
  // V9: Contacts
  listContacts: (relationship?: string) => request<{ data: Array<{ id: string; name: string; phone?: string; email?: string; relationship?: string; birthday?: string; company?: string }> }>(`/contacts/?${relationship ? `relationship=${relationship}` : ""}`),
  createContact: (data: Record<string, unknown>) => request<{ id: string }>("/contacts/", { method: "POST", body: JSON.stringify(data) }),
  deleteContact: (id: string) => request<{ ok: boolean }>(`/contacts/${id}`, { method: "DELETE" }),
  // V9: Documents
  listDocs: (doc_type?: string) => request<{ data: Array<{ id: string; name: string; doc_type: string; doc_number?: string; expiry_date?: string }> }>(`/documents/?${doc_type ? `doc_type=${doc_type}` : ""}`),
  createDoc: (data: Record<string, unknown>) => request<{ id: string }>("/documents/", { method: "POST", body: JSON.stringify(data) }),
  deleteDoc: (id: string) => request<{ ok: boolean }>(`/documents/${id}`, { method: "DELETE" }),
  // V9: Shopping
  listShoppingLists: () => request<{ data: Array<{ id: string; name: string; completed: boolean }> }>("/shopping/"),
  createShoppingList: (name: string) => request<{ id: string }>("/shopping/", { method: "POST", body: JSON.stringify({ name }) }),
  getShoppingItems: (listId: string) => request<Array<{ id: string; name: string; quantity: number; unit?: string; checked: boolean }>>(`/shopping/${listId}/items`),
  addShoppingItem: (listId: string, name: string, quantity?: number) => request<{ id: string }>(`/shopping/${listId}/items`, { method: "POST", body: JSON.stringify({ name, quantity }) }),
  toggleShoppingItem: (listId: string, itemId: string) => request<{ checked: boolean }>(`/shopping/${listId}/items/${itemId}`, { method: "PATCH" }),
  // V10: Integrations
  listIntegrations: () => request<{ integrations: Array<{ id: string; name: string; connected: boolean }> }>("/integrations/"),
  connectIntegration: (id: string, token: string) => request<{ ok: boolean }>("/integrations/connect", { method: "POST", body: JSON.stringify({ integration_id: id, token }) }),
  disconnectIntegration: (id: string) => request<{ ok: boolean }>(`/integrations/disconnect/${id}`, { method: "POST" }),
  // V11: Health
  listHealthLogs: (metric?: string) => request<{ data: Array<{ id: string; log_date: string; metric: string; value: number; unit: string }> }>(`/health/logs?${metric ? `metric=${metric}` : ""}`),
  createHealthLog: (metric: string, value: number) => request<{ id: string }>("/health/logs", { method: "POST", body: JSON.stringify({ metric, value }) }),
  listMeds: () => request<{ data: Array<{ id: string; name: string; dosage?: string; frequency: string; active: boolean }> }>("/health/medications"),
  listBooks: () => request<{ data: Array<{ id: string; title: string; author?: string; status: string; rating?: number }> }>("/health/books"),
  // V12: Dashboard
  lifeOverview: () => request<{ week: { tasks_completed: number; spending: number; mood_avg: number | null; active_goals: number } }>("/dashboard/overview"),
  listGoals: () => request<{ data: Array<{ id: string; title: string; target_value?: number; current_value: number; status: string; deadline?: string }> }>("/dashboard/goals"),
  createGoal: (title: string, target_value?: number, deadline?: string) => request<{ id: string }>("/dashboard/goals", { method: "POST", body: JSON.stringify({ title, target_value, deadline }) }),
  updateGoal: (id: string, data: Record<string, unknown>) => request<{ ok: boolean }>(`/dashboard/goals/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
