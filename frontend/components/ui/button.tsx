import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

const variants = {
  primary: "bg-[var(--brand-primary)] text-white hover:bg-[var(--brand-hover)]",
  secondary: "bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]",
  ghost: "bg-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]",
  danger: "bg-[var(--accent-red)] text-white hover:bg-red-600",
};

const sizes = {
  sm: "text-sm py-1.5 px-3",
  md: "text-base py-2.5 px-4",
  lg: "text-lg py-3 px-6",
  icon: "p-2",
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  loading?: boolean;
};

export const Button = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn("inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] font-medium transition-colors duration-150 press-scale focus-ring-pulse disabled:opacity-50 disabled:pointer-events-none", variants[variant], sizes[size], className)}
      {...props}
    >
      {loading ? <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> : children}
    </button>
  )
);
Button.displayName = "Button";
