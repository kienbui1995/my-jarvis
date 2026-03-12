export function TypingIndicator() {
  return (
    <div role="status" aria-label="Jarvis đang trả lời" className="flex gap-2 mt-5">
      <div className="h-6 w-6 rounded-full bg-gradient-to-br from-[var(--brand-primary)] to-[var(--accent-purple)] flex items-center justify-center text-[10px]">🤖</div>
      <div className="bg-[var(--bubble-ai)] rounded-[var(--radius-bubble)] rounded-bl-[var(--radius-sm)] px-4 py-3 flex gap-1">
        {[0, 1, 2].map((i) => (
          <span key={i} className="h-2 w-2 rounded-full bg-[var(--text-secondary)]" style={{ animation: `bounce-dot 1s ${i * 0.15}s infinite` }} />
        ))}
      </div>
    </div>
  );
}
