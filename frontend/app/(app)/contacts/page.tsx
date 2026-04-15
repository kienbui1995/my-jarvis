"use client";
import { useEffect, useState } from "react";
import { Plus, Trash2, Search } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";

type Contact = { id: string; name: string; phone?: string; email?: string; relationship?: string; birthday?: string; company?: string };

const relTypes = ["all", "family", "friend", "colleague", "client"] as const;

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [filter, setFilter] = useState("all");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", email: "", relationship: "friend", birthday: "", company: "" });
  const toast = useToast((s) => s.add);

  const load = () => api.listContacts(filter === "all" ? undefined : filter).then((r) => setContacts(r.data)).catch(() => {});
  useEffect(() => { load(); }, [filter]);

  const create = async () => {
    await api.createContact(form);
    toast("success", `Đã thêm: ${form.name}`);
    setForm({ name: "", phone: "", email: "", relationship: "friend", birthday: "", company: "" });
    setShowAdd(false); load();
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">👥 Danh bạ</h1>
          <Button size="sm" onClick={() => setShowAdd(true)}><Plus size={16} /> Thêm</Button>
        </div>

        <div className="flex gap-1 mb-4 bg-[var(--bg-secondary)] p-1 rounded-[var(--radius-lg)] w-fit">
          {relTypes.map((t) => (
            <button key={t} onClick={() => setFilter(t)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] transition-colors ${filter === t ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}>
              {t === "all" ? "Tất cả" : t}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {contacts.map((c) => (
            <div key={c.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
              <div>
                <span className="font-medium">{c.name}</span>
                {c.relationship && <span className="text-xs ml-2 px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-full">{c.relationship}</span>}
                <div className="text-sm text-[var(--text-secondary)]">
                  {c.phone && <span>{c.phone}</span>}
                  {c.company && <span className="ml-2">🏢 {c.company}</span>}
                  {c.birthday && <span className="ml-2">🎂 {c.birthday}</span>}
                </div>
              </div>
              <button onClick={() => { api.deleteContact(c.id); setContacts(contacts.filter((x) => x.id !== c.id)); }}><Trash2 size={14} className="text-[var(--text-secondary)]" /></button>
            </div>
          ))}
        </div>

        <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Thêm liên hệ">
          <div className="space-y-3">
            <Input placeholder="Tên *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input placeholder="SĐT" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            <Input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <Input placeholder="Sinh nhật (YYYY-MM-DD)" value={form.birthday} onChange={(e) => setForm({ ...form, birthday: e.target.value })} />
            <Input placeholder="Công ty" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <Button onClick={create} className="w-full">Thêm</Button>
          </div>
        </Modal>
      </div>
    </div>
  );
}
