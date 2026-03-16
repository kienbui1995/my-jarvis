import Link from "next/link";
import { MessageSquare, Brain, Mic, Shield, Zap, Globe } from "lucide-react";

const FEATURES = [
  { icon: Brain, title: "18 module AI", desc: "Smart Router, Plan-and-Execute, Memory, Vision, Voice, Proactive Engine..." },
  { icon: MessageSquare, title: "Đa kênh", desc: "Zalo Mini App, Telegram, Web — trả lời mọi nơi" },
  { icon: Mic, title: "Voice AI tiếng Việt", desc: "Nói chuyện tự nhiên, hands-free voice loop, tự động đọc trả lời" },
  { icon: Zap, title: "24 công cụ", desc: "Tasks, lịch, email, thời tiết, tin tức, OCR, browse web, Google Calendar..." },
  { icon: Shield, title: "Proactive & An toàn", desc: "Nhắc deadline, cảnh báo chi tiêu, phát hiện trùng lịch tự động" },
  { icon: Globe, title: "Hiểu bạn", desc: "Nhớ sở thích, học hành vi, cá nhân hóa — dữ liệu thuộc về bạn" },
];

const DEMO_STEPS = [
  { user: "🎤 Thời tiết Sài Gòn hôm nay?", ai: "🌤 Thời tiết Ho Chi Minh City: mưa nhỏ\n🌡 32°C (cảm giác 36°C) 💧 75% 💨 3.5 m/s" },
  { user: "Tóm tắt tin tức hôm nay", ai: "📰 3 tin nổi bật: (1) VN GDP Q1 tăng 6.8%, (2) AI agent thay đổi cách làm việc, (3) Zalo cán mốc 80M users..." },
  { user: "📎 [Ảnh hóa đơn] Ghi chi tiêu giúp tôi", ai: "📝 OCR: Cà phê Highlands 85,000đ\n💰 Đã ghi: 85,000đ — ăn uống. Hôm nay tổng chi: 350,000đ" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)] overflow-y-auto">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-6 pt-24 pb-16">
        <div className="text-6xl mb-4">🤖</div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">MY JARVIS</h1>
        <p className="text-xl text-[var(--text-secondary)] mb-2">Trợ lý AI cá nhân thông minh</p>
        <p className="text-[var(--text-tertiary)] mb-8 max-w-md">Hiểu bạn. Làm thay bạn. Dữ liệu thuộc về bạn.</p>
        <div className="flex gap-3">
          <Link href="/register" className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-medium transition">
            Dùng thử miễn phí
          </Link>
          <a href="#demo" className="px-6 py-3 border border-[var(--border-default)] hover:bg-white/5 rounded-xl font-medium transition">
            Xem demo
          </a>
        </div>
        <p className="text-xs text-[var(--text-tertiary)] mt-3">v{process.env.APP_VERSION} • Đang tìm early testers 🚀</p>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-10">Không chỉ là chatbot</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="p-5 rounded-xl border border-[var(--border-default)] bg-[var(--bg-secondary)]">
              <Icon size={24} className="text-blue-400 mb-3" />
              <h3 className="font-semibold mb-1">{title}</h3>
              <p className="text-sm text-[var(--text-secondary)]">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Demo Flow */}
      <section id="demo" className="max-w-2xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-10">Xem JARVIS làm việc</h2>
        <div className="space-y-6">
          {DEMO_STEPS.map(({ user, ai }, i) => (
            <div key={i} className="space-y-3">
              <div className="flex justify-end">
                <div className="bg-blue-600/20 text-blue-100 px-4 py-2.5 rounded-2xl rounded-br-md max-w-[80%] text-sm">{user}</div>
              </div>
              <div className="flex justify-start">
                <div className="bg-[var(--bg-secondary)] border border-[var(--border-default)] px-4 py-2.5 rounded-2xl rounded-bl-md max-w-[80%] text-sm">{ai}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="text-center px-6 py-16">
        <h2 className="text-2xl font-bold mb-3">Sẵn sàng thử?</h2>
        <p className="text-[var(--text-secondary)] mb-6">Miễn phí. Không cần thẻ. Đăng ký bằng Google trong 5 giây.</p>
        <Link href="/register" className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-medium transition">
          Bắt đầu ngay
        </Link>
      </section>

      {/* Footer */}
      <footer className="text-center text-xs text-[var(--text-tertiary)] py-8 border-t border-[var(--border-default)]">
        MY JARVIS v{process.env.APP_VERSION} • Built with ❤️ in Vietnam
      </footer>
    </div>
  );
}
