"use client";

// app/counterfactual/page.tsx
import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/use-toast";
import {
  useDatasets,
  useDatasetColumns,
  useDatasetRow,
  useModels,
  useCounterfactual,
} from "@/hooks/useCounterfactual";
import { FeatureChange, CounterfactualResponse } from "@/api/counterfactual";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-400 mb-2">
      {children}
    </p>
  );
}

function ProtectedFeatureToggle({
  feature,
  protected: isProtected,
  onToggle,
}: {
  feature: string;
  protected: boolean;
  onToggle: (f: string) => void;
}) {
  return (
    <button
      onClick={() => onToggle(feature)}
      className={`
        px-3 py-1.5 rounded-md text-xs font-medium border transition-all duration-150
        ${isProtected
          ? "bg-rose-950/60 border-rose-700 text-rose-300"
          : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
        }
      `}
    >
      {isProtected && <span className="mr-1">🔒</span>}
      {feature}
    </button>
  );
}

function FeatureDiffRow({ change, index }: { change: FeatureChange; index: number }) {
  const isNumeric = typeof change.delta === "number";
  const isPositive = isNumeric && (change.delta ?? 0) > 0;

  return (
    <div
      className="grid grid-cols-[1fr_auto_1fr_auto] gap-3 items-center py-3 px-4
                 border-b border-slate-800 last:border-0 group"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Feature name */}
      <div>
        <span className="text-xs text-slate-400 font-mono">{change.feature}</span>
      </div>

      {/* From value */}
      <div className="text-right">
        <span className="text-sm font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
          {String(change.from)}
        </span>
      </div>

      {/* Arrow + delta */}
      <div className="flex items-center gap-2 justify-center">
        <span className="text-slate-600">→</span>
        <span
          className={`text-sm font-mono font-semibold px-2 py-0.5 rounded ${
            isPositive
              ? "text-emerald-300 bg-emerald-950/60"
              : "text-amber-300 bg-amber-950/50"
          }`}
        >
          {String(change.to)}
        </span>
      </div>

      {/* Delta badge */}
      <div className="text-right">
        {isNumeric && change.delta !== undefined && (
          <span
            className={`text-[11px] font-mono ${
              isPositive ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {isPositive ? "+" : ""}
            {change.delta.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}

function ResultPanel({ result }: { result: CounterfactualResponse }) {
  const outcomeFlipped =
    result.original_prediction !== result.counterfactual_prediction;

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Outcome banner */}
      <div
        className={`rounded-xl p-4 flex items-center justify-between border ${
          result.found
            ? "bg-emerald-950/40 border-emerald-800/60"
            : "bg-rose-950/40 border-rose-800/60"
        }`}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{result.found ? "✓" : "✗"}</span>
          <div>
            <p className={`font-semibold text-sm ${result.found ? "text-emerald-300" : "text-rose-300"}`}>
              {result.found ? "Counterfactual Found" : "No Counterfactual Found"}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">{result.message}</p>
          </div>
        </div>
        {result.found && (
          <Badge className="bg-emerald-900 text-emerald-300 border-emerald-700 text-xs">
            {result.n_changes} change{result.n_changes !== 1 ? "s" : ""}
          </Badge>
        )}
      </div>

      {/* Prediction flip */}
      {result.found && (
        <div className="flex items-center gap-3 bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex-1 text-center">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Original</p>
            <span className="text-2xl font-bold font-mono text-rose-400">
              {result.original_prediction}
            </span>
          </div>
          <div className="text-slate-600 text-xl">⟶</div>
          <div className="flex-1 text-center">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Counterfactual</p>
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {result.counterfactual_prediction}
            </span>
          </div>
        </div>
      )}

      {/* Feature diff table */}
      {result.found && result.changed_features.length > 0 && (
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-2 pt-4 px-4">
            <CardTitle className="text-xs uppercase tracking-widest text-slate-400 font-semibold">
              Feature Changes Required
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {result.changed_features.map((change, i) => (
              <FeatureDiffRow key={change.feature} change={change} index={i} />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Row editor: lets user fill in feature values manually or from a dataset row
// ---------------------------------------------------------------------------

function RowEditor({
  columns,
  row,
  protectedFeatures,
  onRowChange,
  onProtectedToggle,
}: {
  columns: string[];
  row: Record<string, string | number>;
  protectedFeatures: string[];
  onRowChange: (key: string, value: string) => void;
  onProtectedToggle: (f: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <SectionLabel>Protected Features (will not be changed)</SectionLabel>
        <div className="flex flex-wrap gap-2">
          {columns.map((col) => (
            <ProtectedFeatureToggle
              key={col}
              feature={col}
              protected={protectedFeatures.includes(col)}
              onToggle={onProtectedToggle}
            />
          ))}
        </div>
      </div>

      <div>
        <SectionLabel>Input Row Values</SectionLabel>
        <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
          {columns.map((col) => (
            <div key={col} className="flex flex-col gap-1">
              <label className="text-[10px] font-mono text-slate-500 truncate">{col}</label>
              <input
                type="text"
                value={String(row[col] ?? "")}
                onChange={(e) => onRowChange(col, e.target.value)}
                className={`
                  h-8 px-2 rounded-md text-xs font-mono bg-slate-800 border text-slate-200
                  focus:outline-none focus:border-indigo-500 transition-colors
                  ${protectedFeatures.includes(col)
                    ? "border-rose-800 opacity-60 cursor-not-allowed"
                    : "border-slate-700"
                  }
                `}
                disabled={protectedFeatures.includes(col)}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function CounterfactualPage() {
  const { data: datasets, isLoading: datasetsLoading } = useDatasets();
  const { data: models, isLoading: modelsLoading } = useModels();

  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [modelId, setModelId] = useState<number | null>(null);
  const [rowIndex, setRowIndex] = useState<number>(0);
  const [targetClass, setTargetClass] = useState<number>(1);
  const [maxChanges, setMaxChanges] = useState<number>(3);
  const [protectedFeatures, setProtectedFeatures] = useState<string[]>([]);
  const [rowValues, setRowValues] = useState<Record<string, string | number>>({});

  const { data: columns } = useDatasetColumns(datasetId);
  const { data: fetchedRow } = useDatasetRow(datasetId, rowIndex);

  // Sync fetched row into local state
  const syncedRow = fetchedRow
    ? { ...fetchedRow, ...rowValues }
    : rowValues;

  const { mutate, data: result, isPending, reset } = useCounterfactual();

  const handleRowChange = useCallback((key: string, value: string) => {
    setRowValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleProtectedToggle = useCallback((feature: string) => {
    setProtectedFeatures((prev) =>
      prev.includes(feature) ? prev.filter((f) => f !== feature) : [...prev, feature]
    );
  }, []);

  const handleRun = () => {
    if (!datasetId || !modelId) {
      toast({ title: "Select a dataset and model first.", variant: "destructive" });
      return;
    }
    if (!columns || columns.length === 0) {
      toast({ title: "No columns found for selected dataset.", variant: "destructive" });
      return;
    }

    // Coerce string inputs to numbers where possible
    const coercedRow: Record<string, string | number> = {};
    for (const [k, v] of Object.entries(syncedRow)) {
      const num = Number(v);
      coercedRow[k] = isNaN(num) ? v : num;
    }

    mutate(
      {
        dataset_id: datasetId,
        model_id: modelId,
        row: coercedRow,
        target_class: targetClass,
        protected_features: protectedFeatures,
        max_changes: maxChanges,
      },
      {
        onError: (err) => {
          toast({
            title: "Counterfactual failed",
            description: err.message,
            variant: "destructive",
          });
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0c10] text-slate-100 font-['DM_Sans',sans-serif]">
      {/* Google Font import */}
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');`}</style>

      {/* Top bar */}
      <header className="border-b border-slate-800/60 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
            <span className="text-xs font-bold text-white">CF</span>
          </div>
          <h1 className="text-sm font-semibold text-slate-200 tracking-tight">
            Counterfactual Explorer
          </h1>
        </div>
        <Badge className="bg-slate-800 text-slate-400 border-slate-700 text-[10px] tracking-widest uppercase">
          Bias · Explainability
        </Badge>
      </header>

      <div className="max-w-6xl mx-auto px-8 py-8 grid grid-cols-[380px_1fr] gap-8">

        {/* ---------------------------------------------------------------- */}
        {/* LEFT PANEL — Configuration                                        */}
        {/* ---------------------------------------------------------------- */}
        <div className="space-y-5">

          {/* Dataset + Model selectors */}
          <Card className="bg-slate-900/80 border-slate-800 shadow-xl">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-xs uppercase tracking-[0.15em] text-slate-400 font-semibold">
                Data &amp; Model
              </CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5 space-y-4">

              <div className="space-y-1.5">
                <SectionLabel>Dataset</SectionLabel>
                {datasetsLoading ? (
                  <Skeleton className="h-9 w-full bg-slate-800" />
                ) : (
                  <Select
                    onValueChange={(v) => {
                      setDatasetId(Number(v));
                      setRowValues({});
                      reset();
                    }}
                  >
                    <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200 text-sm h-9">
                      <SelectValue placeholder="Select dataset…" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-700">
                      {datasets?.map((d) => (
                        <SelectItem
                          key={d.dataset_id}
                          value={String(d.dataset_id)}
                          className="text-slate-200 text-sm focus:bg-slate-800"
                        >
                          {d.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              <div className="space-y-1.5">
                <SectionLabel>Model</SectionLabel>
                {modelsLoading ? (
                  <Skeleton className="h-9 w-full bg-slate-800" />
                ) : (
                  <Select onValueChange={(v) => { setModelId(Number(v)); reset(); }}>
                    <SelectTrigger className="bg-slate-800 border-slate-700 text-slate-200 text-sm h-9">
                      <SelectValue placeholder="Select model…" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-700">
                      {models?.map((m) => (
                        <SelectItem
                          key={m.model_id}
                          value={String(m.model_id)}
                          className="text-slate-200 text-sm focus:bg-slate-800"
                        >
                          <span>{m.name}</span>
                          <span className="ml-2 text-slate-500 text-[10px] uppercase font-mono">
                            {m.file_type}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              {/* Row index picker */}
              <div className="space-y-1.5">
                <SectionLabel>Row Index</SectionLabel>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min={0}
                    value={rowIndex}
                    onChange={(e) => {
                      setRowIndex(Number(e.target.value));
                      setRowValues({});
                    }}
                    className="h-9 w-24 px-3 rounded-md text-sm font-mono bg-slate-800
                               border border-slate-700 text-slate-200 focus:outline-none
                               focus:border-indigo-500 transition-colors"
                  />
                  <p className="text-xs text-slate-500 self-center">
                    Load a row from the dataset to pre-fill values
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Counterfactual settings */}
          <Card className="bg-slate-900/80 border-slate-800 shadow-xl">
            <CardHeader className="pb-2 pt-5 px-5">
              <CardTitle className="text-xs uppercase tracking-[0.15em] text-slate-400 font-semibold">
                Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="px-5 pb-5 space-y-4">

              <div className="space-y-1.5">
                <SectionLabel>Target Class (desired outcome)</SectionLabel>
                <div className="flex gap-2">
                  {[0, 1].map((c) => (
                    <button
                      key={c}
                      onClick={() => setTargetClass(c)}
                      className={`
                        flex-1 h-9 rounded-md text-sm font-mono font-semibold border transition-all
                        ${targetClass === c
                          ? "bg-indigo-600 border-indigo-500 text-white"
                          : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                        }
                      `}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <SectionLabel>Max Feature Changes</SectionLabel>
                <div className="flex gap-2 flex-wrap">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      onClick={() => setMaxChanges(n)}
                      className={`
                        w-10 h-9 rounded-md text-sm font-mono font-semibold border transition-all
                        ${maxChanges === n
                          ? "bg-indigo-600 border-indigo-500 text-white"
                          : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                        }
                      `}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Row editor — only shown when dataset + columns loaded */}
          {columns && columns.length > 0 && (
            <Card className="bg-slate-900/80 border-slate-800 shadow-xl">
              <CardHeader className="pb-2 pt-5 px-5">
                <CardTitle className="text-xs uppercase tracking-[0.15em] text-slate-400 font-semibold">
                  Input Row
                </CardTitle>
              </CardHeader>
              <CardContent className="px-5 pb-5">
                <RowEditor
                  columns={columns}
                  row={syncedRow}
                  protectedFeatures={protectedFeatures}
                  onRowChange={handleRowChange}
                  onProtectedToggle={handleProtectedToggle}
                />
              </CardContent>
            </Card>
          )}

          {/* Run button */}
          <Button
            onClick={handleRun}
            disabled={isPending || !datasetId || !modelId}
            className="w-full h-11 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold
                       text-sm tracking-wide rounded-xl transition-all duration-150
                       disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-indigo-900/30"
          >
            {isPending ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Computing…
              </span>
            ) : (
              "Generate Counterfactual"
            )}
          </Button>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* RIGHT PANEL — Results                                             */}
        {/* ---------------------------------------------------------------- */}
        <div>
          {isPending && (
            <div className="space-y-4 animate-pulse">
              <Skeleton className="h-20 w-full rounded-xl bg-slate-800" />
              <Skeleton className="h-14 w-full rounded-xl bg-slate-800" />
              <Skeleton className="h-48 w-full rounded-xl bg-slate-800" />
            </div>
          )}

          {!isPending && result && <ResultPanel result={result} />}

          {!isPending && !result && (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px]
                            border border-dashed border-slate-800 rounded-2xl text-center p-12">
              <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center mb-4">
                <span className="text-2xl">🔀</span>
              </div>
              <p className="text-sm font-medium text-slate-300 mb-1">
                No results yet
              </p>
              <p className="text-xs text-slate-500 max-w-xs leading-relaxed">
                Select a dataset, model, and input row. Mark protected features
                that should not be changed, then click Generate.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}