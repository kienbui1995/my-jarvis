"use client";
import { useEffect, useState } from "react";
import { Plug, Check, X } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";

type Integration = { id: string; name: string; connected: boolean };

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [token, setToken] = useState("");
  const toast = useToast((s) => s.add);

  const load = () => api.listIntegrations().then((r) => setIntegrations(r.integrations)).catch(() => {});
  useEffect(() => { load(); }, []);

  const connect = async () => {
    if (!connecting || !token) return;
    await api.connectIntegration(connecting, token);
    toast("success", `Đã kết nối ${connecting}`);
    setConnecting(null); setToken(""); load();
  };

  const disconnect = async (id: string) => {
    await api.disconnectIntegration(id);
    toast("success", "Đã ngắt kết nối");
    load();
  };

  const icons: Record<string, string> = { spotify: "🎵", notion: "📝", github: "🐙", home_assistant: "🏠" };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">🔌 Kết nối</h1>
        <div className="space-y-3">
          {integrations.map((i) => (
            <div key={i.id} className="flex items-center justify-between p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-lg)]">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{icons[i.id] || "🔗"}</span>
                <div>
                  <div className="font-medium">{i.name}</div>
                  <div className="text-sm text-[var(--text-secondary)]">{i.connected ? "Đã kết nối" : "Chưa kết nối"}</div>
                </div>
              </div>
              {i.connected ? (
                <Button size="sm" variant="ghost" onClick={() => disconnect(i.id)}><X size={14} /> Ngắt</Button>
              ) : (
                <Button size="sm" onClick={() => setConnecting(i.id)}><Plug size={14} /> Kết nối</Button>
              )}
            </div>
          ))}
        </div>

        <Modal open={!!connecting} onClose={() => setConnecting(null)} title={`Kết nối ${connecting}`}>
          <div className="space-y-3">
            <p className="text-sm text-[var(--text-secondary)]">Nhập API token/key cho {connecting}</p>
            <Input placeholder="Token / API Key" value={token} onChange={(e) => setToken(e.target.value)} type="password" />
            <Button onClick={connect} className="w-full">Kết nối</Button>
          </div>
        </Modal>
      </div>
    </div>
  );
}
