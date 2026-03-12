"use client";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle } from "lucide-react";
import type { ApprovalRequest } from "@/lib/ws";

export function ApprovalDialog({ request, onApprove, onReject }: { request: ApprovalRequest | null; onApprove: () => void; onReject: () => void }) {
  if (!request) return null;
  const { plan, tools, message } = request;

  return (
    <Modal open={!!request} onClose={onReject} title="🤖 JARVIS cần xác nhận">
      <p className="text-sm text-[var(--text-secondary)] mb-3">{message}</p>

      {plan?.steps?.length > 0 && (
        <div className="space-y-1.5 mb-4">
          {plan.steps.map((s, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <span className="text-[var(--accent-green)] mt-0.5">✅</span>
              <span>{i + 1}. {s.description}</span>
            </div>
          ))}
        </div>
      )}

      {tools && tools.length > 0 && (
        <p className="text-xs text-[var(--text-tertiary)] mb-4">
          Tools: {tools.join(", ")}
        </p>
      )}

      <div className="flex gap-2 justify-end">
        <Button variant="ghost" onClick={onReject}><XCircle size={16} /> Hủy</Button>
        <Button onClick={onApprove}><CheckCircle size={16} /> Đồng ý</Button>
      </div>
    </Modal>
  );
}
