"use client";
import { useRef, useState, useEffect, KeyboardEvent, MutableRefObject } from "react";
import { Send, Square, Paperclip, Mic, MicOff, Headphones } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSTT } from "@/lib/hooks/use-voice";

type ChatInputProps = {
  onSend: (msg: string) => void;
  onStop: () => void;
  streaming: boolean;
  voiceMode?: boolean;
  onToggleVoiceMode?: () => void;
  autoListenRef?: MutableRefObject<(() => void) | null>;
};

export function ChatInput({ onSend, onStop, streaming, voiceMode, onToggleVoiceMode, autoListenRef }: ChatInputProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const onSTTResult = (text: string) => {
    if (voiceMode) {
      // Voice mode: auto-send transcribed text
      if (text.trim()) onSend(text.trim());
    } else {
      setValue((v) => v ? v + " " + text : text);
    }
  };

  const { listening, transcribing, toggle: toggleMic } = useSTT(onSTTResult);

  // Expose toggleMic for auto-listen after TTS ends
  useEffect(() => {
    if (autoListenRef) autoListenRef.current = toggleMic;
  }, [autoListenRef, toggleMic]);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = Math.min(ref.current.scrollHeight, 150) + "px";
    }
  }, [value]);

  const send = () => {
    const trimmed = value.trim();
    if (!trimmed || streaming) return;
    onSend(trimmed);
    setValue("");
    if (ref.current) ref.current.style.height = "auto";
  };

  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="border-t border-[var(--border-default)] bg-[var(--bg-secondary)] p-3">
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        <button aria-label="Đính kèm file" className="p-2.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors shrink-0">
          <Paperclip size={20} />
        </button>
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKey}
          aria-label="Nhập tin nhắn"
          placeholder={voiceMode ? "Voice mode - nói để chat..." : "Nhập tin nhắn cho JARVIS..."}
          rows={1}
          className="flex-1 bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded-[1.25rem] px-4 py-2.5 text-base text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none focus:border-[var(--border-focus)] transition-colors"
        />
        <button
          onClick={onToggleVoiceMode}
          aria-label={voiceMode ? "Tắt voice mode" : "Bật voice mode"}
          className={cn("p-2.5 rounded-full transition-colors shrink-0", voiceMode ? "bg-[var(--brand-primary)] text-white" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]")}
        >
          <Headphones size={18} />
        </button>
        <button
          onClick={toggleMic}
          disabled={transcribing}
          aria-label={transcribing ? "Đang nhận dạng..." : listening ? "Dừng ghi âm" : "Nhập bằng giọng nói"}
          className={cn("p-2.5 rounded-full transition-colors shrink-0", transcribing ? "text-[var(--brand-primary)] animate-pulse" : listening ? "bg-[var(--accent-red)] text-white animate-pulse" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]")}
        >
          {listening ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
        <button
          onClick={streaming ? onStop : send}
          disabled={!streaming && !value.trim()}
          aria-label={streaming ? "Dừng" : "Gửi tin nhắn"}
          className={cn(
            "p-2.5 rounded-full transition-colors shrink-0",
            streaming ? "bg-[var(--accent-red)] text-white" : value.trim() ? "bg-[var(--brand-primary)] text-white" : "bg-[var(--bg-tertiary)] text-[var(--text-tertiary)]"
          )}
        >
          {streaming ? <Square size={18} /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}
