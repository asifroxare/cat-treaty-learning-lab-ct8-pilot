import type { CT6Problem } from "./contract";

export type ExecutionState =
  | "editing"
  | "submitting"
  | "success"
  | "schema_error"
  | "domain_error"
  | "contract_blocked"
  | "too_large"
  | "pilot_limit"
  | "pilot_access"
  | "pilot_busy"
  | "server_error"
  | "offline";

export type ResultFreshness = "none" | "current" | "stale";

export type CT6ProblemCode =
  | "CT6_MALFORMED_JSON"
  | "CT6_VERSION_CONFLICT"
  | "CT6_REQUEST_TOO_LARGE"
  | "CT6_SCHEMA_VALIDATION"
  | "CT6_DOMAIN_VALIDATION"
  | "CT6_CONTRACT_BLOCKED"
  | "CT6_INTERNAL_ERROR"
  | "CT6_NOT_READY";

const stateByCode: Readonly<Record<CT6ProblemCode, ExecutionState>> = {
  CT6_MALFORMED_JSON: "schema_error",
  CT6_VERSION_CONFLICT: "schema_error",
  CT6_REQUEST_TOO_LARGE: "too_large",
  CT6_SCHEMA_VALIDATION: "schema_error",
  CT6_DOMAIN_VALIDATION: "domain_error",
  CT6_CONTRACT_BLOCKED: "contract_blocked",
  CT6_INTERNAL_ERROR: "server_error",
  CT6_NOT_READY: "server_error",
};

export function executionStateForProblem(problem: CT6Problem): ExecutionState {
  if (problem.code === "CT8_PILOT_LIMIT") return "pilot_limit";
  if (problem.code === "CT8_PILOT_AUTH" || problem.code === "CT8_PRIVATE_AUTH") return "pilot_access";
  if (problem.code === "CT8_PILOT_BUSY") return "pilot_busy";
  if (problem.code === "CT8_PILOT_INPUT") return "schema_error";
  if (problem.code === "CT8_PILOT_CONTRACT") return "contract_blocked";
  return stateByCode[problem.code as CT6ProblemCode] ?? "server_error";
}

export function resultFreshnessAfterEdit(hasPriorSuccess: boolean): ResultFreshness {
  return hasPriorSuccess ? "stale" : "none";
}
