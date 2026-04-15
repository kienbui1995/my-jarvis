/** M89+M93: Chat screen with voice input */
import { useState, useRef, useEffect } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from "react-native";
import { Audio } from "expo-av";
import { api } from "../../lib/api";

interface Message { role: "user" | "assistant"; content: string }

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [loading, setLoading] = useState(false);
  const flatRef = useRef<FlatList>(null);

  async function send(text: string) {
    if (!text.trim()) return;
    const userMsg: Message = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await api("/chat", { method: "POST", body: JSON.stringify({ message: text }) });
      setMessages((m) => [...m, { role: "assistant", content: res.response }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "⚠️ Lỗi kết nối" }]);
    }
    setLoading(false);
  }

  // M93: Voice input
  async function toggleVoice() {
    if (recording) {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      if (uri) {
        // Upload audio → STT → send as text
        const form = new FormData();
        form.append("audio", { uri, type: "audio/m4a", name: "voice.m4a" } as any);
        try {
          const res = await api("/voice/stt", { method: "POST", body: form, headers: { "Content-Type": "multipart/form-data" } });
          if (res.text) send(res.text);
        } catch { /* ignore */ }
      }
    } else {
      await Audio.requestPermissionsAsync();
      const { recording: rec } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecording(rec);
    }
  }

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === "ios" ? "padding" : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={flatRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        onContentSizeChange={() => flatRef.current?.scrollToEnd()}
        renderItem={({ item }) => (
          <View style={[s.bubble, item.role === "user" ? s.userBubble : s.aiBubble]}>
            <Text style={s.bubbleText}>{item.content}</Text>
          </View>
        )}
        contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
      />
      {loading && <Text style={s.typing}>Jarvis đang suy nghĩ...</Text>}
      <View style={s.inputRow}>
        <TouchableOpacity onPress={toggleVoice} style={s.voiceBtn}>
          <Text style={{ fontSize: 24 }}>{recording ? "⏹️" : "🎤"}</Text>
        </TouchableOpacity>
        <TextInput style={s.textInput} value={input} onChangeText={setInput} placeholder="Nhắn Jarvis..." placeholderTextColor="#666" onSubmitEditing={() => send(input)} />
        <TouchableOpacity onPress={() => send(input)} style={s.sendBtn}>
          <Text style={{ fontSize: 20 }}>➤</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  bubble: { maxWidth: "80%", padding: 12, borderRadius: 16, marginBottom: 8 },
  userBubble: { alignSelf: "flex-end", backgroundColor: "#e94560" },
  aiBubble: { alignSelf: "flex-start", backgroundColor: "#16213e" },
  bubbleText: { color: "#fff", fontSize: 15 },
  typing: { color: "#666", paddingHorizontal: 20, paddingBottom: 4, fontSize: 13 },
  inputRow: { flexDirection: "row", alignItems: "center", padding: 8, borderTopWidth: 1, borderTopColor: "#16213e", backgroundColor: "#1a1a2e" },
  voiceBtn: { padding: 8 },
  textInput: { flex: 1, backgroundColor: "#16213e", color: "#fff", padding: 12, borderRadius: 20, marginHorizontal: 8, fontSize: 15 },
  sendBtn: { padding: 8 },
});
