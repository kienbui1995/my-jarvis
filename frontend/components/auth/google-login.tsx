"use client";
import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/stores/auth";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export function GoogleLoginButton() {
  const btnRef = useRef<HTMLDivElement>(null);
  const googleLogin = useAuth((s) => s.googleLogin);
  const router = useRouter();

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !btnRef.current) return;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response: { credential: string }) => {
          try {
            await googleLogin(response.credential);
            router.push("/chat");
          } catch {
            // silently fail — user can retry
          }
        },
      });
      window.google?.accounts.id.renderButton(btnRef.current!, {
        theme: "outline",
        size: "large",
        width: "100%",
        text: "signin_with",
        locale: "vi",
      });
    };
    document.head.appendChild(script);
    return () => { script.remove(); };
  }, [googleLogin, router]);

  if (!GOOGLE_CLIENT_ID) return null;
  return <div ref={btnRef} className="flex justify-center" />;
}
