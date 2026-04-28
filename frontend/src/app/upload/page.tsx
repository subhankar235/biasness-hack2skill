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
    if (!file) {
      alert("Choose a dataset file first");
      return;
    }

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

      setUploadData(data);
      localStorage.setItem("dataset_id", data.id);
    } catch (error) {
      alert("Upload failed");
    }

    setLoading(false);
  }

  async function runBiasScan() {
    if (!uploadData?.profile) {
      alert("Upload dataset first");
      return;
    }

    setScanLoading(true);

    const columns = uploadData.profile.columns || [];

    const targetCol =
      columns[columns.length - 1] || "target";

    const sensitiveCol =
      uploadData.profile.sensitive_columns?.[0] ||
      columns[0] ||
      "gender";

    try {
      const res = await fetch(
        `${API}/api/v1/bias/scan`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            target_column: targetCol,
            sensitive_column: sensitiveCol,
            positive_value: 1,
          }),
        }
      );

      const data = await res.json();

      setScanData(data);

      localStorage.setItem(
        "fairlens_scan",
        JSON.stringify(data)
      );
    } catch (error) {
      alert("Bias scan failed");
    }

    setScanLoading(false);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white px-6 py-10">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="mb-10">
          <h1 className="text-5xl font-bold tracking-tight">
            FairLens
          </h1>

          <p className="text-slate-400 mt-3 text-lg">
            No-code dataset upload with instant bias scanning.
          </p>
        </div>

        {/* Upload Card */}
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-4">
            Upload Dataset
          </h2>

          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">

            <input
              type="file"
              accept=".csv,.xlsx,.xls,.txt"
              onChange={(e) =>
                setFile(
                  e.target.files?.[0] || null
                )
              }
              className="text-sm"
            />

            <button
              onClick={handleUpload}
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 transition font-medium"
            >
              {loading
                ? "Uploading..."
                : "Upload Dataset"}
            </button>

          </div>
        </section>

        {/* Upload Success */}
        {uploadData?.id && (
          <section className="mt-6 bg-green-900/30 border border-green-700 rounded-2xl p-5">
            <p className="text-green-300 font-semibold">
              Dataset Uploaded Successfully ✅
            </p>

            <p className="text-sm text-green-400 mt-1">
              Dataset ID: {uploadData.id}
            </p>

            <button
              onClick={() =>
                navigator.clipboard.writeText(
                  uploadData.id
                )
              }
              className="mt-3 text-cyan-400 text-sm"
            >
              Copy ID
            </button>
          </section>
        )}

        {/* Dataset Summary */}
        {uploadData?.profile && (
          <section className="mt-10">
            <h2 className="text-2xl font-semibold mb-4">
              Dataset Summary
            </h2>

            <div className="grid md:grid-cols-4 gap-4">

              <Card
                title="Rows"
                value={uploadData.profile.rows}
              />

              <Card
                title="Columns"
                value={
                  uploadData.profile.num_columns
                }
              />

              <Card
                title="Missing Values"
                value={
                  uploadData.profile
                    .missing_values
                }
              />

              <Card
                title="Sensitive Fields"
                value={
                  uploadData.profile
                    .sensitive_columns
                    ?.length || 0
                }
              />

            </div>

            {/* Sensitive Fields */}
            <div className="mt-5 bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <p className="text-slate-400 text-sm mb-3">
                Detected Sensitive Columns
              </p>

              <div className="flex flex-wrap gap-2">
                {(
                  uploadData.profile
                    .sensitive_columns || []
                ).map(
                  (item: string) => (
                    <span
                      key={item}
                      className="px-3 py-1 rounded-full bg-purple-600/20 text-purple-300 text-sm"
                    >
                      {item}
                    </span>
                  )
                )}
              </div>
            </div>

            <button
              onClick={runBiasScan}
              disabled={scanLoading}
              className="mt-6 px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 transition font-medium"
            >
              {scanLoading
                ? "Scanning..."
                : "Run Bias Scan"}
            </button>

          </section>
        )}

        {/* Bias Results */}
        {scanData && (
          <section className="mt-10">
            <h2 className="text-2xl font-semibold mb-4">
              Bias Results
            </h2>

            <div className="grid md:grid-cols-4 gap-4">

              {Object.entries(
                scanData.approval_rates || {}
              ).map(
                ([key, val]: any) => (
                  <Card
                    key={key}
                    title={`${key} Approval`}
                    value={val}
                  />
                )
              )}

              <Card
                title="Parity Difference"
                value={
                  scanData.demographic_parity_diff
                }
              />

              <RiskCard
                value={
                  scanData.risk_level || "LOW"
                }
              />

            </div>
          </section>
        )}

      </div>
    </main>
  );
}

function Card({
  title,
  value,
}: {
  title: string;
  value: any;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <p className="text-slate-400 text-sm">
        {title}
      </p>

      <h3 className="text-3xl font-bold mt-2">
        {value}
      </h3>
    </div>
  );
}

function RiskCard({
  value,
}: {
  value: string;
}) {
  const color =
    value === "HIGH"
      ? "bg-red-600/20 text-red-300"
      : value === "MEDIUM"
      ? "bg-yellow-600/20 text-yellow-300"
      : "bg-green-600/20 text-green-300";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <p className="text-slate-400 text-sm">
        Risk Level
      </p>

      <div
        className={`inline-block mt-3 px-4 py-2 rounded-full font-semibold ${color}`}
      >
        {value}
      </div>
    </div>
  );
}