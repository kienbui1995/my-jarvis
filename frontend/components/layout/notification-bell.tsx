"use client";
import { useEffect, useState, useRef } from "react";
import { Bell } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Notification = { id: string; type: string; content: string; read: boolean; created_at: string };

export function NotificationBell() {
  const [items, setItems] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const unread = items.filter((n) => !n.read).length;

  useEffect(() => {
    api.notifications(false).then(setItems).catch(() => {});
    const interval = setInterval(() => api.notifications(false).then(setItems).catch(() => {}), 60_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const markRead = async (id: string) => {
    await api.markRead(id).catch(() => {});
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const icon = { briefing: "☀️", reminder: "⏰", insight: "💡" } as Record<string, string>;

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} aria-label="Thông báo" className="relative p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[var(--accent-red)] text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-80 max-h-96 overflow-y-auto bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] shadow-xl z-50">
          <div className="px-3 py-2 border-b border-[var(--border-default)] font-semibold text-sm">Thông báo</div>
          {items.length === 0 ? (
            <p className="p-4 text-sm text-[var(--text-tertiary)] text-center">Chưa có thông báo</p>
          ) : (
            items.map((n) => (
              <button
                key={n.id}
                onClick={() => markRead(n.id)}
                className={cn(
                  "w-full text-left px-3 py-2.5 border-b border-[var(--border-default)] hover:bg-[var(--bg-tertiary)] transition-colors",
                  !n.read && "bg-[var(--bg-tertiary)]/50"
                )}
              >
                <div className="flex items-start gap-2">
                  <span className="text-base shrink-0">{icon[n.type] || "🔔"}</span>
                  <div className="min-w-0">
                    <p className={cn("text-sm line-clamp-3", !n.read && "font-medium")}>{n.content}</p>
                    <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
                      {new Date(n.created_at).toLocaleString("vi", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                  {!n.read && <span className="w-2 h-2 bg-[var(--brand-primary)] rounded-full shrink-0 mt-1.5" />}
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
