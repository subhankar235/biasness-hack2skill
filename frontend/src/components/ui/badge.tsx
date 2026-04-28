import React from "react";

interface BadgeProps {
  children?: React.ReactNode;
  variant?: string;
  className?: string;
}

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  const colors = variant === "success" ? "bg-green-500" : "bg-slate-700";
  return <span className={`${colors} px-2 py-1 rounded text-xs ${className}`}>{children}</span>;
}