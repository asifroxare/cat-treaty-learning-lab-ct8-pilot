import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { createCT6Client, type CT6Client, type RunSuccess } from "../../api/client";
import type { CT6Problem } from "../../api/contract";
import type { ExecutionState, ResultFreshness } from "../../api/runState";
import { resultFreshnessAfterEdit } from "../../api/runState";
import { buildHoursRequest, initialHoursForm, type HoursFormErrors, type HoursFormValues } from "./hoursForm";

export interface HoursRunState {
  values: HoursFormValues; errors: HoursFormErrors; executionState: ExecutionState;
  freshness: ResultFreshness; priorSuccess: RunSuccess | null; problem: CT6Problem | null;
  setField<K extends keyof HoursFormValues>(field: K, value: HoursFormValues[K]): void;
  submit(): Promise<void>;
}

function useHoursController(client: CT6Client): HoursRunState {
  const [values, setValues] = useState(initialHoursForm);
  const [errors, setErrors] = useState<HoursFormErrors>({});
  const [executionState, setExecutionState] = useState<ExecutionState>("editing");
  const [freshness, setFreshness] = useState<ResultFreshness>("none");
  const [priorSuccess, setPriorSuccess] = useState<RunSuccess | null>(null);
  const [problem, setProblem] = useState<CT6Problem | null>(null);

  const setField = useCallback(<K extends keyof HoursFormValues>(field: K, value: HoursFormValues[K]) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setProblem(null); setExecutionState("editing"); setFreshness(resultFreshnessAfterEdit(priorSuccess !== null));
  }, [priorSuccess]);

  const submit = useCallback(async () => {
    const built = buildHoursRequest(values); setErrors(built.errors); setProblem(null);
    if (!built.request) { setExecutionState("schema_error"); setFreshness(priorSuccess ? "stale" : "none"); return; }
    setExecutionState("submitting"); setFreshness(priorSuccess ? "stale" : "none");
    const result = await client.runHoursClause(built.request);
    if (result.ok) { setPriorSuccess(result); setExecutionState("success"); setFreshness("current"); return; }
    setProblem(result.problem); setExecutionState(result.state); setFreshness(priorSuccess ? "stale" : "none");
  }, [client, priorSuccess, values]);
  return { values, errors, executionState, freshness, priorSuccess, problem, setField, submit };
}

const HoursRunContext = createContext<HoursRunState | null>(null);
export function HoursRunProvider({ children, client = createCT6Client() }: { children: ReactNode; client?: CT6Client }) {
  return <HoursRunContext.Provider value={useHoursController(client)}>{children}</HoursRunContext.Provider>;
}
export function useHoursRun(): HoursRunState {
  const state = useContext(HoursRunContext);
  if (!state) throw new Error("useHoursRun must be used inside HoursRunProvider");
  return state;
}
