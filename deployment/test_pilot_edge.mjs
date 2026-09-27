import assert from "node:assert/strict";
import test from "node:test";
import pilot from "./pilot_edge_worker.mjs";

const env = {
  PILOT_PUBLIC_HOST: "pilot-api.example.org",
  PILOT_ORIGIN_HOST: "pilot-origin.example.org",
  PILOT_UI_ORIGIN: "https://pilot-ui.example.org",
  PILOT_ORIGIN_SECRET: "an-example-only-secret-longer-than-thirty-two-chars",
};
const url = "https://pilot-api.example.org/api/pilot/v1/runs/catalogue";
test("only explicit pilot paths reach origin; proof is replaced", async () => {
  const original = globalThis.fetch;
  let forwarded;
  globalThis.fetch = async (request) => {
    forwarded = request;
    return new Response("ok", { status: 200 });
  };
  try {
    const unauthorized = await pilot.fetch(new Request(url, { method: "POST" }), env);
    assert.equal(unauthorized.status, 401);
    const frozen = await pilot.fetch(new Request(url.replace("/api/pilot/v1", "/api/v1"),
      { method: "POST", headers: { "Cf-Access-Jwt-Assertion": "valid-looking" } }), env);
    assert.equal(frozen.status, 404);
    assert.equal(forwarded, undefined);
    const accepted = await pilot.fetch(new Request(url, { method: "POST",
      headers: { "Cf-Access-Jwt-Assertion": "valid-looking", "X-CT8-Pilot-Origin": "attacker" },
      body: "{}" }), env);
    assert.equal(accepted.status, 200);
    assert.equal(new URL(forwarded.url).hostname, env.PILOT_ORIGIN_HOST);
    assert.equal(forwarded.headers.get("X-CT8-Pilot-Origin"), env.PILOT_ORIGIN_SECRET);
  } finally { globalThis.fetch = original; }
});
