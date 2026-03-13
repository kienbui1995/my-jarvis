"use client";
import { Sidebar } from "@/components/layout/sidebar";
import AuthGuard from "@/components/auth-guard";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main id="main-content" role="main" className="flex-1 overflow-hidden animate-fade-in">{children}</main>
      </div>
    </AuthGuard>
  );
}
