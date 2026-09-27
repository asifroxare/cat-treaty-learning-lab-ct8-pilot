import assert from "node:assert/strict";
import test from "node:test";
import pilot from "./pilot_edge_worker.mjs";

const env = {
  PILOT_PUBLIC_HOST: "pilot-api.example.org",
  PILOT_ORIGIN_HOST: "pilot-origin.example.org",
  PILOT_UI_ORIGIN: "https://pilot-ui.example.org",
  PILOT_ORIGIN_SECRET: "an-example-only-secret-longer-than-thirty-two-chars",
  PILOT_RATE_LIMITER: { limit: async () => ({ success: true }) },
  ASSETS: { fetch: async () => new Response("ui", { status: 200 }) },
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

test("same-origin UI uses protected assets; forbidden API paths never fall through", async () => {
  let assetCalls = 0;
  const assets = { fetch: async () => { assetCalls++; return new Response("ui", { status: 200 }); } };
  const server = { ...env, ASSETS: assets };
  const root = `https://${env.PILOT_PUBLIC_HOST}`;
  const ui = await pilot.fetch(new Request(`${root}/guided`), server);
  assert.equal(ui.status, 200);
  assert.equal(ui.headers.get("X-Content-Type-Options"), "nosniff");
  assert.ok(ui.headers.get("Content-Security-Policy").includes("connect-src 'self'"));
  assert.equal((await pilot.fetch(new Request(`${root}/assets/index-Ab_2.css`), server)).status, 200);
  assert.equal((await pilot.fetch(new Request(`${root}/api/v1/runs/catalogue`), server)).status, 404);
  assert.equal((await pilot.fetch(new Request(`${root}/api/pilot/v1/runs/other`), server)).status, 404);
  assert.equal((await pilot.fetch(new Request(`${root}/unknown`), server)).status, 404);
  assert.equal(assetCalls, 2);
});

test("calculation binding fails closed without forwarding, while preflight stays available", async () => {
  const original = globalThis.fetch;
  let forwarded = 0;
  globalThis.fetch = async () => { forwarded++; return new Response("ok"); };
  const authenticated = { "Cf-Access-Jwt-Assertion": "edge-assertion" };
  try {
    const denied = await pilot.fetch(new Request(url, { method: "POST", headers: authenticated }),
      { ...env, PILOT_RATE_LIMITER: { limit: async () => ({ success: false }) } });
    assert.equal(denied.status, 429);
    assert.equal(forwarded, 0);
    const absent = await pilot.fetch(new Request(url, { method: "POST", headers: authenticated }),
      { ...env, PILOT_RATE_LIMITER: undefined });
    assert.equal(absent.status, 503);
    const broken = await pilot.fetch(new Request(url, { method: "POST", headers: authenticated }),
      { ...env, PILOT_RATE_LIMITER: { limit: async () => { throw Error("private provider error"); } } });
    assert.equal(broken.status, 503);
    assert.equal((await broken.text()).includes("private"), false);
    const preflight = await pilot.fetch(new Request(url, { method: "OPTIONS", headers: {
      Origin: env.PILOT_UI_ORIGIN, "Access-Control-Request-Method": "POST",
    } }), { ...env, PILOT_RATE_LIMITER: undefined });
    assert.equal(preflight.status, 204);
    assert.equal(forwarded, 0);
  } finally { globalThis.fetch = original; }
});
