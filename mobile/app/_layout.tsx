/** Root layout — auth guard + tab navigation */
import { Slot, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { StatusBar } from "expo-status-bar";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAuth } from "../lib/api";
import { registerPush } from "../lib/native";

export default function RootLayout() {
  const { token, setToken } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    AsyncStorage.getItem("token").then((t) => t && setToken(t));
  }, []);

  useEffect(() => {
    if (token) registerPush();
    const inAuth = segments[0] === "(auth)";
    if (!token && !inAuth) router.replace("/(auth)/login");
    else if (token && inAuth) router.replace("/(tabs)/chat");
  }, [token, segments]);

  return (
    <>
      <StatusBar style="auto" />
      <Slot />
    </>
  );
}
