export type PlanStep = { step_id: number; description: string; tool_hint?: string };
export type ApprovalRequest = { type: "approval_request"; plan: { goal: string; steps: PlanStep[] }; step_num?: number; tools?: string[]; message: string };
export type PlanProgress = { type: "plan_progress"; current_step: number; total_steps: number; step_description: string };

export type WSMessage =
  | { type: "stream"; content: string }
  | { type: "done"; content: string }
  | { type: "error"; content: string }
  | ApprovalRequest
  | PlanProgress;

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_DELAY = 1000;

export function createWSClient(onMessage: (msg: WSMessage) => void, onClose?: () => void) {
  const url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws/chat";
  const token = localStorage.getItem("token") || "";
  let ws: WebSocket;
  let reconnectAttempts = 0;
  let closed = false;
  let pendingMessages: string[] = [];

  function connect() {
    ws = new WebSocket(url);

    ws.onopen = () => {
      ws.send(JSON.stringify({ token }));
      reconnectAttempts = 0;
      // Flush queued messages
      for (const msg of pendingMessages) {
        ws.send(msg);
      }
      pendingMessages = [];
    };
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch {}
    };
    ws.onclose = () => {
      if (closed) { onClose?.(); return; }
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
        reconnectAttempts++;
        setTimeout(connect, delay);
      } else {
        onClose?.();
      }
    };
    ws.onerror = () => {};
  }

  connect();

  return {
    send: (content: string) => {
      const msg = JSON.stringify({ content });
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(msg);
      } else {
        pendingMessages.push(msg);
      }
    },
    sendApproval: (approved: boolean) => { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ approved })); },
    close: () => { closed = true; pendingMessages = []; ws.close(); },
    get ready() { return ws.readyState === WebSocket.OPEN || pendingMessages.length > 0; },
  };
}
