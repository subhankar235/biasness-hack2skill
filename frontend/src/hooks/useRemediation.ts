import { useMutation } from "@tanstack/react-query";
import { runRemediation } from "@/api/remediation";

export const useRemediation = () => {
  return useMutation({
    mutationFn: runRemediation,
  });
};