import React from "react";

interface ButtonProps {
  children?: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

export function Button({ children, onClick, className = "", disabled = false }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded font-semibold ${className} ${disabled ? "opacity-50" : ""}`}
    >
      {children}
    </button>
  );
}