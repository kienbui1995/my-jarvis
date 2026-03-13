"use client";
import { useState, useRef, useCallback } from "react";

let _ready = false;
let _loading = false;
const _waiters: Array<() => void> = [];

async function ensureLoaded() {
  if (_ready) return;
  if (_loading) return new Promise<void>(r => _waiters.push(r));
  _loading = true;
  // Preload triggers model download + WASM init
  const { predict } = await import("@mintplex-labs/piper-tts-web");
  _ready = true;
  _loading = false;
  _waiters.forEach(fn => fn());
  _waiters.length = 0;
}

export function usePiperTTS() {
  const [speaking, setSpeaking] = useState(false);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speak = useCallback(async (text: string) => {
    if (speaking) {
      audioRef.current?.pause();
      setSpeaking(false);
      return;
    }

    const clean = text.replace(/[#*`>\[\]()!_~|]/g, "").replace(/\n+/g, ". ").trim();
    if (!clean) return;

    setLoading(true);
    try {
      await ensureLoaded();
      const { predict } = await import("@mintplex-labs/piper-tts-web");
      const blob = await predict({
        voiceId: "vi_VN-vais1000-medium",
        text: clean,
      });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      setSpeaking(true);
      setLoading(false);
      await audio.play();
    } catch (e) {
      console.error("Piper TTS error:", e);
      setLoading(false);
      setSpeaking(false);
    }
  }, [speaking]);

  const stop = useCallback(() => {
    audioRef.current?.pause();
    setSpeaking(false);
  }, []);

  return { speaking, loading, speak, stop };
}
