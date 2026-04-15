"use client";
import { useEffect, useState } from "react";
import { Plus, Activity, Pill, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";

const metrics = ["sleep", "exercise", "water", "mood", "weight", "steps"] as const;
const metricIcons: Record<string, string> = { sleep: "😴", exercise: "🏃", water: "💧", mood: "😊", weight: "⚖️", steps: "👟" };
const metricUnits: Record<string, string> = { sleep: "h", exercise: "min", water: "ml", mood: "/10", weight: "kg", steps: "" };

export default function HealthPage() {
  const [tab, setTab] = useState<"log" | "meds" | "books">("log");
  const [logs, setLogs] = useState<Array<{ id: string; log_date: string; metric: string; value: number }>>([]);
  const [meds, setMeds] = useState<Array<{ id: string; name: string; dosage?: string; frequency: string }>>([]);
  const [books, setBooks] = useState<Array<{ id: string; title: string; author?: string; status: string; rating?: number }>>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [metric, setMetric] = useState("mood");
  const [value, setValue] = useState("");
  const toast = useToast((s) => s.add);

  useEffect(() => {
    api.listHealthLogs().then((r) => setLogs(r.data)).catch(() => {});
    api.listMeds().then((r) => setMeds(r.data)).catch(() => {});
    api.listBooks().then((r) => setBooks(r.data)).catch(() => {});
  }, []);

  const logHealth = async () => {
    await api.createHealthLog(metric, +value);
    toast("success", `${metricIcons[metric]} ${metric}: ${value}${metricUnits[metric]}`);
    setValue(""); setShowAdd(false);
    api.listHealthLogs().then((r) => setLogs(r.data));
  };

  const tabs = [
    { id: "log", label: "Sức khỏe", icon: Activity },
    { id: "meds", label: "Thuốc", icon: Pill },
    { id: "books", label: "Sách", icon: BookOpen },
  ] as const;

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">❤️ Sức khỏe</h1>
          {tab === "log" && <Button size="sm" onClick={() => setShowAdd(true)}><Plus size={16} /> Ghi</Button>}
        </div>

        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-[var(--radius-lg)] w-fit">
          {tabs.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] flex items-center gap-1.5 ${tab === t.id ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}>
              <t.icon size={14} /> {t.label}
            </button>
          ))}
        </div>

        {tab === "log" && (
          <div className="space-y-2">
            {logs.slice(0, 20).map((l) => (
              <div key={l.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
                <span>{metricIcons[l.metric] || "📊"} {l.metric}</span>
                <div>
                  <span className="font-semibold">{l.value}{metricUnits[l.metric]}</span>
                  <span className="text-xs text-[var(--text-secondary)] ml-2">{l.log_date}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "meds" && (
          <div className="space-y-2">
            {meds.map((m) => (
              <div key={m.id} className="p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
                <span className="font-medium">💊 {m.name}</span>
                {m.dosage && <span className="text-sm text-[var(--text-secondary)] ml-2">{m.dosage}</span>}
                <span className="text-xs ml-2 px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-full">{m.frequency}</span>
              </div>
            ))}
          </div>
        )}

        {tab === "books" && (
          <div className="space-y-2">
            {books.map((b) => (
              <div key={b.id} className="p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
                <span className="font-medium">📚 {b.title}</span>
                {b.author && <span className="text-sm text-[var(--text-secondary)] ml-2">— {b.author}</span>}
                <span className="text-xs ml-2 px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-full">{b.status}</span>
                {b.rating && <span className="ml-2">{"⭐".repeat(b.rating)}</span>}
              </div>
            ))}
          </div>
        )}

        <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Ghi sức khỏe">
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2">
              {metrics.map((m) => (
                <button key={m} onClick={() => setMetric(m)} className={`p-2 rounded-[var(--radius-md)] text-sm ${metric === m ? "bg-[var(--brand-primary)] text-white" : "bg-[var(--bg-tertiary)]"}`}>
                  {metricIcons[m]} {m}
                </button>
              ))}
            </div>
            <Input placeholder={`Giá trị (${metricUnits[metric]})`} type="number" value={value} onChange={(e) => setValue(e.target.value)} />
            <Button onClick={logHealth} className="w-full">Ghi nhận</Button>
          </div>
        </Modal>
      </div>
    </div>
  );
}
