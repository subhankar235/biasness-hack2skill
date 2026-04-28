import React from "react";

interface SelectProps {
  children?: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
}

export function Select({ children, value, onValueChange, className = "" }: SelectProps) {
  return (
    <select value={value} onChange={(e) => onValueChange?.(e.target.value)} className={`w-full px-3 py-2 rounded bg-white text-black ${className}`}>
      {children}
    </select>
  );
}

export function SelectContent({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

export function SelectItem({ children, value }: { children?: React.ReactNode; value: string; className?: string }) {
  return <option value={value}>{children}</option>;
}

export function SelectTrigger({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

export function SelectValue({ placeholder, className = "" }: { placeholder?: string; className?: string }) {
  return <span className={className}>{placeholder}</span>;
}