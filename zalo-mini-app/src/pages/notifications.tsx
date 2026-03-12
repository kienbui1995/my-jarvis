import React, { useEffect, useState } from "react";
import { Page, Box, Text } from "zmp-ui";
import { api } from "../api";

type Notif = { id: string; type: string; content: string; read: boolean; created_at: string };
const ICON: Record<string, string> = { briefing: "☀️", reminder: "⏰", insight: "💡" };

export default function NotificationsPage() {
  const [items, setItems] = useState<Notif[]>([]);
  useEffect(() => { api.notifications().then(setItems).catch(() => {}); }, []);

  const markRead = async (id: string) => {
    await api.markRead(id).catch(() => {});
    setItems((p) => p.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  return (
    <Page>
      <Box style={{ padding: 12 }}>
        <Text size="xLarge" bold style={{ marginBottom: 12 }}>🔔 Thông báo</Text>
        {items.length === 0 ? (
          <Text style={{ color: "#888", textAlign: "center", marginTop: 40 }}>Chưa có thông báo</Text>
        ) : (
          items.map((n) => (
            <Box key={n.id} onClick={() => markRead(n.id)} style={{
              background: n.read ? "#2d2d44" : "#3d3d5c", borderRadius: 12, padding: 12, marginBottom: 8, cursor: "pointer",
            }}>
              <Text bold>{ICON[n.type] || "🔔"} {n.content.slice(0, 100)}{n.content.length > 100 ? "..." : ""}</Text>
              <Text size="xSmall" style={{ color: "#aaa", marginTop: 4 }}>
                {new Date(n.created_at).toLocaleString("vi", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
              </Text>
            </Box>
          ))
        )}
      </Box>
    </Page>
  );
}
