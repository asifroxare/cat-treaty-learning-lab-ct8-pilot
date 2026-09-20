import { createCT6Client } from "../api/client";
import type { CatalogueRunRequest, CT6Problem } from "../api/contract";

const request = {
  api_schema_version: "ct6.0",
  response_detail: "summary",
  input: {},
} as unknown as CatalogueRunRequest;

const successPayload = {
  api: {
    api_schema_version: "ct6.0",
    api_version: "ct6.0.0",
    completion_status: "complete",
    request_id: "server-request",
    client_request_id: null,
    run_mode: "catalogue",
  },
  identity: {},
  pre_capacity: {},
  post_capacity: {},
  learning: {},
  warnings: [],
};

function jsonResponse(payload: unknown, status = 200, requestId = "server-request"): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json", "X-Request-ID": requestId },
  });
}

function problem(code: string): CT6Problem {
  return {
    type: "https://edinsured.example/problems/test",
    title: "Static title",
    status: 422,
    code,
    detail: "Static detail",
    instance: "/api/v1/runs/catalogue",
    request_id: "problem-request",
    errors: [],
  };
}

describe("strict CT6 client", () => {
  it("posts catalogue input to the dedicated route and propagates request ID", async () => {
    const transport = vi.fn(async () => jsonResponse(successPayload));
    const client = createCT6Client("https://api.example.test", transport);
    const result = await client.runCatalogue(request, "client-request");

    expect(transport).toHaveBeenCalledWith(
      "https://api.example.test/api/v1/runs/catalogue",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "X-Request-ID": "client-request" }),
      }),
    );
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.requestId).toBe("server-request");
  });

  it("maps structured CT6 failures by stable code", async () => {
    const transport = vi.fn(async () => jsonResponse(problem("CT6_CONTRACT_BLOCKED"), 422));
    const result = await createCT6Client("https://api.example.test", transport).runCatalogue(request);
    expect(result).toMatchObject({ ok: false, state: "contract_blocked" });
  });

  it("maps network failure to offline without fabricating a problem", async () => {
    const transport = vi.fn(async () => { throw new TypeError("network unavailable"); });
    const result = await createCT6Client("https://api.example.test", transport).runCatalogue(request);
    expect(result).toEqual({ ok: false, state: "offline", problem: null, requestId: null });
  });

  it("fails malformed or unrecognized error payloads closed", async () => {
    const malformed = vi.fn(async () => new Response("not-json", { status: 500 }));
    const unknown = vi.fn(async () => jsonResponse({ message: "unexpected" }, 418));
    await expect(createCT6Client("https://api.example.test", malformed).runCatalogue(request))
      .resolves.toMatchObject({ ok: false, state: "server_error", problem: null });
    await expect(createCT6Client("https://api.example.test", unknown).runCatalogue(request))
      .resolves.toMatchObject({ ok: false, state: "server_error", problem: null });
  });

  it("fails an incomplete HTTP 200 body closed", async () => {
    const transport = vi.fn(async () => jsonResponse({ api: { request_id: "partial" } }));
    const result = await createCT6Client("https://api.example.test", transport).runCatalogue(request);
    expect(result).toMatchObject({ ok: false, state: "server_error", problem: null });
  });
});
