import { create } from "zustand";
import { api } from "@/lib/api";

type User = { id: string; name: string; email: string; tier: string; timezone: string };
type AuthStore = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  googleLogin: (credential: string) => Promise<void>;
  loadUser: () => Promise<void>;
  logout: () => void;
};

function saveTokens(data: { access_token: string; refresh_token: string }) {
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

export const useAuth = create<AuthStore>((set) => ({
  user: null,
  loading: true,
  login: async (email, password) => {
    const tokens = await api.login(email, password);
    saveTokens(tokens);
    set({ user: await api.me() });
  },
  register: async (email, password, name) => {
    const tokens = await api.register(email, password, name);
    saveTokens(tokens);
    set({ user: await api.me() });
  },
  googleLogin: async (credential) => {
    const tokens = await api.googleAuth(credential);
    saveTokens(tokens);
    set({ user: await api.me() });
  },
  loadUser: async () => {
    try {
      set({ user: await api.me(), loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    set({ user: null });
  },
}));
