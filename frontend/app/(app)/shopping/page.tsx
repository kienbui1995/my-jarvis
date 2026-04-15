"use client";
import { useEffect, useState } from "react";
import { Plus, ShoppingCart, Check } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";

type SList = { id: string; name: string; completed: boolean };
type SItem = { id: string; name: string; quantity: number; unit?: string; checked: boolean };

export default function ShoppingPage() {
  const [lists, setLists] = useState<SList[]>([]);
  const [activeList, setActiveList] = useState<string | null>(null);
  const [items, setItems] = useState<SItem[]>([]);
  const [newItem, setNewItem] = useState("");
  const toast = useToast((s) => s.add);

  useEffect(() => { api.listShoppingLists().then((r) => setLists(r.data)).catch(() => {}); }, []);

  useEffect(() => {
    if (activeList) api.getShoppingItems(activeList).then(setItems).catch(() => {});
  }, [activeList]);

  const addItem = async () => {
    if (!newItem.trim() || !activeList) return;
    await api.addShoppingItem(activeList, newItem);
    setNewItem("");
    api.getShoppingItems(activeList).then(setItems);
  };

  const toggle = async (itemId: string) => {
    if (!activeList) return;
    await api.toggleShoppingItem(activeList, itemId);
    setItems(items.map((i) => i.id === itemId ? { ...i, checked: !i.checked } : i));
  };

  const createList = async () => {
    const r = await api.createShoppingList("Danh sách mới");
    toast("success", "Đã tạo danh sách");
    api.listShoppingLists().then((r) => setLists(r.data));
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">🛒 Mua sắm</h1>
          <Button size="sm" onClick={createList}><Plus size={16} /> Danh sách mới</Button>
        </div>

        <div className="flex gap-2 mb-4 overflow-x-auto">
          {lists.map((l) => (
            <button key={l.id} onClick={() => setActiveList(l.id)} className={`px-4 py-2 rounded-[var(--radius-md)] text-sm whitespace-nowrap ${activeList === l.id ? "bg-[var(--brand-primary)] text-white" : "bg-[var(--bg-secondary)]"}`}>
              <ShoppingCart size={14} className="inline mr-1" /> {l.name}
            </button>
          ))}
        </div>

        {activeList && (
          <>
            <div className="flex gap-2 mb-4">
              <Input placeholder="Thêm món..." value={newItem} onChange={(e) => setNewItem(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addItem()} className="flex-1" />
              <Button onClick={addItem}>Thêm</Button>
            </div>
            <div className="space-y-1">
              {items.map((i) => (
                <button key={i.id} onClick={() => toggle(i.id)} className={`w-full flex items-center gap-3 p-3 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] text-left ${i.checked ? "opacity-50" : ""}`}>
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${i.checked ? "bg-green-500 border-green-500" : "border-[var(--text-secondary)]"}`}>
                    {i.checked && <Check size={12} className="text-white" />}
                  </div>
                  <span className={i.checked ? "line-through" : ""}>{i.name}</span>
                  {i.quantity > 1 && <span className="text-sm text-[var(--text-secondary)]">x{i.quantity}</span>}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
