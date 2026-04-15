/** Tab layout — Chat, Dashboard, Settings */
import { Tabs } from "expo-router";
import { Text } from "react-native";

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ headerStyle: { backgroundColor: "#1a1a2e" }, headerTintColor: "#fff", tabBarStyle: { backgroundColor: "#1a1a2e", borderTopColor: "#16213e" }, tabBarActiveTintColor: "#e94560" }}>
      <Tabs.Screen name="chat" options={{ title: "Chat", tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>💬</Text> }} />
      <Tabs.Screen name="dashboard" options={{ title: "Dashboard", tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>📊</Text> }} />
      <Tabs.Screen name="settings" options={{ title: "Settings", tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>⚙️</Text> }} />
    </Tabs>
  );
}
