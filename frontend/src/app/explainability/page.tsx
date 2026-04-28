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
  const [selectedRow, setSelectedRow] = useState(0);

  const biasFlags = data?.bias_flags || [];
  const localExplanations = data?.local_explanations || [];

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
      console.log("SHAP Result:", json);
      setData(json);
    } catch (err) {
      console.error(err);
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

        {data ? (
          <>
            {/* 1. Feature Importance (Global) */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">

              <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Feature Importance (Global)
                </h2>

                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.top_features}>
                      <XAxis dataKey="feature" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip />
                      <Bar dataKey="importance" fill="#06b6d4" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>

              {/* 5. Bias Flags with % */}
              <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Bias Flags
                </h2>

                <div className="space-y-4">
                  {biasFlags.length > 0 && biasFlags[0].impact !== 0 ? biasFlags.map(
                    (flag: any, i: number) => (
                      <div
                        key={i}
                        className="bg-red-500/10 border border-red-500/30 rounded-xl p-4"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-red-300 font-semibold">
                            {flag.type?.toUpperCase() || "BIAS"}
                          </span>
                          <span className="text-red-400 font-bold">
                            {flag.impact?.toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-red-200 text-sm mt-2">
                          {flag.message}
                        </p>
                      </div>
                    )
                  ) : (
                    <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-green-300">
                      No significant bias detected in this dataset.
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* 3. Local Explanation + 4. Prediction Breakdown */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6 mb-8">
              <h2 className="text-xl font-semibold mb-4">
                Local Explanation (Row {selectedRow})
              </h2>

              {localExplanations.length > 0 && (
                <>
                  {/* Row selector */}
                  <div className="flex gap-2 mb-4">
                    {localExplanations.map((_: any, i: number) => (
                      <button
                        key={i}
                        onClick={() => setSelectedRow(i)}
                        className={`px-3 py-1 rounded ${
                          selectedRow === i
                            ? "bg-cyan-500 text-black"
                            : "bg-slate-700 text-white"
                        }`}
                      >
                        Row {i}
                      </button>
                    ))}
                  </div>

                  {/* Prediction Breakdown */}
                  <div className="bg-slate-800 rounded-xl p-4 mb-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <p className="text-slate-400 text-sm">Base Value</p>
                        <p className="text-xl font-bold text-yellow-400">
                          {localExplanations[selectedRow]?.base_value?.toFixed(4)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">+ Contributions</p>
                        <p className="text-xl font-bold text-green-400">
                          +(sum of positive)
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-sm">Final Prediction</p>
                        <p className="text-xl font-bold text-cyan-400">
                          {localExplanations[selectedRow]?.prediction?.toFixed(4)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Per-feature contributions with green/red */}
                  <div className="space-y-2">
                    {localExplanations[selectedRow]?.contributions?.map(
                      (contrib: any, i: number) => (
                        <div
                          key={i}
                          className="flex items-center gap-3"
                        >
                          <span className="w-24 text-sm truncate">
                            {contrib.feature}
                          </span>
                          <div className="flex-1 bg-slate-700 rounded h-6 relative overflow-hidden">
                            <div
                              className={`absolute top-0 h-full ${
                                contrib.positive
                                  ? "bg-green-500"
                                  : "bg-red-500"
                              }`}
                              style={{
                                width: `${Math.min(
                                  Math.abs(contrib.value) * 50,
                                  100
                                )}%`,
                                left: contrib.positive
                                  ? "50%"
                                  : `${50 - Math.abs(contrib.value) * 50}%`,
                              }}
                            />
                          </div>
                          <span className="w-20 text-right text-sm">
                            {contrib.value > 0 ? "+" : ""}
                            {contrib.value}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </>
              )}
            </section>

            {/* 6. AI Insight */}
            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-xl font-semibold mb-4">
                AI Insight
              </h2>

              <div className="text-slate-300 leading-7 space-y-2">
                {data?.top_features?.[0] ? (
                  <>
                    <p>
                      <span className="font-semibold text-cyan-400">
                        {data.top_features[0].feature}
                      </span> is the strongest predictive feature 
                      ({(data.top_features[0].importance * 100).toFixed(1)}% importance).
                      {data.top_features[1] && (
                        <> Followed by <span className="text-cyan-400">{data.top_features[1].feature}</span> ({(data.top_features[1].importance * 100).toFixed(1)}%).</>
                      )}
                    </p>
                    {biasFlags.some((f: any) => f.impact > 0) && (
                      <p className="text-red-300">
                        Warning: Potential bias detected via {biasFlags.filter((f: any) => f.impact > 0).map((f: any) => f.type).join(", ")}.
                        Consider reweighing or threshold optimization.
                      </p>
                    )}
                    {!biasFlags.some((f: any) => f.impact > 0) && (
                      <p className="text-green-300">
                        Model appears fair - no significant bias from protected attributes.
                      </p>
                    )}
                  </>
                ) : (
                  <p>No significant features found in the dataset.</p>
                )}
              </div>
            </section>
          </>
        ) : (
          <div className="text-center text-slate-400 py-12">
            Upload a dataset and click "Run Explainability" to see results.
          </div>
        )}
      </div>
    </main>
  );
}