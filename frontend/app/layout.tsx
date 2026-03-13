import type { Metadata } from "next";
import "./globals.css";
import { ToastContainer } from "@/components/ui/toast";

export const metadata: Metadata = {
  title: "MY JARVIS",
  description: "Trợ lý AI cá nhân thông minh",
  manifest: "/manifest.json",
  themeColor: "#000000",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Jarvis",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen">
        <a href="#main-content" className="skip-to-content">Bỏ qua đến nội dung</a>
        {children}
        <ToastContainer />
      </body>
    </html>
  );
}
