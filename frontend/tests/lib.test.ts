import { describe, it, expect, vi, beforeEach } from "vitest";
import { cn } from "@/lib/utils";

describe("cn utility", () => {
  it("merges class names", () => {
    expect(cn("px-2", "py-1")).toBe("px-2 py-1");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "extra")).toBe("base extra");
  });

  it("deduplicates tailwind conflicts", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});

describe("api module", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("attaches Authorization header when token exists", async () => {
    localStorage.setItem("token", "my-jwt");
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: "1" }), { status: 200, headers: { "Content-Type": "application/json" } })
    );

    // Dynamic import to pick up fresh localStorage
    const { api } = await import("@/lib/api");
    await api.me();

    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("/users/me"),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer my-jwt" }),
      })
    );
  });

  it("throws on non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("Unauthorized", { status: 401 })
    );

    const { api } = await import("@/lib/api");
    await expect(api.me()).rejects.toThrow("Unauthorized");
  });
});

describe("createWSClient", () => {
  it("creates WebSocket with token in URL", async () => {
    localStorage.setItem("token", "ws-tok");

    let capturedUrl = "";
    class MockWS {
      onmessage: any = null;
      onclose: any = null;
      onerror: any = null;
      readyState = 1;
      send = vi.fn();
      close = vi.fn();
      static OPEN = 1;
      constructor(url: string) { capturedUrl = url; }
    }
    vi.stubGlobal("WebSocket", MockWS);

    const { createWSClient } = await import("@/lib/ws");
    createWSClient(vi.fn());

    expect(capturedUrl).toContain("token=ws-tok");
  });
});
