import type { CT6Problem } from "../api/contract";
import { executionStateForProblem, resultFreshnessAfterEdit } from "../api/runState";

const expectedStates = {
  CT6_MALFORMED_JSON: "schema_error",
  CT6_VERSION_CONFLICT: "schema_error",
  CT6_REQUEST_TOO_LARGE: "too_large",
  CT6_SCHEMA_VALIDATION: "schema_error",
  CT6_DOMAIN_VALIDATION: "domain_error",
  CT6_CONTRACT_BLOCKED: "contract_blocked",
  CT6_INTERNAL_ERROR: "server_error",
  CT6_NOT_READY: "server_error",
} as const;

function problem(code: string): CT6Problem {
  return {
    type: "https://edinsured.example/problems/test",
    title: "Static title",
    status: 422,
    code,
    detail: "Static detail",
    instance: "/api/v1/runs/catalogue",
    request_id: "request-1",
    errors: [],
  };
}

describe("frozen CT6 problem mapping", () => {
  it.each(Object.entries(expectedStates))("maps %s to %s", (code, state) => {
    expect(executionStateForProblem(problem(code))).toBe(state);
  });

  it("fails an unknown problem code closed", () => {
    expect(executionStateForProblem(problem("CT6_FUTURE_CODE"))).toBe("server_error");
  });

  it("marks only an existing successful result stale after edit", () => {
    expect(resultFreshnessAfterEdit(true)).toBe("stale");
    expect(resultFreshnessAfterEdit(false)).toBe("none");
  });
});
