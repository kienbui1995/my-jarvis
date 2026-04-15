"use client";
import { useEffect, useState } from "react";
import { Plus, Trash2, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";

type Doc = { id: string; name: string; doc_type: string; doc_number?: string; expiry_date?: string };
const docTypes = ["all", "id_card", "passport", "insurance", "contract", "certificate"] as const;

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [filter, setFilter] = useState("all");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", doc_type: "id_card", doc_number: "", expiry_date: "" });
  const toast = useToast((s) => s.add);

  const load = () => api.listDocs(filter === "all" ? undefined : filter).then((r) => setDocs(r.data)).catch(() => {});
  useEffect(() => { load(); }, [filter]);

  const create = async () => {
    await api.createDoc(form);
    toast("success", `Đã thêm: ${form.name}`);
    setShowAdd(false); load();
  };

  const isExpiring = (d: string | undefined) => {
    if (!d) return false;
    const diff = (new Date(d).getTime() - Date.now()) / 86400000;
    return diff > 0 && diff < 30;
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">📄 Giấy tờ</h1>
          <Button size="sm" onClick={() => setShowAdd(true)}><Plus size={16} /> Thêm</Button>
        </div>
        <div className="flex gap-1 mb-4 flex-wrap bg-[var(--bg-secondary)] p-1 rounded-[var(--radius-lg)] w-fit">
          {docTypes.map((t) => (
            <button key={t} onClick={() => setFilter(t)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] ${filter === t ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}>
              {t === "all" ? "Tất cả" : t.replace("_", " ")}
            </button>
          ))}
        </div>
        <div className="space-y-2">
          {docs.map((d) => (
            <div key={d.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
              <div>
                <FileText size={14} className="inline mr-2" />
                <span className="font-medium">{d.name}</span>
                <span className="text-xs ml-2 px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-full">{d.doc_type}</span>
                {d.doc_number && <span className="text-sm text-[var(--text-secondary)] ml-2">#{d.doc_number}</span>}
                {isExpiring(d.expiry_date) && <span className="text-xs ml-2 text-orange-400">⚠️ Sắp hết hạn</span>}
              </div>
              <button onClick={() => { api.deleteDoc(d.id); setDocs(docs.filter((x) => x.id !== d.id)); }}><Trash2 size={14} className="text-[var(--text-secondary)]" /></button>
            </div>
          ))}
        </div>
        <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Thêm giấy tờ">
          <div className="space-y-3">
            <Input placeholder="Tên (VD: CCCD)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <select className="w-full p-2 bg-[var(--bg-tertiary)] rounded-[var(--radius-md)] text-sm" value={form.doc_type} onChange={(e) => setForm({ ...form, doc_type: e.target.value })}>
              {docTypes.filter((t) => t !== "all").map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
            </select>
            <Input placeholder="Số giấy tờ" value={form.doc_number} onChange={(e) => setForm({ ...form, doc_number: e.target.value })} />
            <Input placeholder="Ngày hết hạn (YYYY-MM-DD)" value={form.expiry_date} onChange={(e) => setForm({ ...form, expiry_date: e.target.value })} />
            <Button onClick={create} className="w-full">Thêm</Button>
          </div>
        </Modal>
      </div>
    </div>
  );
}
