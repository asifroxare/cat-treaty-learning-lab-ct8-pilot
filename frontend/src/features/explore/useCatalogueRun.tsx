import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { createCT6Client, type CT6Client, type RunSuccess } from "../../api/client";
import type { CT6Problem } from "../../api/contract";
import type { ExecutionState, ResultFreshness } from "../../api/runState";
import { resultFreshnessAfterEdit } from "../../api/runState";
import { buildCatalogueRequest, errorsFromProblem, initialCatalogueForm, type CatalogueFormErrors, type CatalogueFormValues } from "./catalogueForm";

export interface CatalogueRunState {
  values: CatalogueFormValues;
  errors: CatalogueFormErrors;
  executionState: ExecutionState;
  freshness: ResultFreshness;
  priorSuccess: RunSuccess | null;
  problem: CT6Problem | null;
  setField<K extends keyof CatalogueFormValues>(field: K, value: CatalogueFormValues[K]): void;
  submit(): Promise<void>;
}

function useCatalogueRunController(client: CT6Client): CatalogueRunState {
  const [values, setValues] = useState(initialCatalogueForm);
  const [errors, setErrors] = useState<CatalogueFormErrors>({});
  const [executionState, setExecutionState] = useState<ExecutionState>("editing");
  const [freshness, setFreshness] = useState<ResultFreshness>("none");
  const [priorSuccess, setPriorSuccess] = useState<RunSuccess | null>(null);
  const [problem, setProblem] = useState<CT6Problem | null>(null);

  const setField = useCallback(<K extends keyof CatalogueFormValues>(field: K, value: CatalogueFormValues[K]) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setProblem(null);
    setExecutionState("editing");
    setFreshness(resultFreshnessAfterEdit(priorSuccess !== null));
  }, [priorSuccess]);

  const submit = useCallback(async () => {
    const built = buildCatalogueRequest(values);
    setErrors(built.errors);
    setProblem(null);
    if (!built.request) {
      setExecutionState("schema_error");
      setFreshness(priorSuccess ? "stale" : "none");
      return;
    }

    setExecutionState("submitting");
    setFreshness(priorSuccess ? "stale" : "none");
    const result = await client.runCatalogue(built.request);
    if (result.ok) {
      setPriorSuccess(result);
      setExecutionState("success");
      setFreshness("current");
      return;
    }
    setProblem(result.problem);
    if (result.problem) setErrors(errorsFromProblem(result.problem));
    setExecutionState(result.state);
    setFreshness(priorSuccess ? "stale" : "none");
  }, [client, priorSuccess, values]);

  return { values, errors, executionState, freshness, priorSuccess, problem, setField, submit };
}

const CatalogueRunContext = createContext<CatalogueRunState | null>(null);

export function CatalogueRunProvider({ children, client = createCT6Client() }: { children: ReactNode; client?: CT6Client }) {
  const state = useCatalogueRunController(client);
  return <CatalogueRunContext.Provider value={state}>{children}</CatalogueRunContext.Provider>;
}

export function useCatalogueRun(): CatalogueRunState {
  const state = useContext(CatalogueRunContext);
  if (!state) throw new Error("useCatalogueRun must be used inside CatalogueRunProvider");
  return state;
}
