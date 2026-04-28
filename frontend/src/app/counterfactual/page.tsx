"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/ui/use-toast";

interface CounterfactualResponse {
  job_id: string;
  status: string;
  original_prediction: number;
  desired_outcome: number;
  counterfactual: Record<string, any>;
  changed_features: Array<{feature: string; from: number; to: number; delta: number}>;
  n_changes: number;
  found: boolean;
  message: string;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-400 mb-2">
      {children}
    </p>
  );
}

function ResultPanel({ result }: { result: CounterfactualResponse }) {
  return (
    <div className="space-y-4">
      <div className={`rounded-xl p-4 border ${
        result.found ? "bg-emerald-950/40 border-emerald-800" : "bg-rose-950/40 border-rose-800"
      }`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">{result.found ? "✓" : "✗"}</span>
          <div>
            <p className={`font-semibold ${result.found ? "text-emerald-300" : "text-rose-300"}`}>
              {result.found ? "Counterfactual Found" : "No Counterfactual"}
            </p>
            <p className="text-xs text-slate-400">{result.message}</p>
          </div>
        </div>
      </div>

      {result.found && (
        <>
          <div className="flex items-center gap-4 bg-slate-800/50 rounded-xl p-4">
            <div className="flex-1 text-center">
              <p className="text-[10px] text-slate-500 mb-1">Original</p>
              <span className="text-2xl font-bold text-rose-400">{result.original_prediction}</span>
            </div>
            <div className="text-slate-600 text-xl">⟶</div>
            <div className="flex-1 text-center">
              <p className="text-[10px] text-slate-500 mb-1">Desired</p>
              <span className="text-2xl font-bold text-emerald-400">{result.desired_outcome}</span>
            </div>
          </div>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-xs uppercase text-slate-400">Changes Required</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {result.changed_features.map((change, i) => (
                <div key={i} className="grid grid-cols-4 gap-3 items-center py-3 px-4 border-b border-slate-800">
                  <span className="text-xs text-slate-400">{change.feature}</span>
                  <span className="text-right text-sm text-slate-300">{change.from}</span>
                  <span className="text-center text-slate-600">→</span>
                  <span className="text-sm text-emerald-300 font-semibold">{change.to}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

export default function CounterfactualPage() {
  const [datasetId, setDatasetId] = useState("");
  const [modelId, setModelId] = useState("");
  const [rowIndex, setRowIndex] = useState(0);
  const [desiredOutcome, setDesiredOutcome] = useState(1);
  const [result, setResult] = useState<CounterfactualResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!datasetId || !modelId) {
      toast({ title: "Enter dataset_id and model_id", variant: "destructive" });
      return;
    }
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/bias/counterfactual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: datasetId,
          model_id: parseInt(modelId),
          row_index: rowIndex,
          desired_outcome: desiredOutcome,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      toast({ title: "Failed", description: err.message, variant: "destructive" });
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">Counterfactual</h1>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <SectionLabel>Dataset ID</SectionLabel>
            <input
              type="text"
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              placeholder="1"
              className="w-full px-3 py-2 rounded bg-white text-black"
            />
          </div>
          <div>
            <SectionLabel>Model ID</SectionLabel>
            <input
              type="text"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="1"
              className="w-full px-3 py-2 rounded bg-white text-black"
            />
          </div>
          <div>
            <SectionLabel>Row Index</SectionLabel>
            <input
              type="number"
              value={rowIndex}
              onChange={(e) => setRowIndex(Number(e.target.value))}
              className="w-full px-3 py-2 rounded bg-white text-black"
            />
          </div>
          <div>
            <SectionLabel>Desired Outcome</SectionLabel>
            <div className="flex gap-2">
              {[0, 1].map((c) => (
                <button
                  key={c}
                  onClick={() => setDesiredOutcome(c)}
                  className={`flex-1 py-2 rounded font-semibold ${
                    desiredOutcome === c ? "bg-indigo-600 text-white" : "bg-slate-700"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>

        <Button
          onClick={handleRun}
          disabled={loading || !datasetId || !modelId}
          className="w-full bg-indigo-600 hover:bg-indigo-500 py-3 rounded-xl font-bold"
        >
          {loading ? "Computing..." : "Generate"}
        </Button>

        {result && <ResultPanel result={result} />}
      </div>
    </div>
  );
}