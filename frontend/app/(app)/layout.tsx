"use client";
import { Sidebar } from "@/components/layout/sidebar";
import AuthGuard from "@/components/auth-guard";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <Sidebar />
      <main id="main-content" role="main" className="flex-1 overflow-hidden animate-fade-in">{children}</main>
    </AuthGuard>
  );
}
