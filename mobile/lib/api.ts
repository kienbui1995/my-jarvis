/** API client + auth + offline sync */
import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";

const API_URL = process.env.EXPO_PUBLIC_API_URL || "https://jarvis.pmai.space/api/v1";

// ── Auth Store ──
interface AuthState {
  token: string | null;
  setToken: (t: string | null) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => {
    if (token) AsyncStorage.setItem("token", token);
    else AsyncStorage.removeItem("token");
    set({ token });
  },
  logout: () => {
    AsyncStorage.removeItem("token");
    set({ token: null });
  },
}));

// ── API Client ──
export async function api<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = useAuth.getState().token;
  const res = await fetch(`${API_URL}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...opts.headers },
  });
  if (res.status === 401) useAuth.getState().logout();
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// ── M92: Offline Cache ──
const CACHE_KEYS = ["tasks", "calendar", "contacts"];

export async function cacheData(key: string, data: any) {
  await AsyncStorage.setItem(`cache:${key}`, JSON.stringify({ data, ts: Date.now() }));
}

export async function getCached<T>(key: string, maxAge = 3600000): Promise<T | null> {
  const raw = await AsyncStorage.getItem(`cache:${key}`);
  if (!raw) return null;
  const { data, ts } = JSON.parse(raw);
  if (Date.now() - ts > maxAge) return null;
  return data;
}

// Sync queue for offline mutations
export async function queueMutation(action: { method: string; path: string; body?: any }) {
  const queue = JSON.parse((await AsyncStorage.getItem("sync_queue")) || "[]");
  queue.push({ ...action, ts: Date.now() });
  await AsyncStorage.setItem("sync_queue", JSON.stringify(queue));
}

export async function flushSyncQueue() {
  const raw = await AsyncStorage.getItem("sync_queue");
  if (!raw) return;
  const queue = JSON.parse(raw);
  const failed: any[] = [];
  for (const action of queue) {
    try {
      await api(action.path, { method: action.method, body: action.body ? JSON.stringify(action.body) : undefined });
    } catch {
      failed.push(action);
    }
  }
  await AsyncStorage.setItem("sync_queue", JSON.stringify(failed));
}
