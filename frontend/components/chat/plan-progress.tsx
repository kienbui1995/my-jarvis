"use client";
import { Badge } from "@/components/ui/badge";

export function PlanProgress({ current, total, description }: { current: number; total: number; description: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 mx-4 mb-2 bg-[var(--bubble-tool)] rounded-[var(--radius-md)] border-l-[3px] border-[var(--accent-purple)]">
      <Badge color="purple">Bước {current}/{total}</Badge>
      <span className="text-sm text-[var(--text-secondary)] truncate">{description}</span>
      <span className="ml-auto animate-spin h-3.5 w-3.5 border-2 border-[var(--accent-purple)] border-t-transparent rounded-full" />
    </div>
  );
}
