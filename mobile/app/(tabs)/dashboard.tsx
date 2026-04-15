/** M90: Dashboard with widgets — weather, tasks, spending, next event */
import { useEffect, useState } from "react";
import { View, Text, ScrollView, StyleSheet, RefreshControl } from "react-native";
import { api, getCached, cacheData } from "../../lib/api";

interface DashboardData { week: { tasks_completed: number; spending: number; mood_avg: number | null; active_goals: number } }

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    const cached = await getCached<DashboardData>("dashboard");
    if (cached) setData(cached);
    try {
      const fresh = await api<DashboardData>("/dashboard/overview");
      setData(fresh);
      cacheData("dashboard", fresh);
    } catch { /* use cached */ }
  }

  useEffect(() => { load(); }, []);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  return (
    <ScrollView style={s.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#e94560" />}>
      <Text style={s.header}>📊 Tuần này</Text>
      {data ? (
        <View style={s.grid}>
          <Widget icon="✅" label="Tasks done" value={String(data.week.tasks_completed)} />
          <Widget icon="💰" label="Chi tiêu" value={`${(data.week.spending / 1000).toFixed(0)}k`} />
          <Widget icon="😊" label="Mood" value={data.week.mood_avg ? `${data.week.mood_avg}/10` : "—"} />
          <Widget icon="🎯" label="Goals" value={String(data.week.active_goals)} />
        </View>
      ) : (
        <Text style={s.loading}>Đang tải...</Text>
      )}
    </ScrollView>
  );
}

function Widget({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <View style={s.widget}>
      <Text style={{ fontSize: 28 }}>{icon}</Text>
      <Text style={s.widgetValue}>{value}</Text>
      <Text style={s.widgetLabel}>{label}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0f0f23" },
  header: { fontSize: 24, fontWeight: "bold", color: "#fff", padding: 20 },
  grid: { flexDirection: "row", flexWrap: "wrap", padding: 12 },
  widget: { width: "46%", backgroundColor: "#16213e", borderRadius: 16, padding: 20, margin: "2%", alignItems: "center" },
  widgetValue: { fontSize: 28, fontWeight: "bold", color: "#fff", marginTop: 8 },
  widgetLabel: { fontSize: 13, color: "#888", marginTop: 4 },
  loading: { color: "#666", textAlign: "center", marginTop: 40 },
});
