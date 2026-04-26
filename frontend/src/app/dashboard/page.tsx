"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { FileDown, Loader2 } from "lucide-react";

export default function DashboardPage() {
  const [upload, setUpload] = useState<any>(null);
  const [scan, setScan] = useState<any>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    const u = localStorage.getItem("fairlens_upload");
    const s = localStorage.getItem("fairlens_scan");

    if (u) setUpload(JSON.parse(u));
    if (s) setScan(JSON.parse(s));
  }, []);

  const chartData = useMemo(() => {
    if (!scan?.approval_rates) return [];

    return [
      {
        group: "Male",
        value: Number(scan.approval_rates.Male || 0),
      },
      {
        group: "Female",
        value: Number(scan.approval_rates.Female || 0),
      },
    ];
  }, [scan]);

  const riskPercent = useMemo(() => {
    if (!scan?.demographic_parity_diff) return 0;

    return Math.min(
      Math.round(Number(scan.demographic_parity_diff) * 100),
      100
    );
  }, [scan]);

  function downloadJSON() {
    const report = {
      generated_at: new Date().toISOString(),
      upload,
      scan,
    };

    const blob = new Blob(
      [JSON.stringify(report, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "fairlens-report.json";
    a.click();

    URL.revokeObjectURL(url);
  }

  async function downloadPDF() {
    try {
      setPdfLoading(true);

      const res = await fetch(
        "http://127.0.0.1:8000/api/v1/report/pdf"
      );

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = "fairlens-audit-report.pdf";
      a.click();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert("PDF generation failed");
    } finally {
      setPdfLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="mb-10">
          <h1 className="text-5xl font-bold">
            FairLens Dashboard
          </h1>

          <p className="text-slate-400 mt-3 text-lg">
            Real-time fairness intelligence from your latest scan.
          </p>
        </div>

        {/* AI Insight + Export */}
        {upload && scan && (
          <div className="grid md:grid-cols-2 gap-6 mb-8">

            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-xl font-semibold mb-4">
                FairLens AI Insight
              </h2>

              <p className="text-slate-300 leading-7">
                Significant disparity detected between demographic groups.
                Female approval outcomes are lower than male outcomes.
                Recommended next step: review labels, thresholds,
                and feature weighting before deployment.
              </p>
            </section>

            <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
              <h2 className="text-xl font-semibold mb-4">
                Export Audit Report
              </h2>

              <div className="flex gap-3 flex-wrap">

                <button
                  onClick={downloadJSON}
                  className="px-5 py-3 rounded-xl bg-cyan-500 text-black font-semibold hover:bg-cyan-400 transition"
                >
                  Download JSON
                </button>

                <button
                  onClick={downloadPDF}
                  disabled={pdfLoading}
                  className="px-5 py-3 rounded-xl bg-white text-black font-semibold hover:bg-slate-200 transition flex items-center gap-2 disabled:opacity-70"
                >
                  {pdfLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FileDown className="w-4 h-4" />
                      Generate Live PDF
                    </>
                  )}
                </button>

              </div>

              <p className="text-slate-400 text-sm mt-4">
                Export investor-grade fairness reports instantly.
              </p>
            </section>

          </div>
        )}

        {!upload && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
            <p className="text-red-400 text-lg">
              No dataset scanned yet.
            </p>

            <p className="text-slate-400 mt-2">
              Upload a dataset first to generate live fairness insights.
            </p>
          </div>
        )}

        {upload && (
          <>
            {/* Metrics */}
            <div className="grid md:grid-cols-4 gap-6 mb-8">
              <Card title="Rows Scanned" value={upload.rows} />
              <Card title="Columns" value={upload.num_columns} />
              <Card title="Missing Values" value={upload.missing_values} />
              <Card
                title="Sensitive Fields"
                value={upload.sensitive_columns.length}
              />
            </div>

            {/* Charts */}
            {scan && (
              <div className="grid md:grid-cols-2 gap-6 mb-8">

                <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    Approval Rate by Group
                  </h2>

                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData}>
                        <XAxis dataKey="group" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip />
                        <Bar dataKey="value" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                  <h2 className="text-xl font-semibold mb-5">
                    Bias Risk Meter
                  </h2>

                  <p className="text-slate-400 mb-3">
                    Demographic Parity Difference
                  </p>

                  <div className="w-full bg-slate-800 rounded-full h-4 overflow-hidden">
                    <div
                      className={`h-full ${
                        riskPercent > 50
                          ? "bg-red-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${riskPercent}%` }}
                    />
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-3xl font-bold">
                      {riskPercent}%
                    </span>

                    <span
                      className={`px-4 py-2 rounded-full font-semibold ${
                        scan.risk_level === "HIGH"
                          ? "bg-red-500/20 text-red-300"
                          : "bg-emerald-500/20 text-emerald-300"
                      }`}
                    >
                      {scan.risk_level}
                    </span>
                  </div>
                </section>

              </div>
            )}

            {/* Bottom */}
            {scan && (
              <div className="grid md:grid-cols-2 gap-6">

                <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    Scan Findings
                  </h2>

                  <div className="space-y-3 text-slate-300">
                    <p>
                      Male Approval Rate:
                      <span className="text-cyan-400 font-semibold ml-2">
                        {scan.approval_rates?.Male}
                      </span>
                    </p>

                    <p>
                      Female Approval Rate:
                      <span className="text-cyan-400 font-semibold ml-2">
                        {scan.approval_rates?.Female}
                      </span>
                    </p>

                    <p>
                      Parity Difference:
                      <span className="text-yellow-400 font-semibold ml-2">
                        {scan.demographic_parity_diff}
                      </span>
                    </p>
                  </div>
                </section>

                <section className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">
                    Sensitive Columns
                  </h2>

                  <div className="flex flex-wrap gap-3">
                    {upload.sensitive_columns.map(
                      (item: string) => (
                        <span
                          key={item}
                          className="px-3 py-1 rounded-full bg-cyan-500 text-black font-semibold"
                        >
                          {item}
                        </span>
                      )
                    )}
                  </div>

                  <p className="text-slate-400 mt-5 text-sm">
                    These fields may require fairness monitoring.
                  </p>
                </section>

              </div>
            )}
          </>
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
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
      <p className="text-slate-400 text-sm">{title}</p>

      <p className="text-3xl font-bold text-cyan-400 mt-2">
        {value}
      </p>
    </div>
  );
}