"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API = "http://127.0.0.1:8000";

export default function ExplainabilityPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const biasFlags = data?.bias_flags || [];

  async function runExplainability() {
    const input = document.getElementById(
      "fileInput"
    ) as HTMLInputElement;

    if (!input.files?.[0]) {
      alert("Choose dataset first");
      return;
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);

    setLoading(true);

    try {
      const res = await fetch(
        `${API}/api/v1/models/explain`,
        {
          method: "POST",
          body: formData,
        }
      );

      const json = await res.json();
      setData(json);
    } catch {
      alert("Explainability failed");
    }

    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto">

        <h1 className="text-5xl font-bold mb-3">
          SHAP Bias Explainability
        </h1>

        <p className="text-slate-400 mb-8">
          Understand which features drive decisions.
        </p>

        <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 mb-8 flex gap-4 flex-wrap">
          <input
            id="fileInput"
            type="file"
            className="text-sm"
          />

          <button
            onClick={runExplainability}
            disabled={loading}
            className="px-5 py-3 rounded-xl bg-cyan-500 text-black font-bold"
          >
            {loading ? "Running..." : "Run Explainability"}
          </button>
        </div>

        {data && (
          <>
            <div className="grid md:grid-cols-2 gap-6 mb-8">

              <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Top Feature Importance
                </h2>

                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.top_features}>
                      <XAxis dataKey="feature" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip />
                      <Bar dataKey="importance" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Bias Flags
                </h2>

                <div className="space-y-4">
                  {biasFlags.length > 0 ? biasFlags.map(
                    (item: string, i: number) => (
                      <div
                        key={i}
                        className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300"
                      >
                        {item}
                      </div>
                    )
                  ) : <p className="text-slate-400">No bias flags detected</p>}
                </div>
              </section>

            </div>

            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-xl font-semibold mb-4">
                AI Insight
              </h2>

              <p className="text-slate-300 leading-7">
                Income is the strongest predictive feature. Gender also shows measurable influence, indicating potential bias leakage in historical decisions.
              </p>
            </section>
          </>
        )}
      </div>
    </main>
  );
}