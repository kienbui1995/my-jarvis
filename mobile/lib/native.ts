/** M91: Push notifications + M94: Location triggers + M95: Biometric auth */
import * as Notifications from "expo-notifications";
import * as Location from "expo-location";
import * as LocalAuthentication from "expo-local-authentication";
import * as SecureStore from "expo-secure-store";
import { api } from "./api";

// ── M91: Push Notifications ──
export async function registerPush() {
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") return null;
  const token = (await Notifications.getExpoPushTokenAsync()).data;
  await api("/push/register", { method: "POST", body: JSON.stringify({ token, platform: "expo" }) });
  return token;
}

Notifications.setNotificationHandler({
  handleNotification: async () => ({ shouldShowAlert: true, shouldPlaySound: true, shouldSetBadge: true }),
});

// ── M94: Location Triggers ──
interface GeoFence { id: string; lat: number; lng: number; radius: number; action: string }

let geoFences: GeoFence[] = [];

export async function startLocationTriggers(fences: GeoFence[]) {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== "granted") return;
  geoFences = fences;
  await Location.startLocationUpdatesAsync("jarvis-location", {
    accuracy: Location.Accuracy.Balanced,
    distanceInterval: 100,
    deferredUpdatesInterval: 60000,
  });
}

export function checkGeoFences(lat: number, lng: number): GeoFence | null {
  for (const f of geoFences) {
    const d = Math.sqrt((lat - f.lat) ** 2 + (lng - f.lng) ** 2) * 111000; // rough meters
    if (d < f.radius) return f;
  }
  return null;
}

// ── M95: Biometric Auth ──
export async function authenticateBiometric(): Promise<boolean> {
  const compatible = await LocalAuthentication.hasHardwareAsync();
  if (!compatible) return false;
  const enrolled = await LocalAuthentication.isEnrolledAsync();
  if (!enrolled) return false;
  const result = await LocalAuthentication.authenticateAsync({ promptMessage: "Xác thực để mở Jarvis", fallbackLabel: "Dùng mật khẩu" });
  return result.success;
}

export async function saveSecure(key: string, value: string) {
  await SecureStore.setItemAsync(key, value);
}

export async function getSecure(key: string): Promise<string | null> {
  return SecureStore.getItemAsync(key);
}
