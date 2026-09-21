import { cn } from "@/lib/utils";

export function Button({ className, variant = "default", size = "default", ...props }) {
  return <button className={cn("inline-flex items-center justify-center gap-2 font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-40", variant === "ghost" && "bg-transparent hover:bg-accent", variant === "outline" && "border border-foreground bg-transparent hover:bg-accent", size === "icon" && "size-10", className)} {...props} />;
}
