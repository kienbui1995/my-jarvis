"use client";
import { useState, useRef, useCallback } from "react";

// --- STT ---
type SpeechRecognitionType = typeof window extends { SpeechRecognition: infer T } ? T : any;

export function useSTT(onResult: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const recRef = useRef<any>(null);

  const toggle = useCallback(() => {
    if (listening) { recRef.current?.stop(); return; }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { alert("Trình duyệt không hỗ trợ nhận diện giọng nói"); return; }

    const rec = new SR();
    rec.lang = "vi-VN";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (e: any) => { onResult(e.results[0][0].transcript); };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    rec.start();
    setListening(true);
  }, [listening, onResult]);

  return { listening, toggle };
}

// --- TTS ---
let _voices: SpeechSynthesisVoice[] = [];
if (typeof window !== "undefined" && window.speechSynthesis) {
  _voices = speechSynthesis.getVoices();
  speechSynthesis.onvoiceschanged = () => { _voices = speechSynthesis.getVoices(); };
}

function getViVoice(): SpeechSynthesisVoice | null {
  return _voices.find(v => v.lang === "vi-VN")
    || _voices.find(v => v.lang.startsWith("vi"))
    || null;
}

export function useTTS() {
  const [speaking, setSpeaking] = useState(false);
  const uttRef = useRef<SpeechSynthesisUtterance | null>(null);

  const speak = useCallback((text: string) => {
    if (speaking) { speechSynthesis.cancel(); setSpeaking(false); return; }
    const clean = text.replace(/[#*`>\[\]()!_~|]/g, "").replace(/\n+/g, ". ");
    const utt = new SpeechSynthesisUtterance(clean);
    const viVoice = getViVoice();
    if (viVoice) { utt.voice = viVoice; utt.lang = viVoice.lang; }
    else { utt.lang = "vi-VN"; }
    utt.rate = 1.05;
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    uttRef.current = utt;
    setSpeaking(true);
    speechSynthesis.speak(utt);
  }, [speaking]);

  const stop = useCallback(() => { speechSynthesis.cancel(); setSpeaking(false); }, []);

  return { speaking, speak, stop };
}
