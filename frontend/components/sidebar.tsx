"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, CheckSquare, Calendar, BarChart3, Settings } from "lucide-react";

const NAV = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/calendar", label: "Lịch", icon: Calendar },
  { href: "/analytics", label: "Thống kê", icon: BarChart3 },
  { href: "/settings", label: "Cài đặt", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-[var(--border)] flex flex-col p-4 gap-1">
      <Link href="/" className="text-xl font-bold mb-6 px-3">
        🤖 JARVIS
      </Link>
      {NAV.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={`flex items-center gap-3 px-3 py-2 rounded-lg transition ${
            pathname === href ? "bg-blue-600/20 text-blue-400" : "text-gray-400 hover:text-white hover:bg-white/5"
          }`}
        >
          <Icon size={18} />
          {label}
        </Link>
      ))}
    </aside>
  );
}
