export function WelcomeMessage({ onQuickAction }: { onQuickAction: (msg: string) => void }) {
  const chips = ["Tạo task", "Xem lịch hôm nay", "Chi tiêu hôm nay", "Tìm kiếm"];
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-4 text-center">
      <div className="text-5xl">🤖</div>
      <h2 className="text-lg font-semibold">Chào bạn! Tôi là JARVIS</h2>
      <p className="text-sm text-[var(--text-secondary)] max-w-sm">
        Trợ lý AI cá nhân — quản lý task, lịch, chi tiêu, tìm kiếm, và ghi nhớ mọi thứ cho bạn.
      </p>
      <div className="flex flex-wrap justify-center gap-2 mt-2">
        {chips.map((c) => (
          <button key={c} onClick={() => onQuickAction(c)} className="px-3 py-1.5 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)] transition-colors">
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}
