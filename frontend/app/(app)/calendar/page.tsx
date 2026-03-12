"use client";
import { useEffect, useState } from "react";
import { Plus, CalendarDays } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { SkeletonCard } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

type Event = { id: string; title: string; start_time: string; location: string };
const colors = ["border-l-blue-500", "border-l-purple-500", "border-l-green-500", "border-l-orange-500", "border-l-red-500"];

export default function CalendarPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("");
  const [location, setLocation] = useState("");
  const toast = useToast((s) => s.add);
  const today = new Date();

  const load = () => api.listEvents().then(setEvents).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!title.trim() || !startTime) return;
    await api.createEvent(title, new Date(startTime).toISOString(), undefined, location);
    toast("success", `Đã tạo: ${title}`);
    setTitle(""); setStartTime(""); setLocation(""); setShowCreate(false); load();
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">Lịch</h1>
          <Button size="sm" onClick={() => setShowCreate(true)}><Plus size={16} /> Tạo sự kiện</Button>
        </div>

        <p className="text-sm text-[var(--text-secondary)] mb-4">
          Hôm nay — {today.toLocaleDateString("vi", { weekday: "long", day: "numeric", month: "numeric", year: "numeric" })}
        </p>

        <div className="space-y-2">
          {loading && <>{[1,2,3].map(i => <SkeletonCard key={i} />)}</>}
          {!loading && events.length === 0 && <EmptyState icon={CalendarDays} title="Chưa có sự kiện" description="Tạo sự kiện mới hoặc nhờ Jarvis qua chat" action="Tạo sự kiện" onAction={() => setShowCreate(true)} />}
          {events.map((e, i) => {
            const t = new Date(e.start_time);
            return (
              <div key={e.id} className={`flex gap-4 p-3 bg-[var(--bg-secondary)] border border-[var(--border-default)] ${colors[i % colors.length]} border-l-[3px] rounded-[var(--radius-lg)] hover-lift`}>
                <span className="text-sm text-[var(--text-secondary)] w-12 shrink-0">{t.toLocaleTimeString("vi", { hour: "2-digit", minute: "2-digit" })}</span>
                <div>
                  <p className="font-medium text-sm">{e.title}</p>
                  {e.location && <p className="text-xs text-[var(--text-secondary)]">{e.location}</p>}
                </div>
              </div>
            );
          })}
        </div>

        <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Tạo sự kiện">
          <div className="space-y-4">
            <Input placeholder="Tiêu đề" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
            <div>
              <label className="text-sm text-[var(--text-secondary)] mb-1 block">Thời gian</label>
              <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-primary)] text-[var(--text-primary)]" />
            </div>
            <Input placeholder="Địa điểm (tùy chọn)" value={location} onChange={(e) => setLocation(e.target.value)} />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setShowCreate(false)}>Hủy</Button>
              <Button onClick={create} disabled={!title.trim() || !startTime}>Tạo</Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
}
