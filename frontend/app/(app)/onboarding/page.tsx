"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/stores/auth";
import { api } from "@/lib/api";

const interests = [
  { id: "tasks", emoji: "📋", label: "Quản lý công việc" },
  { id: "finance", emoji: "💰", label: "Theo dõi chi tiêu" },
  { id: "calendar", emoji: "📅", label: "Lịch & nhắc nhở" },
  { id: "research", emoji: "🔍", label: "Tìm kiếm & tóm tắt" },
  { id: "writing", emoji: "✍️", label: "Viết & soạn thảo" },
  { id: "learning", emoji: "📚", label: "Học tập" },
];

const channels = [
  { id: "zalo", icon: "💬", label: "Zalo OA", desc: "Nhắn tin qua Zalo" },
  { id: "telegram", icon: "✈️", label: "Telegram", desc: "Bot Telegram" },
  { id: "web", icon: "🌐", label: "Web", desc: "Đang dùng", connected: true },
];

export default function OnboardingPage() {
  const user = useAuth((s) => s.user);
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [name, setName] = useState(user?.name || "");
  const [selected, setSelected] = useState<string[]>([]);

  const toggle = (id: string) => setSelected((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id]);

  const finish = async () => {
    try {
      await api.updateProfile({ name, preferences: { interests: selected } });
      // Auto-create default proactive triggers
      const defaultTriggers = [
        { trigger_type: "morning_briefing", config: {} },
        { trigger_type: "deadline_approaching", config: { hours_before: 2 } },
      ];
      for (const t of defaultTriggers) {
        try { await api.createTrigger(t.trigger_type, t.config); } catch {}
      }
    } catch {}
    router.push("/chat");
  };

  return (
    <div className="flex items-center justify-center h-full px-4">
      <div className="w-full max-w-md">
        {/* Progress */}
        <div className="flex gap-1.5 mb-8">
          {[0, 1, 2].map((i) => (
            <div key={i} className={`h-1 flex-1 rounded-full transition-colors ${i <= step ? "bg-[var(--brand-primary)]" : "bg-[var(--bg-tertiary)]"}`} />
          ))}
        </div>

        {/* Step 1: Greeting */}
        {step === 0 && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="text-5xl mb-4">👋</div>
              <h1 className="text-2xl font-bold">Chào mừng đến Jarvis!</h1>
              <p className="text-[var(--text-secondary)] mt-2">Mình cần biết tên bạn để giao tiếp tự nhiên hơn</p>
            </div>
            <div>
              <label className="text-sm text-[var(--text-secondary)] mb-1 block">Tên của bạn</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nhập tên..." autoFocus />
            </div>
            <Button className="w-full" onClick={() => setStep(1)} disabled={!name.trim()}>Tiếp tục</Button>
          </div>
        )}

        {/* Step 2: Interests */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">Bạn muốn Jarvis giúp gì?</h1>
              <p className="text-[var(--text-secondary)] mt-2">Chọn để mình cá nhân hóa trải nghiệm</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {interests.map(({ id, emoji, label }) => (
                <button key={id} onClick={() => toggle(id)} className={`flex items-center gap-2 p-3 rounded-[var(--radius-lg)] border text-left text-sm transition-colors ${selected.includes(id) ? "border-[var(--brand-primary)] bg-[var(--brand-subtle)]" : "border-[var(--border-default)] hover:border-[var(--border-hover)]"}`}>
                  <span className="text-lg">{emoji}</span>
                  <span>{label}</span>
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setStep(0)} className="flex-1">Quay lại</Button>
              <Button onClick={() => setStep(2)} className="flex-1">Tiếp tục</Button>
            </div>
          </div>
        )}

        {/* Step 3: Channels */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">Kết nối kênh chat</h1>
              <p className="text-[var(--text-secondary)] mt-2">Nói chuyện với Jarvis ở bất cứ đâu</p>
            </div>
            <div className="space-y-2">
              {channels.map(({ id, icon, label, desc, connected }) => (
                <div key={id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)]">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{icon}</span>
                    <div>
                      <p className="font-medium text-sm">{label}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{desc}</p>
                    </div>
                  </div>
                  {connected
                    ? <span className="text-xs text-[var(--accent-green)]">✓ Đã kết nối</span>
                    : <Button size="sm" variant="secondary">Kết nối</Button>
                  }
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setStep(1)} className="flex-1">Quay lại</Button>
              <Button onClick={finish} className="flex-1">Bắt đầu dùng Jarvis 🚀</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
