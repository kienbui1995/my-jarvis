/**
 * Chat page — voice-first, HTTP chat endpoint, quick actions.
 */
import React, { useState, useRef, useEffect, useCallback } from "react";
import { Page, Box, Text, Input, Button, Icon } from "zmp-ui";
import { api, getToken } from "../api";

type Msg = { role: "user" | "assistant"; content: string; imageUrl?: string };

const QUICK_ACTIONS = [
  { label: "Thời tiết", msg: "Thời tiết hôm nay ở Sài Gòn" },
  { label: "Tin tức", msg: "Tóm tắt tin tức hôm nay" },
  { label: "Tasks", msg: "Liệt kê tasks của tôi" },
  { label: "Lịch", msg: "Lịch hôm nay" },
];

export default function ChatPage() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [pendingFile, setPendingFile] = useState<{ key: string; url: string; name: string } | null>(null);
  const [uploading, setUploading] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading) return;
    const fileKey = pendingFile?.key;
    const imageUrl = pendingFile?.url;
    setInput("");
    setPendingFile(null);
    setMsgs((p) => [...p, { role: "user", content: text, imageUrl }]);
    setLoading(true);
    try {
      const data = await api.chat(text, fileKey || undefined);
      setMsgs((p) => [...p, { role: "assistant", content: data.response }]);
    } catch {
      setMsgs((p) => [...p, { role: "assistant", content: "Lỗi kết nối, thử lại sau." }]);
    }
    setLoading(false);
  }, [loading, pendingFile]);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await api.uploadFile(file, file.name);
      setPendingFile({ key: result.key, url: result.url, name: file.name });
    } catch {
      // Upload failed silently
    }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  }, []);

  // Voice recording
  const toggleRecord = useCallback(async () => {
    if (recording) {
      recorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size > 0) {
          setTranscribing(true);
          try {
            const text = await api.transcribe(blob);
            if (text) await sendMessage(text);
          } catch {
            setMsgs((p) => [...p, { role: "assistant", content: "Không nhận dạng được giọng nói." }]);
          }
          setTranscribing(false);
        }
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      // Mic not available
    }
  }, [recording, sendMessage]);

  // Play TTS for a message
  const playTTS = (text: string) => {
    const url = api.speakUrl(text);
    const audio = new Audio();
    audio.crossOrigin = "anonymous";
    // Need auth header — use fetch + blob instead
    fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const objUrl = URL.createObjectURL(blob);
        audio.src = objUrl;
        audio.onended = () => URL.revokeObjectURL(objUrl);
        audio.play();
      })
      .catch(() => {});
  };

  return (
    <Page>
      <Box flex flexDirection="column" style={{ height: "calc(100vh - 100px)" }}>
        {/* Messages */}
        <Box flex flexDirection="column" style={{ flex: 1, overflow: "auto", padding: 12, gap: 8 }}>
          {msgs.length === 0 && (
            <Box style={{ textAlign: "center", marginTop: 40 }}>
              <Text size="xLarge" style={{ marginBottom: 8 }}>🤖</Text>
              <Text style={{ color: "#ccc", marginBottom: 16 }}>Chào bạn! Tôi là JARVIS</Text>
              <Box flex style={{ flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
                {QUICK_ACTIONS.map((qa) => (
                  <Button key={qa.label} size="small" variant="secondary"
                    onClick={() => sendMessage(qa.msg)}
                    style={{ borderRadius: 20, fontSize: 13 }}>
                    {qa.label}
                  </Button>
                ))}
              </Box>
            </Box>
          )}
          {msgs.map((m, i) => (
            <Box key={i} style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "#6C5CE7" : "#2d2d44",
              color: "#fff", borderRadius: 16, padding: "8px 14px", maxWidth: "80%",
            }}>
              {m.imageUrl && (
                <img src={m.imageUrl} alt="" style={{ maxWidth: "100%", borderRadius: 8, marginBottom: 6 }} />
              )}
              <Text size="small" style={{ whiteSpace: "pre-wrap" }}>{m.content}</Text>
              {m.role === "assistant" && (
                <Box style={{ marginTop: 4 }}>
                  <Text size="xxSmall" style={{ color: "#aaa", cursor: "pointer" }}
                    onClick={() => playTTS(m.content)}>
                    🔊 Nghe
                  </Text>
                </Box>
              )}
            </Box>
          ))}
          {loading && (
            <Box style={{ alignSelf: "flex-start", background: "#2d2d44", borderRadius: 16, padding: "8px 14px" }}>
              <Text size="small" style={{ color: "#aaa" }}>Đang suy nghĩ...</Text>
            </Box>
          )}
          <div ref={bottom} />
        </Box>

        {/* Pending file indicator */}
        {pendingFile && (
          <Box flex style={{ padding: "4px 12px", gap: 8, alignItems: "center", background: "#2d2d44" }}>
            <Text size="xxSmall" style={{ color: "#aaa", flex: 1 }}>📎 {pendingFile.name}</Text>
            <Text size="xxSmall" style={{ color: "#f66", cursor: "pointer" }}
              onClick={() => setPendingFile(null)}>✕</Text>
          </Box>
        )}

        {/* Input bar */}
        <input ref={fileRef} type="file" accept="image/*,.pdf,.txt,.docx,.xlsx"
          style={{ display: "none" }} onChange={handleFileSelect} />
        <Box flex style={{ padding: 8, gap: 8, borderTop: "1px solid #333", alignItems: "center" }}>
          <Button size="small" variant="secondary"
            onClick={() => fileRef.current?.click()}
            disabled={uploading || loading}
            style={{ borderRadius: "50%", width: 40, height: 40, padding: 0 }}>
            {uploading ? "..." : "📎"}
          </Button>
          <Button size="small" variant={recording ? "primary" : "secondary"}
            onClick={toggleRecord}
            disabled={transcribing || loading}
            style={{ borderRadius: "50%", width: 40, height: 40, padding: 0 }}>
            {transcribing ? "..." : recording ? "⏹" : "🎤"}
          </Button>
          <Input
            placeholder={transcribing ? "Đang nhận dạng..." : pendingFile ? "Hỏi về file..." : "Nhập tin nhắn..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e: any) => e.key === "Enter" && sendMessage(input)}
            disabled={loading || transcribing}
            style={{ flex: 1 }}
          />
          <Button size="small" onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            style={{ borderRadius: "50%", width: 40, height: 40, padding: 0 }}>
            ➤
          </Button>
        </Box>
      </Box>
    </Page>
  );
}
