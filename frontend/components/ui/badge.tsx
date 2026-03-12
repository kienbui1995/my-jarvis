import { cn } from "@/lib/utils";

const colors = {
  default: "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
  blue: "bg-[var(--brand-subtle)] text-[var(--brand-primary)]",
  green: "bg-green-500/15 text-[var(--accent-green)]",
  yellow: "bg-yellow-500/15 text-[var(--accent-yellow)]",
  red: "bg-red-500/15 text-[var(--accent-red)]",
  orange: "bg-orange-500/15 text-[var(--accent-orange)]",
  purple: "bg-purple-500/15 text-[var(--accent-purple)]",
};

export function Badge({ color = "default", children, className }: { color?: keyof typeof colors; children: React.ReactNode; className?: string }) {
  return <span className={cn("inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full", colors[color], className)}>{children}</span>;
}
