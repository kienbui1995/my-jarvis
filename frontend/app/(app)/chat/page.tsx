"use client";
import { useEffect, useRef, useCallback, useState } from "react";
import { useChat } from "@/lib/stores/chat";
import { createWSClient, type WSMessage, type ApprovalRequest } from "@/lib/ws";
import { useTTS } from "@/lib/hooks/use-voice";
import { MessageBubble } from "@/components/chat/message-bubble";
import { ChatInput } from "@/components/chat/chat-input";
import { TypingIndicator } from "@/components/chat/typing-indicator";
import { WelcomeMessage } from "@/components/chat/welcome";
import { ApprovalDialog } from "@/components/chat/approval-dialog";
import { PlanProgress } from "@/components/chat/plan-progress";
import { Plus, MessageSquare, Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function ChatPage() {
  const { conversations, activeConvId, messages, streaming, loadConversations, switchConversation, newConversation, addUserMessage, startStreaming, appendStream, finishStreaming } = useChat();
  const wsRef = useRef<ReturnType<typeof createWSClient> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pendingRef = useRef(false);
  const [approval, setApproval] = useState<ApprovalRequest | null>(null);
  const [planProgress, setPlanProgress] = useState<{ current: number; total: number; description: string } | null>(null);
  const [voiceMode, setVoiceMode] = useState(false);
  const voiceModeRef = useRef(false);
  const autoListenRef = useRef<(() => void) | null>(null);
  const { speak: ttsSpeak } = useTTS(() => {
    // onEnd callback: auto-listen after TTS finishes in voice mode
    if (voiceModeRef.current) autoListenRef.current?.();
  });

  useEffect(() => { voiceModeRef.current = voiceMode; }, [voiceMode]);

  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" }); }, [messages, planProgress]);

  useEffect(() => { loadConversations(); }, []);

  useEffect(() => {
    if (!activeConvId) return;
    const onMsg = (msg: WSMessage) => {
      if (msg.type === "stream") {
        setPlanProgress(null);
        if (!pendingRef.current) { startStreaming(); pendingRef.current = true; }
        appendStream(msg.content);
      } else if (msg.type === "done") {
        finishStreaming(msg.content);
        pendingRef.current = false;
        setPlanProgress(null);
        if (voiceModeRef.current && msg.content) ttsSpeak(msg.content);
      } else if (msg.type === "approval_request") {
        setApproval(msg);
      } else if (msg.type === "plan_progress") {
        setPlanProgress({ current: msg.current_step, total: msg.total_steps, description: msg.step_description });
      } else if (msg.type === "error") {
        finishStreaming(msg.content || "Đã xảy ra lỗi.");
        pendingRef.current = false;
        setPlanProgress(null);
      }
    };
    wsRef.current?.close();
    wsRef.current = createWSClient(onMsg, () => {
      wsRef.current = null;
      if (pendingRef.current) {
        finishStreaming("Mất kết nối. Vui lòng thử lại.");
        pendingRef.current = false;
        setPlanProgress(null);
      }
    });
    return () => { wsRef.current?.close(); };
  }, [activeConvId]);

  const send = useCallback((content: string) => {
    if (!content.trim() || !wsRef.current?.ready) return;
    addUserMessage(content);
    wsRef.current.send(content);
  }, [addUserMessage]);

  const handleApproval = (approved: boolean) => {
    wsRef.current?.sendApproval(approved);
    setApproval(null);
    if (approved) setPlanProgress({ current: 1, total: approval?.plan?.steps?.length || 0, description: "Đang thực hiện..." });
  };

  return (
    <div className="flex h-full">
      {/* Conversation sidebar */}
      <div className="w-56 border-r border-[var(--border-default)] flex flex-col bg-[var(--bg-secondary)]">
        <div className="p-3 border-b border-[var(--border-default)]">
          <button onClick={newConversation} className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-[var(--radius-md)] bg-[var(--brand-primary)] text-white hover:opacity-90 transition">
            <Plus size={14} /> Chat mới
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((c) => (
            <button key={c.id} onClick={() => switchConversation(c.id)}
              className={`w-full text-left px-3 py-2 text-sm rounded-[var(--radius-md)] transition group ${activeConvId === c.id ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"}`}>
              <div className="flex items-center gap-1.5">
                <MessageSquare size={12} className="opacity-50 shrink-0" />
                <span className="truncate">{c.summary || `Chat ${new Date(c.started_at).toLocaleDateString("vi")}`}</span>
              </div>
              {/* Resume indicator for conversations with rolling_summary */}
              {(c as any).rolling_summary && (c as any).total_turns > 0 && activeConvId !== c.id && (
                <div className="flex items-center gap-1 mt-1 ml-4">
                  <Badge color="purple" className="text-[10px] px-1.5 py-0">
                    <Play size={8} className="mr-0.5" /> Tiếp tục
                  </Badge>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && <WelcomeMessage onQuickAction={send} />}
          {messages.map((m) => <MessageBubble key={m.id} message={m} isGrouped={false} />)}
          {streaming && <TypingIndicator />}
        </div>
        {planProgress && <PlanProgress {...planProgress} />}
        <ChatInput onSend={send} onStop={() => {}} streaming={streaming} voiceMode={voiceMode} onToggleVoiceMode={() => setVoiceMode(v => !v)} autoListenRef={autoListenRef} />
      </div>

      <ApprovalDialog request={approval} onApprove={() => handleApproval(true)} onReject={() => handleApproval(false)} />
    </div>
  );
}
