import { acceptAuthoritativeResponse, type AuthoritativeSuccessResponse } from "./authoritative";
import { CT6_API_BASE_URL, CT8_PILOT_MODE } from "./config";
import type { CatalogueRunRequest, CT6Problem, HoursRunRequest } from "./contract";
import { executionStateForProblem, type ExecutionState } from "./runState";
import type { components } from "./generated/ct6";

type RawSuccessResponse = components["schemas"]["CT6SuccessResponse"];

export type RunSuccess = {
  readonly ok: true;
  readonly data: AuthoritativeSuccessResponse;
  readonly requestId: string;
};

export type RunFailure = {
  readonly ok: false;
  readonly state: ExecutionState;
  readonly problem: CT6Problem | null;
  readonly requestId: string | null;
};

export type RunResult = RunSuccess | RunFailure;

export type FetchTransport = typeof fetch;

export interface CT6Client {
  runCatalogue(request: CatalogueRunRequest, requestId?: string): Promise<RunResult>;
  runHoursClause(request: HoursRunRequest, requestId?: string): Promise<RunResult>;
}

function isProblem(value: unknown): value is CT6Problem {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<CT6Problem>;
  return typeof candidate.code === "string"
    && typeof candidate.status === "number"
    && typeof candidate.request_id === "string";
}

function isSuccessResponse(value: unknown): value is RawSuccessResponse {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<RawSuccessResponse>;
  return typeof candidate.api === "object"
    && candidate.api !== null
    && candidate.api.api_schema_version === "ct6.0"
    && candidate.api.api_version === "ct6.0.0"
    && candidate.api.completion_status === "complete"
    && typeof candidate.identity === "object"
    && candidate.identity !== null
    && typeof candidate.pre_capacity === "object"
    && candidate.pre_capacity !== null
    && typeof candidate.post_capacity === "object"
    && candidate.post_capacity !== null
    && typeof candidate.learning === "object"
    && candidate.learning !== null
    && Array.isArray(candidate.warnings);
}

export function createCT6Client(
  baseUrl = CT6_API_BASE_URL,
  transport: FetchTransport = fetch,
): CT6Client {
  const normalizedBaseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;

  async function run(path: string, body: CatalogueRunRequest | HoursRunRequest, requestId?: string): Promise<RunResult> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (requestId) headers["X-Request-ID"] = requestId;

    let response: Response;
    try {
      response = await transport(`${normalizedBaseUrl}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      ...(CT8_PILOT_MODE ? { credentials: "include" as const } : {}),
      });
    } catch {
      return { ok: false, state: "offline", problem: null, requestId: null };
    }

    const responseRequestId = response.headers.get("X-Request-ID");
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      return { ok: false, state: "server_error", problem: null, requestId: responseRequestId };
    }

    if (response.ok && isSuccessResponse(payload)) {
      return {
        ok: true,
        data: acceptAuthoritativeResponse(payload),
        requestId: responseRequestId ?? payload.api.request_id,
      };
    }

    if (response.ok) {
      return { ok: false, state: "server_error", problem: null, requestId: responseRequestId };
    }

    if (!isProblem(payload)) {
      return { ok: false, state: "server_error", problem: null, requestId: responseRequestId };
    }
    return {
      ok: false,
      state: executionStateForProblem(payload),
      problem: payload,
      requestId: responseRequestId ?? payload.request_id,
    };
  }

  return {
    runCatalogue: (request, requestId) => run(`${CT8_PILOT_MODE ? "/api/pilot/v1" : "/api/v1"}/runs/catalogue`, request, requestId),
    runHoursClause: (request, requestId) => run(`${CT8_PILOT_MODE ? "/api/pilot/v1" : "/api/v1"}/runs/hours-clause`, request, requestId),
  };
}
