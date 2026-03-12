"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/stores/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { GoogleLoginButton } from "@/components/auth/google-login";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const register = useAuth((s) => s.register);
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, name);
      router.push("/onboarding");
    } catch {
      setError("Không thể đăng ký. Email có thể đã tồn tại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center h-full px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🤖</div>
          <h1 className="text-2xl font-bold">Tạo tài khoản</h1>
        </div>

        <form onSubmit={submit} className="bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-[var(--radius-xl)] p-6 space-y-4">
          <Input placeholder="Tên hiển thị" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input type="password" placeholder="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} error={error || undefined} required minLength={6} />
          <Button type="submit" loading={loading} className="w-full">Đăng ký</Button>

          <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
            <div className="flex-1 h-px bg-[var(--border-default)]" />
            <span>hoặc</span>
            <div className="flex-1 h-px bg-[var(--border-default)]" />
          </div>

          <GoogleLoginButton />

          <p className="text-center text-sm text-[var(--text-secondary)]">
            Đã có tài khoản? <Link href="/login" className="text-[var(--brand-primary)] hover:underline">Đăng nhập</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
