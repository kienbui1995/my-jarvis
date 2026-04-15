"use client";
import { useEffect, useState } from "react";
import { Wallet, Plus, Trash2, CreditCard, Receipt } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";

type Bill = { id: string; name: string; amount: number; due_day: number; category: string; enabled: boolean };
type Sub = { id: string; name: string; amount: number; frequency: string; category: string; active: boolean };

export default function FinancePage() {
  const [tab, setTab] = useState<"overview" | "bills" | "subs">("overview");
  const [dashboard, setDashboard] = useState<{ month_total: number; by_category: Record<string, number>; subscriptions_monthly: number } | null>(null);
  const [bills, setBills] = useState<Bill[]>([]);
  const [subs, setSubs] = useState<Sub[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const toast = useToast((s) => s.add);

  useEffect(() => {
    api.financeDashboard().then(setDashboard).catch(() => {});
    api.listBills().then((r) => setBills(r.data)).catch(() => {});
    api.listSubs().then((r) => setSubs(r.data)).catch(() => {});
  }, []);

  const addBill = async () => {
    await api.createBill({ name, amount: +amount, due_day: 1 });
    toast("success", `Đã thêm: ${name}`);
    setName(""); setAmount(""); setShowAdd(false);
    api.listBills().then((r) => setBills(r.data));
  };

  const tabs = [
    { id: "overview", label: "Tổng quan", icon: Wallet },
    { id: "bills", label: "Hóa đơn", icon: Receipt },
    { id: "subs", label: "Subscriptions", icon: CreditCard },
  ] as const;

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">💰 Tài chính</h1>

        <div className="flex gap-1 mb-6 bg-[var(--bg-secondary)] p-1 rounded-[var(--radius-lg)] w-fit">
          {tabs.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`px-3 py-1.5 text-sm rounded-[var(--radius-md)] transition-colors flex items-center gap-1.5 ${tab === t.id ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)]"}`}>
              <t.icon size={14} /> {t.label}
            </button>
          ))}
        </div>

        {tab === "overview" && dashboard && (
          <div className="grid grid-cols-2 gap-4">
            <Card label="Chi tiêu tháng" value={`${(dashboard.month_total / 1000).toFixed(0)}k`} icon="💸" />
            <Card label="Subscriptions/tháng" value={`${(dashboard.subscriptions_monthly / 1000).toFixed(0)}k`} icon="📱" />
            {Object.entries(dashboard.by_category).map(([cat, amt]) => (
              <Card key={cat} label={cat} value={`${(amt / 1000).toFixed(0)}k`} icon="📊" />
            ))}
          </div>
        )}

        {tab === "bills" && (
          <>
            <div className="flex justify-end mb-4">
              <Button size="sm" onClick={() => setShowAdd(true)}><Plus size={16} /> Thêm hóa đơn</Button>
            </div>
            <div className="space-y-2">
              {bills.map((b) => (
                <div key={b.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
                  <div>
                    <span className="font-medium">{b.name}</span>
                    <span className="text-[var(--text-secondary)] text-sm ml-2">ngày {b.due_day} — {b.category}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold">{b.amount?.toLocaleString()}đ</span>
                    <button onClick={() => { api.deleteBill(b.id); setBills(bills.filter((x) => x.id !== b.id)); }}><Trash2 size={14} className="text-[var(--text-secondary)]" /></button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {tab === "subs" && (
          <div className="space-y-2">
            {subs.map((s) => (
              <div key={s.id} className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)]">
                <div>
                  <span className="font-medium">{s.name}</span>
                  <span className="text-[var(--text-secondary)] text-sm ml-2">{s.frequency} — {s.category}</span>
                </div>
                <span className="font-semibold">{s.amount?.toLocaleString()}đ</span>
              </div>
            ))}
          </div>
        )}

        <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Thêm hóa đơn">
          <div className="space-y-3">
            <Input placeholder="Tên (VD: Tiền điện)" value={name} onChange={(e) => setName(e.target.value)} />
            <Input placeholder="Số tiền" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
            <Button onClick={addBill} className="w-full">Thêm</Button>
          </div>
        </Modal>
      </div>
    </div>
  );
}

function Card({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="p-4 bg-[var(--bg-secondary)] rounded-[var(--radius-lg)]">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm text-[var(--text-secondary)]">{label}</div>
    </div>
  );
}
