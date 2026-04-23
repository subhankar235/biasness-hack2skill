"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function HomePage() {
  const stats = [
    { label: "Datasets Audited", value: "12K+" },
    { label: "Bias Flags Raised", value: "3.4K+" },
    { label: "Avg Scan Time", value: "4 sec" },
  ];

  return (
    <main className="min-h-screen bg-slate-950 text-white overflow-hidden">
      <section className="max-w-7xl mx-auto px-6 py-24">

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <p className="text-cyan-400 font-semibold uppercase tracking-widest mb-4">
            Trust Layer For AI Decisions
          </p>

          <h1 className="text-6xl md:text-7xl font-bold leading-tight">
            Detect Hidden Bias
            <span className="text-cyan-400"> Before Deployment</span>
          </h1>

          <p className="text-slate-300 mt-6 max-w-3xl mx-auto text-lg leading-8">
            FairLens audits datasets and ML decisions for unfair outcomes,
            sensitive attribute risks, and demographic disparity in seconds.
          </p>

          <div className="mt-10 flex justify-center gap-4 flex-wrap">
            <Link
              href="/upload"
              className="px-7 py-3 rounded-xl bg-cyan-500 text-black font-semibold hover:bg-cyan-400 transition"
            >
              Start Free Scan
            </Link>

            <Link
              href="/dashboard"
              className="px-7 py-3 rounded-xl border border-slate-700 hover:border-cyan-400 transition"
            >
              Live Dashboard
            </Link>
          </div>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6 mt-20">
          {stats.map((item, i) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.15 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center"
            >
              <h3 className="text-4xl font-bold text-cyan-400">
                {item.value}
              </h3>
              <p className="text-slate-400 mt-2">{item.label}</p>
            </motion.div>
          ))}
        </div>
      </section>
    </main>
  );
}