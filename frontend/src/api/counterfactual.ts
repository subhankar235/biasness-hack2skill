// src/api/counterfactual.ts
import axios from "@/lib/axiosClient";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CounterfactualRequest {
  dataset_id: number;
  model_id: number;
  row: Record<string, string | number | boolean>;
  target_class: number;
  protected_features: string[];
  max_changes: number;
}

export interface FeatureChange {
  feature: string;
  from: string | number;
  to: string | number;
  delta?: number;
}

export interface CounterfactualResponse {
  job_id: string;
  status: string;
  candidates: any[];
  dataset_id?: number;
  model_id?: number;
  original_prediction?: number;
  counterfactual_prediction?: number;
  original_row?: Record<string, any>;
  counterfactual_row?: Record<string, any>;
  changed_features?: any[];
  n_changes?: number;
  found?: boolean;
  message?: string;
}

export interface DatasetMeta {
  dataset_id: number;
  name: string;
  columns: string[];
  n_rows: number;
  created_at: string;
}

export interface ModelMeta {
  model_id: number;
  name: string;
  file_type: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const runCounterfactual = generateCounterfactual;

export async function generateCounterfactual(
  payload: CounterfactualRequest
): Promise<CounterfactualResponse> {
  const { data } = await axios.post<CounterfactualResponse>(
    "/bias/counterfactual",
    payload
  );
  return data;
}

export async function fetchDatasets(): Promise<DatasetMeta[]> {
  const { data } = await axios.get<DatasetMeta[]>("/datasets");
  return data;
}

export async function fetchDatasetColumns(
  datasetId: number
): Promise<string[]> {
  const { data } = await axios.get<DatasetMeta>(`/datasets/${datasetId}`);
  return data.columns;
}

export async function fetchDatasetRow(
  datasetId: number,
  rowIndex: number
): Promise<Record<string, string | number>> {
  const { data } = await axios.get(
    `/datasets/${datasetId}/rows/${rowIndex}`
  );
  return data;
}

export async function fetchModels(): Promise<ModelMeta[]> {
  const { data } = await axios.get<ModelMeta[]>("/models");
  return data;
}