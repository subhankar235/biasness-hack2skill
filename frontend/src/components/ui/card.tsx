import React from "react";

interface CardProps {
  children?: React.ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl p-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardContent({ children, className = "" }: CardProps) {
  return <div className={className}>{children}</div>;
}

export function CardHeader({ children, className = "" }: CardProps) {
  return <div className={className}>{children}</div>;
}

export function CardTitle({ children, className = "" }: CardProps) {
  return <h3 className={className}>{children}</h3>;
}