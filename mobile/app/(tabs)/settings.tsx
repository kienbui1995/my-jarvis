/** Settings screen — integrations, biometric, location triggers */
import { View, Text, TouchableOpacity, Switch, StyleSheet, Alert } from "react-native";
import { useState } from "react";
import { useAuth } from "../../lib/api";
import { authenticateBiometric } from "../../lib/native";

export default function Settings() {
  const { logout } = useAuth();
  const [biometric, setBiometric] = useState(false);
  const [locationTriggers, setLocationTriggers] = useState(false);

  async function toggleBiometric(val: boolean) {
    if (val) {
      const ok = await authenticateBiometric();
      if (!ok) return Alert.alert("Không hỗ trợ", "Thiết bị không hỗ trợ sinh trắc học");
    }
    setBiometric(val);
  }

  return (
    <View style={s.container}>
      <Text style={s.header}>⚙️ Cài đặt</Text>
      <Row label="🔐 Đăng nhập sinh trắc học" value={biometric} onToggle={toggleBiometric} />
      <Row label="📍 Nhắc nhở theo vị trí" value={locationTriggers} onToggle={setLocationTriggers} />
      <TouchableOpacity style={s.logoutBtn} onPress={logout}>
        <Text style={s.logoutText}>Đăng xuất</Text>
      </TouchableOpacity>
    </View>
  );
}

function Row({ label, value, onToggle }: { label: string; value: boolean; onToggle: (v: boolean) => void }) {
  return (
    <View style={s.row}>
      <Text style={s.rowLabel}>{label}</Text>
      <Switch value={value} onValueChange={onToggle} trackColor={{ true: "#e94560" }} />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23", padding: 20 },
  header: { fontSize: 24, fontWeight: "bold", color: "#fff", marginBottom: 24 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: "#16213e" },
  rowLabel: { color: "#fff", fontSize: 16 },
  logoutBtn: { marginTop: 40, backgroundColor: "#e94560", padding: 16, borderRadius: 12, alignItems: "center" },
  logoutText: { color: "#fff", fontSize: 16, fontWeight: "600" },
});
