"use client";
import { create } from "zustand";
import { cn } from "@/lib/utils";
import { useEffect } from "react";
import { CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react";

type Toast = { id: number; type: "success" | "error" | "warning" | "info"; message: string };
type ToastStore = { toasts: Toast[]; add: (type: Toast["type"], message: string) => void; remove: (id: number) => void };

let toastId = 0;
export const useToast = create<ToastStore>((set) => ({
  toasts: [],
  add: (type, message) => {
    const id = ++toastId;
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), 4000);
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

const icons = { success: CheckCircle, error: XCircle, warning: AlertTriangle, info: Info };
const borders = { success: "border-l-[var(--accent-green)]", error: "border-l-[var(--accent-red)]", warning: "border-l-[var(--accent-yellow)]", info: "border-l-[var(--brand-primary)]" };

export function ToastContainer() {
  const toasts = useToast((s) => s.toasts);
  return (
    <div role="status" aria-live="polite" className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => {
        const Icon = icons[t.type];
        return (
          <div key={t.id} className={cn("flex items-center gap-3 bg-[var(--bg-elevated)] border border-[var(--border-default)] border-l-[3px] rounded-[var(--radius-lg)] shadow-[var(--shadow-md)] px-4 py-3 min-w-[280px] animate-slide-in-right", borders[t.type])}>
            <Icon size={18} />
            <span className="text-sm">{t.message}</span>
          </div>
        );
      })}
    </div>
  );
}
