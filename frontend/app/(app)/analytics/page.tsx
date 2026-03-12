"use client";
import { useEffect, useState } from "react";
import { MessageSquare, CheckSquare, Wallet, Brain } from "lucide-react";
import { api } from "@/lib/api";
import { LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";

const summaryCards = [
  { label: "Tin nhắn", icon: MessageSquare, key: "messages_today", color: "var(--brand-primary)" },
  { label: "Tasks done", icon: CheckSquare, key: "tasks_done", color: "var(--accent-green)" },
  { label: "Chi tiêu", icon: Wallet, key: "spending", color: "var(--accent-orange)" },
  { label: "Memories", icon: Brain, key: "memories", color: "var(--accent-purple)" },
];

// Mock 7-day data (will be replaced by real API)
const weekData = [
  { day: "T2", msgs: 12 }, { day: "T3", msgs: 8 }, { day: "T4", msgs: 15 },
  { day: "T5", msgs: 22 }, { day: "T6", msgs: 18 }, { day: "T7", msgs: 5 }, { day: "CN", msgs: 3 },
];

const modelData = [
  { name: "Gemini Flash", value: 65, color: "#3B82F6" },
  { name: "Claude Haiku", value: 25, color: "#8B5CF6" },
  { name: "Claude Sonnet", value: 10, color: "#F59E0B" },
];

const spendingData = [
  { name: "LLM", value: 70, color: "#3B82F6" },
  { name: "Embeddings", value: 20, color: "#22C55E" },
  { name: "Tools", value: 10, color: "#EAB308" },
];

export default function AnalyticsPage() {
  const [usage, setUsage] = useState({ messages_today: 0, tokens_today: 0, cost_today: 0 });
  useEffect(() => { api.usage().then(setUsage).catch(() => {}); }, []);

  const data: Record<string, number | string> = { messages_today: usage.messages_today, tasks_done: 0, spending: "0đ", memories: 0 };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Thống kê</h1>

        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {summaryCards.map(({ label, icon: Icon, key, color }) => (
            <div key={key} className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] p-4">
              <Icon size={20} style={{ color }} />
              <p className="text-2xl font-bold mt-2">{data[key]}</p>
              <p className="text-sm text-[var(--text-secondary)]">{label}</p>
            </div>
          ))}
        </div>

        {/* Usage chart */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] p-4 mb-4">
          <h3 className="text-sm font-semibold mb-3">Tin nhắn 7 ngày qua</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={weekData}>
              <XAxis dataKey="day" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 12 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", borderRadius: 8, color: "var(--text-primary)" }} />
              <Line type="monotone" dataKey="msgs" stroke="var(--brand-primary)" strokeWidth={2} dot={{ r: 3, fill: "var(--brand-primary)" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pie charts row */}
        <div className="grid grid-cols-2 gap-3">
          {[{ title: "Chi phí", data: spendingData }, { title: "Model AI", data: modelData }].map(({ title, data: d }) => (
            <div key={title} className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] p-4">
              <h3 className="text-sm font-semibold mb-2">{title}</h3>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={d} cx="50%" cy="50%" innerRadius={30} outerRadius={55} dataKey="value" stroke="none">
                    {d.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", borderRadius: 8, color: "var(--text-primary)", fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-1">
                {d.map(({ name, value, color }) => (
                  <div key={name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
                      <span className="text-[var(--text-secondary)]">{name}</span>
                    </div>
                    <span>{value}%</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* AI usage detail */}
        <div className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] p-4 mt-4">
          <h3 className="text-sm font-semibold mb-3">AI Usage hôm nay</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Tokens</span><span>{usage.tokens_today.toLocaleString()}</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Chi phí</span><span>${usage.cost_today.toFixed(4)}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
