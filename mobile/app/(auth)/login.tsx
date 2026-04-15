/** Login screen */
import { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { api, useAuth } from "../../lib/api";
import { authenticateBiometric, getSecure, saveSecure } from "../../lib/native";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { setToken } = useAuth();

  async function handleLogin() {
    try {
      const saved = await getSecure("credentials");
      if (saved) {
        const ok = await authenticateBiometric();
        if (ok) {
          const { email: e, password: p } = JSON.parse(saved);
          const res = await api("/auth/login", { method: "POST", body: JSON.stringify({ email: e, password: p }) });
          setToken(res.access_token);
          return;
        }
      }
      const res = await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setToken(res.access_token);
      await saveSecure("credentials", JSON.stringify({ email, password }));
    } catch {
      Alert.alert("Lỗi", "Email hoặc mật khẩu không đúng");
    }
  }

  return (
    <View style={s.container}>
      <Text style={s.title}>MY JARVIS</Text>
      <Text style={s.subtitle}>Trợ lý AI cá nhân</Text>
      <TextInput style={s.input} placeholder="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />
      <TextInput style={s.input} placeholder="Mật khẩu" value={password} onChangeText={setPassword} secureTextEntry />
      <TouchableOpacity style={s.btn} onPress={handleLogin}><Text style={s.btnText}>Đăng nhập</Text></TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#1a1a2e" },
  title: { fontSize: 32, fontWeight: "bold", color: "#e94560", textAlign: "center" },
  subtitle: { fontSize: 16, color: "#aaa", textAlign: "center", marginBottom: 40 },
  input: { backgroundColor: "#16213e", color: "#fff", padding: 16, borderRadius: 12, marginBottom: 12, fontSize: 16 },
  btn: { backgroundColor: "#e94560", padding: 16, borderRadius: 12, alignItems: "center", marginTop: 8 },
  btnText: { color: "#fff", fontSize: 18, fontWeight: "600" },
});
