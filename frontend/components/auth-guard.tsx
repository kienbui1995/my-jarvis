"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/stores/auth";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, loadUser } = useAuth();
  const router = useRouter();

  useEffect(() => { loadUser(); }, []);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) return <div className="flex items-center justify-center h-full text-[var(--text-secondary)]">Đang tải...</div>;
  if (!user) return null;
  return <>{children}</>;
}
