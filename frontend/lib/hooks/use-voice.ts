"use client";
import { useState, useRef, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// --- STT: MediaRecorder → backend /voice/transcribe → fallback Web Speech API ---

export function useSTT(onResult: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const fallbackWebSpeech = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.lang = "vi-VN";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (e: any) => onResult(e.results[0][0].transcript);
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    rec.start();
    setListening(true);
  }, [onResult]);

  const sendToBackend = useCallback(async (blob: Blob) => {
    setTranscribing(true);
    try {
      const form = new FormData();
      form.append("audio", blob, "recording.webm");
      const res = await fetch(`${API}/voice/transcribe`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: form,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.text) onResult(data.text);
    } catch {
      // Fallback: re-record with Web Speech API
      fallbackWebSpeech();
    } finally {
      setTranscribing(false);
    }
  }, [onResult, fallbackWebSpeech]);

  const toggle = useCallback(async () => {
    if (listening) {
      recorderRef.current?.stop();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        setListening(false);
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size > 0) sendToBackend(blob);
      };

      recorderRef.current = recorder;
      recorder.start();
      setListening(true);
    } catch {
      // MediaRecorder not available — fallback to Web Speech API
      fallbackWebSpeech();
    }
  }, [listening, sendToBackend, fallbackWebSpeech]);

  return { listening, transcribing, toggle };
}

// --- TTS: backend /voice/speak → fallback Piper WASM ---

export function useTTS(onEnd?: () => void) {
  const [speaking, setSpeaking] = useState(false);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const onEndRef = useRef(onEnd);
  onEndRef.current = onEnd;

  const speak = useCallback(async (text: string) => {
    if (speaking) {
      audioRef.current?.pause();
      setSpeaking(false);
      return;
    }

    const clean = text.replace(/[#*`>\[\]()!_~|]/g, "").replace(/\n+/g, ". ").trim();
    if (!clean) return;

    const handleEnded = (url: string) => () => {
      setSpeaking(false);
      URL.revokeObjectURL(url);
      onEndRef.current?.();
    };

    setLoading(true);
    try {
      const params = new URLSearchParams({ text: clean.slice(0, 2000), voice: "vi-VN" });
      const res = await fetch(`${API}/voice/speak?${params}`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = handleEnded(url);
      audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      setSpeaking(true);
      setLoading(false);
      await audio.play();
    } catch {
      // Fallback to Piper WASM TTS
      setLoading(false);
      try {
        const { predict } = await import("@mintplex-labs/piper-tts-web");
        const blob = await predict({ voiceId: "vi_VN-vais1000-medium", text: clean });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = handleEnded(url);
        audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
        setSpeaking(true);
        await audio.play();
      } catch {
        setSpeaking(false);
      }
    }
  }, [speaking]);

  const stop = useCallback(() => {
    audioRef.current?.pause();
    setSpeaking(false);
  }, []);

  return { speaking, loading, speak, stop };
}
