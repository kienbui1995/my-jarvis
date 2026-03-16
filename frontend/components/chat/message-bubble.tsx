import { cn } from "@/lib/utils";
import { AiAvatar } from "@/components/ui/avatar";
import type { Message } from "@/lib/stores/chat";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Volume2, VolumeX, ThumbsUp, ThumbsDown, Loader2 } from "lucide-react";
import { useTTS } from "@/lib/hooks/use-voice";
import { useState } from "react";
import { api } from "@/lib/api";

function FeedbackButtons({ messageId }: { messageId: string }) {
  const [sent, setSent] = useState<"up" | "down" | null>(null);

  const send = async (rating: "up" | "down") => {
    setSent(rating);
    try { await api.submitFeedback(messageId, rating); } catch {}
  };

  if (sent) return <span className="text-xs">{sent === "up" ? "👍" : "👎"}</span>;
  return (
    <>
      <button onClick={() => send("up")} aria-label="Hữu ích" className="hover:text-green-400 transition-colors"><ThumbsUp size={12} /></button>
      <button onClick={() => send("down")} aria-label="Chưa tốt" className="hover:text-red-400 transition-colors"><ThumbsDown size={12} /></button>
    </>
  );
}

function ToolCallBlock({ name, result, status }: { name: string; args: Record<string, string>; result?: string; status: string }) {
  return (
    <div className="mt-2 bg-[var(--bubble-tool)] border-l-[3px] border-[var(--accent-purple)] rounded-[var(--radius-md)] px-3 py-2">
      <div className="flex items-center gap-2 text-sm font-mono font-semibold text-[var(--accent-purple)]">
        🔧 {name}
        <span>{status === "pending" ? "⏳" : status === "done" ? "✅" : "❌"}</span>
      </div>
      {result && <p className="text-sm mt-1 text-[var(--text-secondary)]">→ {result}</p>}
    </div>
  );
}

function AiContent({ content }: { content: string }) {
  return (
    <div className="prose-jarvis">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}

export function MessageBubble({ message, isGrouped }: { message: Message; isGrouped: boolean }) {
  const isUser = message.role === "user";
  const time = message.timestamp.toLocaleTimeString("vi", { hour: "2-digit", minute: "2-digit" });
  const { speaking, loading, speak } = useTTS();

  return (
    <div className={cn("flex gap-2", isUser ? "justify-end" : "justify-start", isGrouped ? "mt-1" : "mt-5")}>
      {!isUser && !isGrouped && <AiAvatar size="sm" />}
      {!isUser && isGrouped && <div className="w-6" />}

      <div className={cn("max-w-[75%] sm:max-w-[65%]")}>
        <div className={cn(
          "px-3 py-2.5 text-base break-words",
          isUser
            ? "bg-[var(--bubble-user)] text-white rounded-[var(--radius-bubble)] rounded-br-[var(--radius-sm)] whitespace-pre-wrap"
            : "bg-[var(--bubble-ai)] text-[var(--text-primary)] rounded-[var(--radius-bubble)] rounded-bl-[var(--radius-sm)]",
          message.streaming && "streaming-cursor"
        )}>
          {isUser
            ? message.content
            : <AiContent content={message.content || (message.streaming ? "" : "...")} />
          }
          {message.toolCalls?.map((tc, i) => <ToolCallBlock key={i} {...tc} />)}
        </div>
        {!isGrouped && <p className={cn("text-xs text-[var(--text-tertiary)] mt-1 flex items-center gap-1.5", isUser ? "justify-end" : "justify-start")}>
          {time}
          {!isUser && message.content && !message.streaming && (
            <button onClick={() => speak(message.content)} aria-label={speaking ? "Dừng đọc" : "Đọc tin nhắn"} className="hover:text-[var(--text-primary)] transition-colors">
              {loading ? <Loader2 size={12} className="animate-spin" /> : speaking ? <VolumeX size={12} /> : <Volume2 size={12} />}
            </button>
          )}
          {!isUser && message.content && !message.streaming && <FeedbackButtons messageId={message.id} />}
        </p>}
      </div>
    </div>
  );
}
