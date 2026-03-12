import { cn } from "@/lib/utils";
import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & { error?: string };

export const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, ...props }, ref) => (
  <div className="w-full">
    <input
      ref={ref}
      className={cn(
        "w-full bg-[var(--bg-tertiary)] border rounded-[var(--radius-md)] px-3 py-3 text-base text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] transition-colors duration-150 focus:outline-none focus:border-[var(--border-focus)] focus:shadow-[var(--shadow-glow)]",
        error ? "border-[var(--accent-red)]" : "border-[var(--border-default)]",
        className
      )}
      {...props}
    />
    {error && <p className="mt-1 text-xs text-[var(--accent-red)]">{error}</p>}
  </div>
));
Input.displayName = "Input";

type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded-[var(--radius-md)] px-3 py-3 text-base text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none transition-colors duration-150 focus:outline-none focus:border-[var(--border-focus)]",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
