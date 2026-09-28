import assert from "node:assert/strict";
import test from "node:test";
import pilot from "./pilot_nocard_worker.mjs";

const host = "ct8-cat.asif-rox.workers.dev";
const root = `https://${host}`;
const env = {
  PILOT_NOCARD_ENABLED: "true", PILOT_PUBLIC_HOST: host,
  PILOT_ORIGIN_HOST: "cat-treaty-learning-lab-ct8-pilot.onrender.com",
  PILOT_ASSERTION_KEY: "a".repeat(64), PILOT_SESSION_KEY: "b".repeat(64),
  PILOT_LOGIN_KEY: "c".repeat(64), PILOT_OAUTH_CLIENT_SECRET: "d".repeat(40),
  PILOT_OAUTH_CLIENT_ID: "Iv1.abcdef012345", PILOT_ID_ALLOWLIST: "12345",
  PILOT_EPOCH: "reviewonly2026", PILOT_MAX_BODY_BYTES: "4096",
  PILOT_RATE_LIMITER: { limit: async () => ({ success: true }) },
  ASSETS: { fetch: async () => new Response("static pilot shell") },
};

test("unknown routes and missing identity never reach Render", async () => {
  const prior = globalThis.fetch;
  let forwarded = 0;
  globalThis.fetch = async () => { forwarded++; return new Response("bad"); };
  try {
    assert.equal((await pilot.fetch(new Request(`${root}/api/v1/runs/catalogue`), env)).status, 404);
    assert.equal((await pilot.fetch(new Request(`${root}/api/pilot/v1/runs/catalogue`,
      { method: "POST", body: "{}", headers: { Origin: root } }), env)).status, 401);
    assert.equal((await pilot.fetch(new Request(`${root}/unknown`), env)).status, 404);
    assert.equal((await pilot.fetch(new Request(`${root}/auth/session`), env)).status, 401);
    assert.equal((await pilot.fetch(new Request(`${root}/guided`), env)).status, 200);
    assert.equal(forwarded, 0);
  } finally { globalThis.fetch = prior; }
});

test("GitHub PKCE login, revocation, CSRF and signed forwarding", async () => {
  const prior = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push([url, options]);
    if (url === "https://github.com/login/oauth/access_token")
      return Response.json({ access_token: "gho_reviewonly", scope: "" });
    if (url === "https://api.github.com/user") return Response.json({ id: 12345 });
    return Response.json({ ok: true });
  };
  try {
    const login = await pilot.fetch(new Request(`${root}/auth/start`), env);
    assert.equal(login.status, 302);
    const authorize = new URL(login.headers.get("Location"));
    assert.equal(authorize.hostname, "github.com");
    assert.equal(authorize.searchParams.get("code_challenge_method"), "S256");
    assert.equal(authorize.searchParams.has("scope"), false);
    const startCookie = login.headers.get("Set-Cookie").split(";", 1)[0];
    assert.match(login.headers.get("Set-Cookie"), /SameSite=Lax/);
    const callback = `${root}/auth/callback?state=${authorize.searchParams.get("state")}&code=reviewCode1`;
    assert.equal((await pilot.fetch(new Request(callback.replace("reviewCode1", "bad?"),
      { headers: { Cookie: startCookie } }), env)).status, 401);
    const successful = await pilot.fetch(new Request(callback, { headers: { Cookie: startCookie } }), env);
    assert.equal(successful.status, 303);
    assert.equal(calls.length, 2);
    const session = successful.headers.getSetCookie().find(v => v.startsWith("__Host-CT8PilotSession="));
    assert.ok(session);
    const cookie = session.split(";", 1)[0];
    const logged = await pilot.fetch(new Request(`${root}/auth/session`, { headers: { Cookie: cookie } }), env);
    assert.equal(logged.status, 200);
    const csrf = (await logged.json()).csrf;
    const path = "/api/pilot/v1/runs/catalogue";
    const headers = { Cookie: cookie, Origin: root, "Content-Type": "application/json", "X-CT8-CSRF": csrf,
      "X-CT8-Assertion-Signature": "client-forgery" };
    assert.equal((await pilot.fetch(new Request(root+path, { method: "POST", body: "{}",
      headers: { ...headers, Origin: "https://edinsured-live.asif-rox.workers.dev" } }), env)).status, 401);
    assert.equal((await pilot.fetch(new Request(root+path, { method: "POST", body: "{}",
      headers: { ...headers, Cookie: `${cookie}; ${cookie}` } }), env)).status, 401);
    const allowed = await pilot.fetch(new Request(root+path, { method: "POST", body: "{}", headers }), env);
    assert.equal(allowed.status, 200);
    const [forwarded, options] = calls.at(-1);
    assert.equal(new URL(forwarded).hostname, env.PILOT_ORIGIN_HOST);
    assert.notEqual(options.headers.get("X-CT8-Assertion-Signature"), "client-forgery");
    assert.equal(options.headers.has("Cookie"), false);
    assert.equal(options.headers.get("X-CT8-Assertion-ID"), "12345");
    assert.equal((await pilot.fetch(new Request(root+path, { method: "POST", body: "{}", headers }),
      { ...env, PILOT_ID_ALLOWLIST: "99999" })).status, 401);
  } finally { globalThis.fetch = prior; }
});
