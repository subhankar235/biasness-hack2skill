"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-black text-white relative overflow-hidden">

      {/* Futuristic Background */}
      <div className="absolute inset-0 overflow-hidden">

        {/* Glow center */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[900px] h-[300px] bg-cyan-500/10 blur-3xl rounded-full" />

        {/* Top arc */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[1400px] h-[500px] border-t border-cyan-400/20 rounded-full" />

        {/* Bottom arc */}
        <div className="absolute bottom-16 left-1/2 -translate-x-1/2 w-[1000px] h-[380px] border-t border-cyan-500/20 rounded-full" />

        {/* Radial glow */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.08),transparent_55%)]" />

        {/* Grid fade */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />
      </div>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-28 grid md:grid-cols-2 gap-12 items-center">

        {/* Left Side */}
        <div>
          <p className="text-cyan-400 font-semibold tracking-[0.25em] mb-5 text-sm">
            FAIR AI INFRASTRUCTURE
          </p>

          <h1 className="text-6xl md:text-7xl font-bold leading-tight">
            Detect Hidden
            <span className="text-cyan-400"> Bias </span>
            In Seconds
          </h1>

          <p className="text-slate-400 text-lg mt-6 leading-8 max-w-xl">
            Upload datasets, detect sensitive columns, monitor fairness,
            run explainability analysis, and export audit-ready reports instantly.
          </p>

          <div className="flex gap-4 mt-10 flex-wrap">
            <Link
              href="/upload"
              className="px-6 py-3 rounded-xl bg-cyan-500 text-black font-bold hover:bg-cyan-400 transition"
            >
              Start Scan
            </Link>

            <Link
              href="/dashboard"
              className="px-6 py-3 rounded-xl border border-slate-700 hover:bg-slate-900 transition"
            >
              Live Dashboard
            </Link>
          </div>
        </div>

        {/* Right Card */}
        <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl">

          <div className="space-y-6">

            <Metric label="Rows Scanned" value="1.2M" />
            <Metric label="Sensitive Fields" value="3 Found" />
            <Metric label="Bias Risk" value="High" danger />

            <div>
              <p className="text-slate-400 mb-2">
                Demographic Parity Difference
              </p>

              <div className="w-full h-4 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full w-3/4 bg-orange-500 rounded-full" />
              </div>

              <p className="text-cyan-400 text-4xl font-bold mt-4">
                0.75
              </p>
            </div>

          </div>
        </div>

      </section>
    </main>
  );
}

function Metric({
  label,
  value,
  danger = false,
}: {
  label: string;
  value: string;
  danger?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>

      <span
        className={`font-semibold ${
          danger ? "text-orange-400" : "text-white"
        }`}
      >
        {value}
      </span>
    </div>
  );
}