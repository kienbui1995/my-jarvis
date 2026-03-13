export type PlanStep = { step_id: number; description: string; tool_hint?: string };
export type ApprovalRequest = { type: "approval_request"; plan: { goal: string; steps: PlanStep[] }; step_num?: number; tools?: string[]; message: string };
export type PlanProgress = { type: "plan_progress"; current_step: number; total_steps: number; step_description: string };

export type WSMessage =
  | { type: "stream"; content: string }
  | { type: "done"; content: string }
  | { type: "error"; content: string }
  | ApprovalRequest
  | PlanProgress;

export function createWSClient(onMessage: (msg: WSMessage) => void, onClose?: () => void) {
  const url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws/chat";
  const token = localStorage.getItem("token") || "";
  const ws = new WebSocket(url);

  ws.onopen = () => {
    ws.send(JSON.stringify({ token }));
  };
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); } catch {}
  };
  ws.onclose = () => onClose?.();
  ws.onerror = () => onClose?.();

  return {
    send: (content: string) => { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ content })); },
    sendApproval: (approved: boolean) => { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ approved })); },
    close: () => ws.close(),
    get ready() { return ws.readyState === WebSocket.OPEN; },
  };
}
