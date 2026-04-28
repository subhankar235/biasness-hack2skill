"use client";

import { useState } from "react";
import { runRemediation } from "@/api/remediation";

export default function RemediationPage() {
  const [datasetIdInput, setDatasetIdInput] = useState("demo");
  const [strategy, setStrategy] = useState("reweight");
  const [sensitive, setSensitive] = useState("gender");
  const [target, setTarget] = useState("loan");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function handleRun() {
    const dataset_id = datasetIdInput || "demo";

    setLoading(true);
    setResult(null);

    try {
      const res = await runRemediation({
        dataset_id,
        strategy,
        sensitive_column: sensitive,
        target_column: target,
      });

      setResult(res);
    } catch (err: any) {
      console.error(err);
      alert(`❌ Remediation failed: ${err.message}`);
    }

    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-2xl mx-auto">

        <h1 className="text-4xl font-bold mb-6">
          Bias Remediation
        </h1>

        <p className="text-sm text-slate-400 mb-4">
          Use "demo" for mock data, or upload a CSV and use the dataset ID. Target must be binary (0/1).
        </p>

        {/* Dataset ID */}
        <div className="mb-4">
          <label className="block mb-1 text-sm text-slate-400">
            Dataset ID (optional)
          </label>
          <input
            value={datasetIdInput}
            onChange={(e) => setDatasetIdInput(e.target.value)}
            placeholder="Enter dataset_id or leave blank"
            className="w-full px-3 py-2 rounded bg-white text-black"
          />
        </div>

        {/* Strategy */}
        <div className="mb-4">
          <label className="block mb-1 text-sm text-slate-400">
            Strategy
          </label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="w-full px-3 py-2 rounded bg-white text-black"
          >
            <option value="reweigh">Reweight</option>
            <option value="resample">Resample</option>
            <option value="threshold">Threshold</option>
          </select>
        </div>

        {/* Sensitive Column */}
        <div className="mb-4">
          <label className="block mb-1 text-sm text-slate-400">
            Sensitive Column
          </label>
          <input
            value={sensitive}
            onChange={(e) => setSensitive(e.target.value)}
            className="w-full px-3 py-2 rounded bg-white text-black"
          />
        </div>

        {/* Target Column */}
        <div className="mb-6">
          <label className="block mb-1 text-sm text-slate-400">
            Target Column
          </label>
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="w-full px-3 py-2 rounded bg-white text-black"
          />
        </div>

        {/* Button */}
        <button
          onClick={handleRun}
          disabled={loading}
          className="w-full bg-green-500 hover:bg-green-600 text-black font-bold py-3 rounded-xl"
        >
          {loading ? "Running..." : "Run Remediation"}
        </button>

        {/* Result */}
        {result && (
          <div className="mt-8 bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <h2 className="text-lg font-semibold mb-2">
              Result
            </h2>
            <pre className="text-sm text-slate-300 overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

      </div>
    </main>
  );
}