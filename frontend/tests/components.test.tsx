import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "@/components/ui/button";
import { ChatInput } from "@/components/chat/chat-input";
import { WelcomeMessage } from "@/components/chat/welcome";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("disabled when loading", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("shows spinner when loading", () => {
    const { container } = render(<Button loading>Save</Button>);
    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Button variant="danger">Delete</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-[var(--accent-red)]");
  });
});

describe("ChatInput", () => {
  it("calls onSend with trimmed value on Enter", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={vi.fn()} streaming={false} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "  hello  " } });
    fireEvent.keyDown(textarea, { key: "Enter" });

    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("does not send empty message", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={vi.fn()} streaming={false} />);

    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    expect(onSend).not.toHaveBeenCalled();
  });

  it("Shift+Enter does not send", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={vi.fn()} streaming={false} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

    expect(onSend).not.toHaveBeenCalled();
  });

  it("send button disabled when empty", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} streaming={false} />);
    expect(screen.getByLabelText("Gửi tin nhắn")).toBeDisabled();
  });

  it("shows stop button when streaming", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} streaming={true} />);
    expect(screen.getByLabelText("Dừng")).toBeInTheDocument();
  });

  it("calls onStop when streaming and stop clicked", () => {
    const onStop = vi.fn();
    render(<ChatInput onSend={vi.fn()} onStop={onStop} streaming={true} />);
    fireEvent.click(screen.getByLabelText("Dừng"));
    expect(onStop).toHaveBeenCalled();
  });

  it("has accessible label on textarea", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} streaming={false} />);
    expect(screen.getByLabelText("Nhập tin nhắn")).toBeInTheDocument();
  });
});

describe("WelcomeMessage", () => {
  it("renders greeting", () => {
    render(<WelcomeMessage onQuickAction={vi.fn()} />);
    expect(screen.getByText("Chào bạn! Tôi là JARVIS")).toBeInTheDocument();
  });

  it("renders quick action chips", () => {
    render(<WelcomeMessage onQuickAction={vi.fn()} />);
    expect(screen.getByText("Tạo task")).toBeInTheDocument();
    expect(screen.getByText("Xem lịch hôm nay")).toBeInTheDocument();
  });

  it("calls onQuickAction when chip clicked", () => {
    const handler = vi.fn();
    render(<WelcomeMessage onQuickAction={handler} />);
    fireEvent.click(screen.getByText("Tạo task"));
    expect(handler).toHaveBeenCalledWith("Tạo task");
  });
});
