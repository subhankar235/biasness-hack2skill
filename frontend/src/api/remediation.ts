import { fetchApi } from "./fetchApi";

export interface RemediationParams {
  strategy: string;
  sensitive_column: string;
  target_column: string;
  dataset_id?: number;
  model_id?: number;
}

export const runRemediation = async (params: RemediationParams) => {
  const strategy = params.strategy;
  const payload = {
    dataset_id: params.dataset_id || 1,
    sensitive_feature: params.sensitive_column,
    label_col: params.target_column,
    privileged_group: { [params.sensitive_column]: "privileged" },
  };
  
  if (strategy === "threshold") {
    payload.model_id = params.model_id || 1;
    payload.constraint = "demographic_parity";
  }
  
  if (strategy === "smote") {
    payload.sampling_strategy = "auto";
  }
  
  const result = await fetchApi.post(`/api/v1/remediation/${strategy === "reweight" ? "reweigh" : strategy}`, payload);
  return result;
};