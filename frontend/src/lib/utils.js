import { useLocation } from "react-router-dom";
export function useQuery() { return new URLSearchParams(useLocation().search); }

export function joinQS(params) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") q.set(k, v);
  return q.toString();
}