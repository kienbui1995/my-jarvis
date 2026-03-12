"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/stores/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { GoogleLoginButton } from "@/components/auth/google-login";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuth((s) => s.login);
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/chat");
    } catch {
      setError("Email hoặc mật khẩu không đúng");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center h-full px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🤖</div>
          <h1 className="text-2xl font-bold">MY JARVIS</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Trợ lý AI cá nhân thông minh</p>
        </div>

        <form onSubmit={submit} className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-xl)] p-6 space-y-4">
          <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} error={error ? " " : undefined} required />
          <Input type="password" placeholder="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} error={error || undefined} required />
          <Button type="submit" loading={loading} className="w-full">Đăng nhập</Button>

          <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
            <div className="flex-1 h-px bg-[var(--border-default)]" />
            <span>hoặc</span>
            <div className="flex-1 h-px bg-[var(--border-default)]" />
          </div>

          <GoogleLoginButton />

          <p className="text-center text-sm text-[var(--text-secondary)]">
            Chưa có tài khoản? <Link href="/register" className="text-[var(--brand-primary)] hover:underline">Đăng ký</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
