"use client";

import { useState, useCallback } from "react";

interface ToastParams {
  title?: string;
  description?: string;
  variant?: string;
}

export function toast(params: ToastParams) {
  console.log("Toast:", params);
  alert(params.title || params.description || "Toast");
}

export function useToast() {
  const [toasts, setToasts] = useState<Array<{ id: number; title: string; description?: string }>>([]);

  const addToast = useCallback((params: ToastParams) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, title: params.title || "", description: params.description }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  return { toasts, toast: addToast };
}