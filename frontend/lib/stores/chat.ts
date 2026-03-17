import { create } from "zustand";
import { api } from "@/lib/api";

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  streaming?: boolean;
  toolCalls?: Array<{ name: string; args: Record<string, string>; result?: string; status: "pending" | "done" | "error" }>;
};

type Conversation = { id: string; summary: string | null; started_at: string; message_count: number; rolling_summary?: string; total_turns?: number };

type ChatStore = {
  conversations: Conversation[];
  activeConvId: string | null;
  messages: Message[];
  streaming: boolean;
  loadConversations: () => Promise<void>;
  switchConversation: (id: string) => Promise<void>;
  newConversation: () => Promise<void>;
  addUserMessage: (content: string) => void;
  startStreaming: () => void;
  appendStream: (chunk: string) => void;
  finishStreaming: (fullContent: string) => void;
};

let msgId = 0;

export const useChat = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConvId: null,
  messages: [],
  streaming: false,

  loadConversations: async () => {
    try {
      const convs = await api.listConversations();
      set({ conversations: convs });
      if (convs.length > 0 && !get().activeConvId) {
        await get().switchConversation(convs[0].id);
      } else if (convs.length === 0 && !get().activeConvId) {
        await get().newConversation();
      }
    } catch {}
  },

  switchConversation: async (id) => {
    set({ activeConvId: id, messages: [], streaming: false });
    try {
      const msgs = await api.getMessages(id);
      set({
        messages: msgs.map((m) => ({ id: m.id, role: m.role as "user" | "assistant", content: m.content, timestamp: new Date(m.created_at) })),
      });
    } catch {}
  },

  newConversation: async () => {
    try {
      const { id } = await api.createConversation();
      set((s) => ({
        activeConvId: id,
        messages: [],
        conversations: [{ id, summary: null, started_at: new Date().toISOString(), message_count: 0 }, ...s.conversations],
      }));
    } catch {}
  },

  addUserMessage: (content) =>
    set((s) => ({ messages: [...s.messages, { id: `u${++msgId}`, role: "user", content, timestamp: new Date() }] })),
  startStreaming: () =>
    set((s) => ({ streaming: true, messages: [...s.messages, { id: `a${++msgId}`, role: "assistant", content: "", timestamp: new Date(), streaming: true }] })),
  appendStream: (chunk) =>
    set((s) => ({ messages: s.messages.map((m, i) => (i === s.messages.length - 1 && m.streaming ? { ...m, content: m.content + chunk } : m)) })),
  finishStreaming: (fullContent) =>
    set((s) => ({ streaming: false, messages: s.messages.map((m, i) => (i === s.messages.length - 1 ? { ...m, content: fullContent, streaming: false } : m)) })),
}));
