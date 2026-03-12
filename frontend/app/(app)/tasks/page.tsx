"use client";
import { useEffect, useState } from "react";
import { Plus, Trash2, ClipboardList } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { EmptyState } from "@/components/ui/empty-state";

type Task = { id: string; title: string; status: string; priority: string; due_date: string | null };

const priorityColor = { urgent: "red", high: "orange", medium: "yellow", low: "default" } as const;
const statusIcon = { todo: "○", in_progress: "◉", done: "✓" };
const nextStatus: Record<string, string> = { todo: "in_progress", in_progress: "done", done: "todo" };
const tabs = ["all", "todo", "in_progress", "done"] as const;
const tabLabels = { all: "Tất cả", todo: "Todo", in_progress: "Đang làm", done: "Xong" };

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tab, setTab] = useState<string>("all");
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");
  const toast = useToast((s) => s.add);

  const load = () => api.listTasks(tab).then(setTasks).catch(() => {});
  useEffect(() => { load(); }, [tab]);

  const create = async () => {
    if (!title.trim()) return;
    await api.createTask(title, priority);
    toast("success", `Đã tạo: ${title}`);
    setTitle(""); setShowCreate(false); load();
  };

  const toggleStatus = async (t: Task) => {
    await api.updateTask(t.id, { status: nextStatus[t.status] || "todo" });
    load();
  };

  const remove = async (id: string) => {
    await api.deleteTask(id);
    toast("success", "Đã xóa task");
    load();
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">Tasks</h1>
          <Button size="sm" onClick={() => setShowCreate(true)}><Plus size={16} /> Tạo task</Button>
        </div>

        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-[var(--radius-lg)] w-fit">
          {tabs.map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] transition-colors ${tab === t ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
              {tabLabels[t]}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {tasks.length === 0 && <EmptyState icon={ClipboardList} title="Chưa có task nào" description="Tạo task mới hoặc nhờ Jarvis qua chat" action="Tạo task" onAction={() => setShowCreate(true)} />}
          {tasks.map((t) => (
            <div key={t.id} className={`flex items-center gap-3 p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-lg)] hover-lift transition-colors ${t.status === "done" ? "opacity-60" : ""}`}>
              <button onClick={() => toggleStatus(t)} className={`text-lg transition-colors ${t.status === "done" ? "text-[var(--accent-green)]" : t.status === "in_progress" ? "text-[var(--brand-primary)]" : "text-[var(--text-tertiary)] hover:text-[var(--brand-primary)]"}`}>
                {statusIcon[t.status as keyof typeof statusIcon] || "○"}
              </button>
              <span className={`flex-1 ${t.status === "done" ? "line-through text-[var(--text-secondary)]" : ""}`}>{t.title}</span>
              <Badge color={priorityColor[t.priority as keyof typeof priorityColor] || "default"}>{t.priority}</Badge>
              {t.due_date && <span className="text-xs text-[var(--text-secondary)]">📅 {new Date(t.due_date).toLocaleDateString("vi")}</span>}
              <button onClick={() => remove(t.id)} className="text-[var(--text-tertiary)] hover:text-red-400 transition-colors"><Trash2 size={14} /></button>
            </div>
          ))}
        </div>

        <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Tạo task mới">
          <div className="space-y-4">
            <Input placeholder="Tiêu đề task" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
            <div>
              <label className="text-sm text-[var(--text-secondary)] mb-1 block">Priority</label>
              <div className="flex gap-2">
                {["low", "medium", "high", "urgent"].map((p) => (
                  <button key={p} onClick={() => setPriority(p)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] border transition-colors ${priority === p ? "border-[var(--brand-primary)] bg-[var(--brand-subtle)]" : "border-[var(--border-default)] hover:border-[var(--border-hover)]"}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)}>Hủy</Button>
              <Button onClick={create} disabled={!title.trim()}>Tạo task</Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
}
