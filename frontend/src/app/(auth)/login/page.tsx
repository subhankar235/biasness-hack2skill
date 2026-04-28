"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { fetchApi, setAuthToken } from "@/api/fetchApi";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!res.ok) {
        setError("Invalid credentials");
        return;
      }

      const data = await res.json();
      setAuthToken(data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <Card className="w-full max-w-md p-8 bg-slate-900 border-slate-800">
        <h1 className="text-2xl font-bold mb-6 text-center text-white">Login</h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-800 rounded text-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-slate-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 bg-slate-800 border border-slate-700 rounded text-white"
              required
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 bg-slate-800 border border-slate-700 rounded text-white"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-cyan-500 py-2 rounded text-black font-bold hover:bg-cyan-400"
          >
            Login
          </button>
        </form>
      </Card>
    </div>
  );
}