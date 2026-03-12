import { cn } from "@/lib/utils";

const sizeMap = { sm: "h-6 w-6 text-[10px]", md: "h-8 w-8 text-xs", lg: "h-10 w-10 text-sm", xl: "h-14 w-14 text-lg" };

export function Avatar({ name, src, size = "md", className }: { name?: string; src?: string; size?: keyof typeof sizeMap; className?: string }) {
  const initials = name?.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "?";
  return (
    <div className={cn("rounded-full flex items-center justify-center font-semibold text-white shrink-0", sizeMap[size], !src && "bg-gradient-to-br from-[var(--brand-primary)] to-[var(--accent-purple)]", className)}>
      {src ? <img src={src} alt={name} className="h-full w-full rounded-full object-cover" /> : initials}
    </div>
  );
}

export function AiAvatar({ size = "md" }: { size?: keyof typeof sizeMap }) {
  return <div className={cn("rounded-full flex items-center justify-center shrink-0 bg-gradient-to-br from-[var(--brand-primary)] to-[var(--accent-purple)]", sizeMap[size])}>🤖</div>;
}
