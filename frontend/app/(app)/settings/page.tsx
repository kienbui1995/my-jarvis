"use client";
import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/stores/auth";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { X, Plus, Shield, Sliders, Brain, Link2, Wrench, ClipboardList, Search, Trash2, Plug } from "lucide-react";

const tabs = [
  { label: "Hồ sơ", icon: null },
  { label: "Tùy chọn", icon: Sliders },
  { label: "Bộ nhớ", icon: Brain },
  { label: "Kết nối", icon: Link2 },
  { label: "MCP", icon: Plug },
  { label: "Tools", icon: Wrench },
  { label: "Audit", icon: ClipboardList },
] as const;

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!on)} className={`w-10 h-6 rounded-full transition-colors relative ${on ? "bg-[var(--brand-primary)]" : "bg-[var(--bg-tertiary)]"}`}>
      <span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${on ? "left-5" : "left-1"}`} />
    </button>
  );
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      className="bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded-[var(--radius-md)] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-focus)]">
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

const CHANNEL_LABELS: Record<string, string> = { telegram: "Telegram", zalo_oa: "Zalo OA", zalo_bot: "Zalo Bot" };

function ConnectionsTab() {
  const [conns, setConns] = useState<Array<{ channel: string; connected: boolean; bot_username?: string }>>([]);
  const [linkCode, setLinkCode] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { try { setConns((await api.connections()).connections); } catch {} setLoading(false); }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <p className="text-sm text-[var(--text-secondary)] py-4">Đang tải...</p>;
  return (
    <div className="space-y-3">
      <div className="p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
        <p className="text-sm text-[var(--text-secondary)] mb-2">Liên kết tài khoản chat:</p>
        {linkCode ? (
          <div><code className="text-2xl font-mono font-bold tracking-widest text-[var(--brand-primary)]">{linkCode}</code><span className="text-xs text-[var(--text-tertiary)] ml-2">5 phút</span></div>
        ) : <Button size="sm" onClick={async () => setLinkCode((await api.createLinkCode()).code)}>Tạo mã liên kết</Button>}
      </div>
      {conns.map(({ channel, connected }) => (
        <div key={channel} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${connected ? "bg-[var(--accent-green)]" : "bg-[var(--text-tertiary)]"}`} />
            <span>{CHANNEL_LABELS[channel] || channel}</span>
            {connected && <span className="text-xs text-[var(--accent-green)]">Đã kết nối</span>}
          </div>
          {connected && <Button size="sm" variant="ghost" onClick={() => { api.unlinkChannel(channel); load(); }}>Ngắt</Button>}
        </div>
      ))}
    </div>
  );
}

function PreferencesTab() {
  const [prefs, setPrefs] = useState({ tone: "friendly", verbosity: "concise", language: "vi", interests: [] as string[], custom_rules: [] as string[] });
  const [newInterest, setNewInterest] = useState("");
  const [newRule, setNewRule] = useState("");
  const [saving, setSaving] = useState(false);
  const [proactive, setProactive] = useState(true);
  const [morning, setMorning] = useState(true);
  const [deadline, setDeadline] = useState(true);

  useEffect(() => { api.getPreferences().then(setPrefs).catch(() => {}); }, []);

  const save = async () => {
    setSaving(true);
    try { await api.updatePreferences(prefs); } catch {}
    setSaving(false);
  };

  const addInterest = () => { if (newInterest.trim() && !prefs.interests.includes(newInterest.trim())) { setPrefs((p) => ({ ...p, interests: [...p.interests, newInterest.trim()] })); setNewInterest(""); } };
  const addRule = () => { if (newRule.trim()) { setPrefs((p) => ({ ...p, custom_rules: [...p.custom_rules, newRule.trim()] })); setNewRule(""); } };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm text-[var(--text-secondary)] mb-1 block">Phong cách trả lời</label>
          <Select value={prefs.tone} onChange={(v) => setPrefs((p) => ({ ...p, tone: v }))} options={[
            { value: "friendly", label: "Thân thiện" }, { value: "formal", label: "Trang trọng" }, { value: "casual", label: "Thoải mái" },
          ]} />
        </div>
        <div>
          <label className="text-sm text-[var(--text-secondary)] mb-1 block">Độ chi tiết</label>
          <Select value={prefs.verbosity} onChange={(v) => setPrefs((p) => ({ ...p, verbosity: v }))} options={[
            { value: "concise", label: "Ngắn gọn" }, { value: "balanced", label: "Cân bằng" }, { value: "detailed", label: "Chi tiết" },
          ]} />
        </div>
        <div>
          <label className="text-sm text-[var(--text-secondary)] mb-1 block">Ngôn ngữ AI</label>
          <Select value={prefs.language} onChange={(v) => setPrefs((p) => ({ ...p, language: v }))} options={[
            { value: "vi", label: "Tiếng Việt" }, { value: "en", label: "English" }, { value: "mixed", label: "Hỗn hợp" },
          ]} />
        </div>
      </div>

      {/* Interests */}
      <div>
        <label className="text-sm text-[var(--text-secondary)] mb-1 block">Sở thích & lĩnh vực quan tâm</label>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {prefs.interests.map((t) => (
            <Badge key={t} color="blue" className="gap-1">
              {t} <button onClick={() => setPrefs((p) => ({ ...p, interests: p.interests.filter((i) => i !== t) }))}><X size={10} /></button>
            </Badge>
          ))}
        </div>
        <div className="flex gap-2">
          <Input value={newInterest} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewInterest(e.target.value)} placeholder="VD: tech, finance..." className="flex-1" onKeyDown={(e: React.KeyboardEvent) => e.key === "Enter" && addInterest()} />
          <Button size="sm" variant="secondary" onClick={addInterest}><Plus size={14} /></Button>
        </div>
      </div>

      {/* Custom rules */}
      <div>
        <label className="text-sm text-[var(--text-secondary)] mb-1 block">Quy tắc riêng cho AI</label>
        <div className="space-y-1.5 mb-2">
          {prefs.custom_rules.map((r, i) => (
            <div key={i} className="flex items-center gap-2 text-sm bg-[var(--bg-secondary)] px-3 py-1.5 rounded-[var(--radius-md)]">
              <span className="flex-1">{r}</span>
              <button onClick={() => setPrefs((p) => ({ ...p, custom_rules: p.custom_rules.filter((_, j) => j !== i) }))} className="text-[var(--text-tertiary)] hover:text-[var(--accent-red)]"><X size={12} /></button>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <Input value={newRule} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewRule(e.target.value)} placeholder='VD: "Luôn dùng emoji"' className="flex-1" onKeyDown={(e: React.KeyboardEvent) => e.key === "Enter" && addRule()} />
          <Button size="sm" variant="secondary" onClick={addRule}><Plus size={14} /></Button>
        </div>
      </div>

      {/* Proactive toggles */}
      <div className="border-t border-[var(--border-default)] pt-4 space-y-3">
        <p className="text-sm font-medium">Tin nhắn chủ động</p>
        {[
          { label: "Tin nhắn chủ động", state: proactive, set: setProactive },
          { label: "Tóm tắt buổi sáng", state: morning, set: setMorning },
          { label: "Nhắc deadline", state: deadline, set: setDeadline },
        ].map(({ label, state, set }) => (
          <div key={label} className="flex items-center justify-between"><span className="text-sm">{label}</span><Toggle on={state} onChange={set} /></div>
        ))}
      </div>

      <Button onClick={save} loading={saving}>Lưu thay đổi</Button>
    </div>
  );
}

function ToolPermissionsTab() {
  const [tools, setTools] = useState<Array<{ tool_name: string; enabled: boolean }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getToolPermissions().then(setTools).catch(() => {}).finally(() => setLoading(false)); }, []);

  const toggle = async (name: string, enabled: boolean) => {
    setTools((t) => t.map((x) => x.tool_name === name ? { ...x, enabled } : x));
    try { await api.updateToolPermission(name, enabled); } catch { setTools((t) => t.map((x) => x.tool_name === name ? { ...x, enabled: !enabled } : x)); }
  };

  if (loading) return <p className="text-sm text-[var(--text-secondary)] py-4">Đang tải...</p>;
  if (!tools.length) return <p className="text-sm text-[var(--text-secondary)] py-4">Chưa có tool nào được cấu hình. Các tool mặc định đều được bật.</p>;

  return (
    <div className="space-y-2">
      <p className="text-sm text-[var(--text-secondary)] mb-3">Bật/tắt từng tool mà JARVIS có thể sử dụng.</p>
      {tools.map(({ tool_name, enabled }) => (
        <div key={tool_name} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
          <div className="flex items-center gap-2">
            <Shield size={14} className={enabled ? "text-[var(--accent-green)]" : "text-[var(--text-tertiary)]"} />
            <span className="text-sm font-mono">{tool_name}</span>
          </div>
          <Toggle on={enabled} onChange={(v) => toggle(tool_name, v)} />
        </div>
      ))}
    </div>
  );
}

function AuditTab() {
  const [logs, setLogs] = useState<Array<{ id: string; event_type: string; node: string; tool_name: string | null; model_used: string | null; duration_ms: number; cost: number; timestamp: string; error: string | null }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getAuditLogs().then(setLogs).catch(() => {}).finally(() => setLoading(false)); }, []);

  if (loading) return <p className="text-sm text-[var(--text-secondary)] py-4">Đang tải...</p>;
  if (!logs.length) return <p className="text-sm text-[var(--text-secondary)] py-4">Chưa có log nào.</p>;

  const icons: Record<string, string> = { llm_call: "🧠", tool_call: "🔧", plan_created: "📝", approval: "✅" };

  return (
    <div className="space-y-2">
      <p className="text-sm text-[var(--text-secondary)] mb-3">Lịch sử hành động của JARVIS.</p>
      {logs.slice(0, 50).map((log) => (
        <div key={log.id} className="flex items-start gap-3 p-2.5 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] text-sm">
          <span className="mt-0.5">{icons[log.event_type] || "📋"}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium">{log.node}</span>
              {log.tool_name && <Badge color="purple" className="text-[10px]">{log.tool_name}</Badge>}
              {log.error && <Badge color="red" className="text-[10px]">error</Badge>}
            </div>
            <div className="flex gap-3 text-xs text-[var(--text-tertiary)] mt-0.5">
              <span>{new Date(log.timestamp).toLocaleString("vi")}</span>
              <span>{log.duration_ms}ms</span>
              {log.model_used && <span>{log.model_used}</span>}
              {log.cost > 0 && <span>${log.cost.toFixed(5)}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

const ICON_MAP: Record<string, string> = { google: "🔵", github: "⚫", notion: "📝", trello: "🟦", linear: "🟣", sentry: "🔴" };

function MCPTab() {
  const [registry, setRegistry] = useState<Array<{ id: string; name: string; description: string; icon: string; category: string; has_shared_key?: boolean }>>([]);
  const [servers, setServers] = useState<Array<{ id: string; name: string; enabled: boolean; curated_id: string | null }>>([]);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [reg, srv] = await Promise.all([api.mcpRegistry(), api.mcpServers()]);
      setRegistry(reg);
      setServers(srv);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const connectedIds = new Set(servers.map((s) => s.curated_id));

  const handleConnect = async (curatedId: string) => {
    if (!apiKey.trim()) return;
    try {
      await api.mcpConnect(curatedId, apiKey);
      setApiKey("");
      setConnecting(null);
      await load();
    } catch {}
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    setServers((s) => s.map((x) => x.id === id ? { ...x, enabled } : x));
    try { await api.mcpToggle(id, enabled); } catch { await load(); }
  };

  const handleDelete = async (id: string) => {
    setServers((s) => s.filter((x) => x.id !== id));
    try { await api.mcpDelete(id); } catch { await load(); }
  };

  if (loading) return <p className="text-sm text-[var(--text-secondary)] py-4">Đang tải...</p>;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium mb-3">MCP Servers có sẵn</p>
        <div className="grid grid-cols-1 gap-3">
          {registry.map((r) => {
            const connected = connectedIds.has(r.id);
            return (
              <div key={r.id} className="p-4 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{ICON_MAP[r.icon] || "🔌"}</span>
                    <div>
                      <p className="font-medium">{r.name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{r.description}</p>
                    </div>
                  </div>
                  {connected ? (
                    <Badge color="green" className="text-xs">Đã kết nối</Badge>
                  ) : connecting === r.id ? (
                    <div className="flex gap-2 items-center">
                      <Input value={apiKey} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiKey(e.target.value)} placeholder={r.has_shared_key ? "API Key (hoặc để trống dùng key chung)..." : "API Key..."} className="w-48 text-xs" onKeyDown={(e: React.KeyboardEvent) => e.key === "Enter" && handleConnect(r.id)} />
                      <Button size="sm" onClick={() => handleConnect(r.id)}>OK</Button>
                      <button onClick={() => { setConnecting(null); setApiKey(""); }} className="text-[var(--text-tertiary)]"><X size={14} /></button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      {r.has_shared_key && <Badge color="blue" className="text-[10px]">Free</Badge>}
                      <Button size="sm" variant="secondary" onClick={() => r.has_shared_key ? handleConnect(r.id) : setConnecting(r.id)}>{r.has_shared_key ? "Dùng ngay" : "Kết nối"}</Button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {servers.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-3">Đã kết nối ({servers.length})</p>
          <div className="space-y-2">
            {servers.map((s) => (
              <div key={s.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${s.enabled ? "bg-[var(--accent-green)]" : "bg-[var(--text-tertiary)]"}`} />
                  <span className="text-sm">{s.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Toggle on={s.enabled} onChange={(v) => handleToggle(s.id, v)} />
                  <button onClick={() => handleDelete(s.id)} className="text-[var(--text-tertiary)] hover:text-[var(--accent-red)]"><Trash2 size={14} /></button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const TYPE_LABELS: Record<string, string> = { fact: "Sự kiện", preference: "Sở thích", episodic: "Hội thoại", note: "Ghi chú" };

function MemoryTab() {
  const [memories, setMemories] = useState<Array<{ id: string; type: string; content: string; importance: number; metadata: Record<string, unknown> | null; created_at: string }>>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (search.trim()) {
        const res = await api.searchMemories(search);
        setMemories(res.memories);
        setTotal(res.memories.length);
      } else {
        const res = await api.listMemories(filter, 30);
        setMemories(res.memories);
        setTotal(res.total);
      }
    } catch {}
    setLoading(false);
  }, [search, filter]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id: string) => {
    try { await api.deleteMemory(id); setMemories((m) => m.filter((x) => x.id !== id)); setTotal((t) => t - 1); } catch {}
  };

  const handleSearch = () => { load(); };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input value={search} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)} placeholder="Tìm trong bộ nhớ..." className="flex-1" onKeyDown={(e: React.KeyboardEvent) => e.key === "Enter" && handleSearch()} />
        <Button size="sm" onClick={handleSearch}><Search size={14} /></Button>
      </div>
      <div className="flex gap-1">
        {["", "fact", "preference", "episodic", "note"].map((t) => (
          <button key={t} onClick={() => { setFilter(t); setSearch(""); }} className={`px-2.5 py-1 text-xs rounded-[var(--radius-md)] transition-colors ${filter === t && !search ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}>
            {t ? TYPE_LABELS[t] || t : "Tất cả"}
          </button>
        ))}
      </div>
      <p className="text-xs text-[var(--text-tertiary)]">{total} bộ nhớ</p>
      {loading ? (
        <p className="text-sm text-[var(--text-secondary)] py-4">Đang tải...</p>
      ) : memories.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)] text-center py-8">Chưa có bộ nhớ nào. Chat với JARVIS để bắt đầu tạo.</p>
      ) : (
        <div className="space-y-2">
          {memories.map((m) => (
            <div key={m.id} className="p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] group">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Badge color={m.type === "note" ? "blue" : m.type === "preference" ? "purple" : "default"} className="text-[10px]">{TYPE_LABELS[m.type] || m.type}</Badge>
                    <span className="text-[10px] text-[var(--text-tertiary)]">{m.created_at ? new Date(m.created_at).toLocaleDateString("vi") : ""}</span>
                  </div>
                  <p className="text-sm text-[var(--text-primary)] break-words">{m.content.length > 200 ? m.content.slice(0, 200) + "..." : m.content}</p>
                </div>
                <button onClick={() => handleDelete(m.id)} className="opacity-0 group-hover:opacity-100 transition-opacity text-[var(--text-tertiary)] hover:text-[var(--accent-red)] shrink-0" title="Xóa">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const user = useAuth((s) => s.user);
  const [tab, setTab] = useState(0);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Cài đặt</h1>

        <div className="flex gap-1 mb-6 overflow-x-auto">
          {tabs.map((t, i) => (
            <button key={t.label} onClick={() => setTab(i)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] whitespace-nowrap transition-colors ${tab === i ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Profile */}
        {tab === 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-14 w-14 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--accent-purple)] flex items-center justify-center text-lg font-semibold text-white">
                {user?.name?.[0]?.toUpperCase() || "?"}
              </div>
              <div>
                <p className="font-semibold">{user?.name || "Chưa đặt tên"}</p>
                <p className="text-sm text-[var(--text-secondary)]">{user?.email}</p>
              </div>
            </div>
            <div><label className="text-sm text-[var(--text-secondary)] mb-1 block">Tên hiển thị</label><Input defaultValue={user?.name || ""} /></div>
            <div><label className="text-sm text-[var(--text-secondary)] mb-1 block">Múi giờ</label><Input defaultValue="Asia/Ho_Chi_Minh (UTC+7)" disabled /></div>
            <Button>Lưu thay đổi</Button>
          </div>
        )}

        {tab === 1 && <PreferencesTab />}
        {tab === 2 && <MemoryTab />}
        {tab === 3 && <ConnectionsTab />}
        {tab === 4 && <MCPTab />}
        {tab === 5 && <ToolPermissionsTab />}
        {tab === 6 && <AuditTab />}
      </div>
    </div>
  );
}
