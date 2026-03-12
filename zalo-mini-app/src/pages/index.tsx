/**
 * Chat page — simple text input, sends to backend WS, shows responses.
 */
import React, { useState, useRef, useEffect } from "react";
import { Page, Box, Text, Input, Button } from "zmp-ui";

type Msg = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMsgs((p) => [...p, { role: "user", content: text }]);
    setLoading(true);
    try {
      // Simple HTTP fallback (WS not available in Mini App WebView)
      const res = await fetch("__API_URL__/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${sessionStorage.getItem("token") || ""}` },
        body: JSON.stringify({ content: text }),
      });
      const data = await res.json();
      setMsgs((p) => [...p, { role: "assistant", content: data.response || "..." }]);
    } catch {
      setMsgs((p) => [...p, { role: "assistant", content: "Lỗi kết nối, thử lại sau." }]);
    }
    setLoading(false);
  };

  return (
    <Page>
      <Box flex flexDirection="column" style={{ height: "calc(100vh - 100px)" }}>
        <Box flex flexDirection="column" style={{ flex: 1, overflow: "auto", padding: 12, gap: 8 }}>
          {msgs.length === 0 && (
            <Box style={{ textAlign: "center", marginTop: 60, color: "#888" }}>
              <Text size="xLarge">🤖</Text>
              <Text>Chào bạn! Tôi là JARVIS</Text>
            </Box>
          )}
          {msgs.map((m, i) => (
            <Box key={i} style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "#6C5CE7" : "#2d2d44",
              color: "#fff", borderRadius: 16, padding: "8px 14px", maxWidth: "80%",
            }}>
              <Text size="small" style={{ whiteSpace: "pre-wrap" }}>{m.content}</Text>
            </Box>
          ))}
          <div ref={bottom} />
        </Box>
        <Box flex style={{ padding: 8, gap: 8, borderTop: "1px solid #333" }}>
          <Input placeholder="Nhập tin nhắn..." value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e: any) => e.key === "Enter" && send()} style={{ flex: 1 }} />
          <Button size="small" onClick={send} loading={loading}>Gửi</Button>
        </Box>
      </Box>
    </Page>
  );
}
