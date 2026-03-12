"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, CheckSquare, Calendar, BarChart3, Settings, Menu, X, LogOut, Sun, Moon } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/stores/auth";
import { NotificationBell } from "@/components/layout/notification-bell";

const NAV = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/calendar", label: "Lịch", icon: Calendar },
  { href: "/analytics", label: "Thống kê", icon: BarChart3 },
  { href: "/settings", label: "Cài đặt", icon: Settings },
];

function NavItems({ onClick }: { onClick?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      {NAV.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          onClick={onClick}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-[var(--radius-lg)] transition-colors duration-150",
            pathname === href ? "bg-[var(--brand-subtle)] text-[var(--brand-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]/50"
          )}
        >
          <Icon size={18} />
          <span className="sidebar-label">{label}</span>
        </Link>
      ))}
    </>
  );
}

export function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = localStorage.getItem("theme") || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    setTheme(saved as "dark" | "light");
    document.documentElement.setAttribute("data-theme", saved);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("theme", next);
    document.documentElement.setAttribute("data-theme", next);
  };

  return (
    <>
      {/* Mobile hamburger */}
      <button onClick={() => setMobileOpen(true)} aria-label="Mở menu" className="fixed top-3 left-3 z-30 p-2 rounded-[var(--radius-md)] bg-[var(--bg-secondary)] border border-[var(--border-default)] sm:hidden">
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && <div className="fixed inset-0 z-30 bg-black/50 sm:hidden" onClick={() => setMobileOpen(false)} />}

      {/* Sidebar */}
      <aside className={cn(
        "fixed sm:static z-40 h-full bg-[var(--bg-secondary)] border-r border-[var(--border-default)] flex flex-col transition-transform duration-200",
        "w-[240px] sm:w-[240px] md:w-[240px]",
        mobileOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0"
      )}>
        {/* Header */}
        <div className="flex items-center justify-between p-4">
          <Link href="/" className="text-xl font-bold flex items-center gap-2">🤖 JARVIS</Link>
          <div className="flex items-center gap-1">
            {user && <NotificationBell />}
            <button onClick={() => setMobileOpen(false)} aria-label="Đóng menu" className="sm:hidden p-1 text-[var(--text-secondary)]"><X size={18} /></button>
          </div>
        </div>

        {/* Nav */}
        <nav role="navigation" aria-label="Menu chính" className="flex-1 flex flex-col gap-1 px-3">
          <NavItems onClick={() => setMobileOpen(false)} />
        </nav>

        {/* User footer */}
        {user && (
          <div className="p-3 border-t border-[var(--border-default)]">
            <button onClick={toggleTheme} aria-label={theme === "dark" ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối"} className="flex items-center gap-3 px-2 py-1.5 w-full rounded-[var(--radius-md)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors mb-2">
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              <span className="text-sm">{theme === "dark" ? "Sáng" : "Tối"}</span>
            </button>
            <div className="flex items-center gap-3 px-2">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--accent-purple)] flex items-center justify-center text-xs font-semibold text-white">
                {user.name?.[0]?.toUpperCase() || "?"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.name || user.email}</p>
                <p className="text-xs text-[var(--text-secondary)] capitalize">{user.tier}</p>
              </div>
              <button onClick={logout} aria-label="Đăng xuất" className="p-1 text-[var(--text-tertiary)] hover:text-[var(--accent-red)]"><LogOut size={16} /></button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
