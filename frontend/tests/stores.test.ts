import { describe, it, expect, vi, beforeEach } from "vitest";
import { useAuth } from "@/lib/stores/auth";
import { useChat } from "@/lib/stores/chat";

// Mock api module
vi.mock("@/lib/api", () => ({
  api: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
  },
}));

import { api } from "@/lib/api";

describe("useAuth", () => {
  beforeEach(() => {
    useAuth.setState({ user: null, loading: true });
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("login stores token and sets user", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "tok123", refresh_token: "r" });
    vi.mocked(api.me).mockResolvedValue({ id: "1", name: "A", email: "a@b.c", tier: "free" });

    await useAuth.getState().login("a@b.c", "pass");

    expect(localStorage.getItem("token")).toBe("tok123");
    expect(useAuth.getState().user).toEqual({ id: "1", name: "A", email: "a@b.c", tier: "free" });
  });

  it("register stores token and sets user", async () => {
    vi.mocked(api.register).mockResolvedValue({ access_token: "tok456", refresh_token: "r" });
    vi.mocked(api.me).mockResolvedValue({ id: "2", name: "B", email: "b@c.d", tier: "free" });

    await useAuth.getState().register("b@c.d", "pass", "B");

    expect(localStorage.getItem("token")).toBe("tok456");
    expect(useAuth.getState().user?.name).toBe("B");
  });

  it("logout clears token and user", () => {
    localStorage.setItem("token", "old");
    useAuth.setState({ user: { id: "1", name: "A", email: "a@b.c", tier: "free" } });

    useAuth.getState().logout();

    expect(localStorage.getItem("token")).toBeNull();
    expect(useAuth.getState().user).toBeNull();
  });

  it("loadUser sets user on success", async () => {
    vi.mocked(api.me).mockResolvedValue({ id: "1", name: "A", email: "a@b.c", tier: "pro" });

    await useAuth.getState().loadUser();

    expect(useAuth.getState().user?.tier).toBe("pro");
    expect(useAuth.getState().loading).toBe(false);
  });

  it("loadUser clears user on failure", async () => {
    vi.mocked(api.me).mockRejectedValue(new Error("401"));

    await useAuth.getState().loadUser();

    expect(useAuth.getState().user).toBeNull();
    expect(useAuth.getState().loading).toBe(false);
  });
});

describe("useChat", () => {
  beforeEach(() => {
    useChat.getState().clear();
  });

  it("addUserMessage appends user message", () => {
    useChat.getState().addUserMessage("hello");

    const msgs = useChat.getState().messages;
    expect(msgs).toHaveLength(1);
    expect(msgs[0].role).toBe("user");
    expect(msgs[0].content).toBe("hello");
  });

  it("startStreaming adds empty assistant message", () => {
    useChat.getState().startStreaming();

    const msgs = useChat.getState().messages;
    expect(msgs).toHaveLength(1);
    expect(msgs[0].role).toBe("assistant");
    expect(msgs[0].streaming).toBe(true);
    expect(useChat.getState().streaming).toBe(true);
  });

  it("appendStream accumulates content", () => {
    useChat.getState().startStreaming();
    useChat.getState().appendStream("Xin ");
    useChat.getState().appendStream("chào!");

    expect(useChat.getState().messages[0].content).toBe("Xin chào!");
  });

  it("finishStreaming sets final content and stops streaming", () => {
    useChat.getState().startStreaming();
    useChat.getState().appendStream("partial");
    useChat.getState().finishStreaming("full response");

    const msg = useChat.getState().messages[0];
    expect(msg.content).toBe("full response");
    expect(msg.streaming).toBe(false);
    expect(useChat.getState().streaming).toBe(false);
  });

  it("clear resets everything", () => {
    useChat.getState().addUserMessage("test");
    useChat.getState().clear();

    expect(useChat.getState().messages).toHaveLength(0);
    expect(useChat.getState().streaming).toBe(false);
  });
});
