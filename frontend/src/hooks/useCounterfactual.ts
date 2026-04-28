import { useMutation, useQuery } from "@tanstack/react-query";
import {
  runCounterfactual as apiRunCounterfactual,
  fetchDatasets,
  fetchDatasetColumns,
  fetchDatasetRow,
  fetchModels,
  CounterfactualRequest,
  CounterfactualResponse,
} from "@/api/counterfactual";

export const useCounterfactual = () => {
  return useMutation({
    mutationFn: (payload: CounterfactualRequest) => apiRunCounterfactual(payload),
  });
};

export const useDatasets = () => {
  return useQuery({
    queryKey: ["datasets"],
    queryFn: fetchDatasets,
  });
};

export const useDatasetColumns = (datasetId: number | null) => {
  return useQuery({
    queryKey: ["datasetColumns", datasetId],
    queryFn: () => fetchDatasetColumns(datasetId!),
    enabled: !!datasetId,
  });
};

export const useDatasetRow = (datasetId: number | null, rowIndex: number) => {
  return useQuery({
    queryKey: ["datasetRow", datasetId, rowIndex],
    queryFn: () => fetchDatasetRow(datasetId!, rowIndex),
    enabled: !!datasetId && rowIndex >= 0,
  });
};

export const useModels = () => {
  return useQuery({
    queryKey: ["models"],
    queryFn: fetchModels,
  });
};

export { runCounterfactual } from "@/api/counterfactual";