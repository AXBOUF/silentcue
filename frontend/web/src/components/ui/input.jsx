import { cn } from "@/lib/utils";

export function Input({ className, ...props }) {
  return <input className={cn("w-full border border-input bg-background px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-primary", className)} {...props} />;
}
