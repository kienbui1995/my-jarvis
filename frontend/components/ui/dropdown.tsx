"use client";
import { useState, useRef, useEffect, useCallback, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type Item = { label: string; value: string; icon?: ReactNode };

export function Dropdown({ items, value, onChange, placeholder = "Chọn...", className }: {
  items: Item[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [focus, setFocus] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);
  const selected = items.find((i) => i.value === value);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const onKey = useCallback((e: React.KeyboardEvent) => {
    if (!open && (e.key === "Enter" || e.key === " " || e.key === "ArrowDown")) { e.preventDefault(); setOpen(true); setFocus(0); return; }
    if (!open) return;
    switch (e.key) {
      case "Escape": setOpen(false); break;
      case "ArrowDown": e.preventDefault(); setFocus((f) => Math.min(f + 1, items.length - 1)); break;
      case "ArrowUp": e.preventDefault(); setFocus((f) => Math.max(f - 1, 0)); break;
      case "Enter": if (focus >= 0) { onChange(items[focus].value); setOpen(false); } break;
    }
  }, [open, focus, items, onChange]);

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => { setOpen(!open); setFocus(-1); }}
        onKeyDown={onKey}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 text-sm bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-md)] hover:border-[var(--border-hover)] transition-colors"
      >
        <span className={selected ? "text-[var(--text-primary)]" : "text-[var(--text-tertiary)]"}>
          {selected ? <>{selected.icon} {selected.label}</> : placeholder}
        </span>
        <span className={`text-xs transition-transform ${open ? "rotate-180" : ""}`}>▾</span>
      </button>

      {open && (
        <ul role="listbox" className="absolute z-50 mt-1 w-full bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-[var(--radius-md)] py-1 shadow-lg max-h-48 overflow-y-auto">
          {items.map((item, i) => (
            <li
              key={item.value}
              role="option"
              aria-selected={item.value === value}
              className={cn(
                "px-3 py-2 text-sm cursor-pointer flex items-center gap-2 transition-colors",
                i === focus && "bg-[var(--bg-tertiary)]",
                item.value === value && "text-[var(--brand-primary)]",
              )}
              onMouseEnter={() => setFocus(i)}
              onClick={() => { onChange(item.value); setOpen(false); }}
            >
              {item.icon}{item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
