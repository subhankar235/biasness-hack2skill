"use client";

import { useState } from "react";

const API = "http://127.0.0.1:8000";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadData, setUploadData] = useState<any>(null);
  const [scanData, setScanData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);

  async function handleUpload() {
    if (!file) return;

    setLoading(true);
    setScanData(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(
        `${API}/api/v1/datasets/upload?name=test&org_id=test`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await res.json();

      // ✅ store FULL response (important)
      setUploadData(data);

      // ✅ store dataset_id for future pages
      localStorage.setItem("dataset_id", data.id);

    } catch (err) {
      alert("Upload failed");
    }

    setLoading(false);
  }

  async function runBiasScan() {
    setScanLoading(true);

    const columns = uploadData?.profile?.columns || [];
    const targetCol = columns[columns.length - 1];
    const sensitiveCol =
      uploadData?.profile?.sensitive_columns?.[0] || columns[0];

    try {
      const res = await fetch(`${API}/api/v1/bias/bias/scan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          target_column: targetCol,
          sensitive_column: sensitiveCol,
          positive_value: 1,
        }),
      });

      const data = await res.json();
      setScanData(data);

      localStorage.setItem("fairlens_scan", JSON.stringify(data));
    } catch (err) {
      alert("Bias scan failed");
    }

    setScanLoading(false);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white px-6 py-10">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="mb-10">
          <h1 className="text-5xl font-bold tracking-tight">FairLens</h1>
          <p className="text-slate-400 mt-3 text-lg">
            Upload datasets and detect hidden bias instantly.
          </p>
        </div>

        {/* Upload Card */}
        <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 shadow-lg">
          <h2 className="text-xl font-semibold mb-4">Dataset Upload</h2>

          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
            <input
              type="file"
              onChange={(e) =>
                setFile(e.target.files ? e.target.files[0] : null)
              }
              className="text-sm"
            />

            <button
              onClick={handleUpload}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-xl font-medium transition"
            >
              {loading ? "Uploading..." : "Upload Dataset"}
            </button>
          </div>
        </div>

        {/* ✅ SHOW DATASET ID */}
        {uploadData?.id && (
          <div className="mt-6 bg-green-900/40 border border-green-700 p-4 rounded-xl">
            <p className="text-green-300 font-semibold">
              Dataset Uploaded Successfully ✅
            </p>

            <p className="text-green-400 text-sm mt-1">
              Dataset ID: {uploadData.id}
            </p>

            <button
              onClick={() =>
                navigator.clipboard.writeText(uploadData.id)
              }
              className="mt-2 text-xs text-cyan-400"
            >
              Copy ID
            </button>
          </div>
        )}

        {/* Dataset Summary */}
        {uploadData?.profile && (
          <div className="mt-8">
            <h2 className="text-2xl font-semibold mb-4">Dataset Summary</h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card title="Rows" value={uploadData.profile.rows} />
              <Card title="Columns" value={uploadData.profile.num_columns} />
              <Card title="Missing Values" value={uploadData.profile.missing_values} />
              <Card
                title="Sensitive Columns"
                value={uploadData.profile.sensitive_columns.length}
              />
            </div>

            <div className="mt-5 bg-slate-900 rounded-2xl p-5 border border-slate-800">
              <p className="text-slate-400 text-sm mb-2">
                Detected Sensitive Fields
              </p>

              <div className="flex gap-2 flex-wrap">
                {uploadData.profile.sensitive_columns.map((col: string) => (
                  <span
                    key={col}
                    className="bg-purple-600/20 text-purple-300 px-3 py-1 rounded-full text-sm"
                  >
                    {col}
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={runBiasScan}
              disabled={scanLoading}
              className="mt-6 bg-emerald-600 hover:bg-emerald-700 px-5 py-3 rounded-xl font-medium transition"
            >
              {scanLoading ? "Scanning..." : "Run Bias Scan"}
            </button>
          </div>
        )}

        {/* Bias Results */}
        {scanData && (
          <div className="mt-10">
            <h2 className="text-2xl font-semibold mb-4">Bias Results</h2>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {Object.entries(scanData.approval_rates || {}).map(
                ([key, val]: [string, any]) => (
                  <Card key={key} title={`${key} Approval`} value={val} />
                )
              )}

              <Card
                title="Parity Difference"
                value={scanData.demographic_parity_diff}
              />

              <RiskCard value={scanData.risk_level} />
            </div>
          </div>
        )}

      </div>
    </main>
  );
}

function Card({ title, value }: { title: string; value: any }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <p className="text-slate-400 text-sm">{title}</p>
      <h3 className="text-3xl font-bold mt-2">{value}</h3>
    </div>
  );
}

function RiskCard({ value }: { value: string }) {
  const color =
    value === "HIGH"
      ? "bg-red-600/20 text-red-300"
      : "bg-green-600/20 text-green-300";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <p className="text-slate-400 text-sm">Risk Level</p>
      <div
        className={`inline-block mt-3 px-4 py-2 rounded-full font-semibold ${color}`}
      >
        {value}
      </div>
    </div>
  );
}