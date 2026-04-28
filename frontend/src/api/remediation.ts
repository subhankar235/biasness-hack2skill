import { fetchApi } from "./fetchApi";

export interface RemediationParams {
  dataset_id: string;
  strategy: string;
  sensitive_column: string;
  target_column: string;
}

export const runRemediation = async (params: RemediationParams) => {
  const payload = {
    dataset_id: params.dataset_id || "demo",
    sensitive_feature: params.sensitive_column,
    label_col: params.target_column,
  };
  
  const strategyMap: Record<string, string> = {
    reweight: "reweigh",
    reweigh: "reweigh",
    resample: "resample",
    smote: "resample",
    threshold: "threshold",
  };
  
  const endpoint = strategyMap[params.strategy] || "reweigh";
  const result = await fetchApi.post(`/api/v1/remediation/${endpoint}`, payload);
  return result;
};