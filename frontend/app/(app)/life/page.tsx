"use client";
import { useEffect, useState } from "react";
import { Plus, Target, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";

type Overview = { week: { tasks_completed: number; spending: number; mood_avg: number | null; active_goals: number } };
type Goal = { id: string; title: string; target_value?: number; current_value: number; status: string; deadline?: string };

export default function LifePage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ title: "", target_value: "", deadline: "" });
  const toast = useToast((s) => s.add);

  useEffect(() => {
    api.lifeOverview().then(setOverview).catch(() => {});
    api.listGoals().then((r) => setGoals(r.data)).catch(() => {});
  }, []);

  const createGoal = async () => {
    await api.createGoal(form.title, form.target_value ? +form.target_value : undefined, form.deadline || undefined);
    toast("success", `🎯 Goal: ${form.title}`);
    setForm({ title: "", target_value: "", deadline: "" }); setShowAdd(false);
    api.listGoals().then((r) => setGoals(r.data));
  };

  const completeGoal = async (g: Goal) => {
    await api.updateGoal(g.id, { status: "completed" });
    setGoals(goals.map((x) => x.id === g.id ? { ...x, status: "completed" } : x));
  };

  const w = overview?.week;

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">🌟 Life Dashboard</h1>

        {w && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Stat icon="✅" label="Tasks done" value={String(w.tasks_completed)} />
            <Stat icon="💰" label="Chi tiêu" value={`${(w.spending / 1000).toFixed(0)}k`} />
            <Stat icon="😊" label="Mood" value={w.mood_avg ? `${w.mood_avg}/10` : "—"} />
            <Stat icon="🎯" label="Goals" value={String(w.active_goals)} />
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">🎯 Goals</h2>
          <Button size="sm" onClick={() => setShowAdd(true)}><Plus size={16} /> Thêm</Button>
        </div>

        <div className="space-y-2">
          {goals.map((g) => (
            <div key={g.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
              <div className="flex-1">
                <span className={`font-medium ${g.status === "completed" ? "line-through opacity-50" : ""}`}>{g.title}</span>
                {g.target_value != null && (
                  <div className="mt-1">
                    <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                      <div className="h-full bg-[var(--brand-primary)] rounded-full transition-all" style={{ width: `${Math.min(100, (g.current_value / g.target_value) * 100)}%` }} />
                    </div>
                    <span className="text-xs text-[var(--text-secondary)]">{g.current_value}/{g.target_value}</span>
                  </div>
                )}
                {g.deadline && <span className="text-xs text-[var(--text-secondary)] ml-2">📅 {g.deadline}</span>}
              </div>
              {g.status === "active" && (
                <button onClick={() => completeGoal(g)} className="ml-3"><CheckCircle size={18} className="text-green-500" /></button>
              )}
            </div>
          ))}
        </div>

        <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Thêm Goal">
          <div className="space-y-3">
            <Input placeholder="Mục tiêu *" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <Input placeholder="Target (số)" type="number" value={form.target_value} onChange={(e) => setForm({ ...form, target_value: e.target.value })} />
            <Input placeholder="Deadline (YYYY-MM-DD)" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
            <Button onClick={createGoal} className="w-full">Tạo Goal</Button>
          </div>
        </Modal>
      </div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div className="p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-lg)] text-center">
      <div className="text-2xl">{icon}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      <div className="text-xs text-[var(--text-secondary)]">{label}</div>
    </div>
  );
}
