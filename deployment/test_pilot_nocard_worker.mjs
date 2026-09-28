import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import pilot from "./pilot_nocard_worker.mjs";

const host = "ct8-cat.asif-rox.workers.dev";
const root = `https://${host}`;
const env = {
  PILOT_NOCARD_ENABLED: "true", PILOT_PUBLIC_HOST: host,
  PILOT_ORIGIN_HOST: "cat-treaty-learning-lab-ct8-pilot.onrender.com",
  PILOT_ASSERTION_KEY: createHash("sha256").update("review-only-assertion-key").digest("base64url"),
  PILOT_ASSERTION_KEY_ID: "k1",
  PILOT_SESSION_KEY: createHash("sha256").update("review-session-key").digest("base64url"),
  PILOT_LOGIN_KEY: createHash("sha256").update("review-login-key").digest("base64url"),
  PILOT_OAUTH_CLIENT_SECRET: "d".repeat(40),
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
    if (url === `https://${env.PILOT_ORIGIN_HOST}/health/ready`)
      return Response.json({ status: "ready", boot: "b".repeat(32) });
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
    const unexpectedIssuer = await pilot.fetch(new Request(`${callback}&iss=https%3A%2F%2Fevil.example`,
      { headers: { Cookie: startCookie } }), env);
    assert.equal(unexpectedIssuer.status, 401);
    const duplicateIssuer = await pilot.fetch(new Request(`${callback}&iss=https%3A%2F%2Fgithub.com%2Flogin%2Foauth&iss=https%3A%2F%2Fgithub.com%2Flogin%2Foauth`,
      { headers: { Cookie: startCookie } }), env);
    assert.equal(duplicateIssuer.status, 401);
    const successful = await pilot.fetch(new Request(`${callback}&iss=https%3A%2F%2Fgithub.com%2Flogin%2Foauth`,
      { headers: { Cookie: startCookie } }), env);
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
    assert.equal(options.headers.get("X-CT8-Assertion-Boot"), "b".repeat(32));
    assert.equal((await pilot.fetch(new Request(root+path, { method: "POST", body: "{}", headers }),
      { ...env, PILOT_ID_ALLOWLIST: "99999" })).status, 401);
  } finally { globalThis.fetch = prior; }
});

test("cold start signs after readiness and handles an upstream timeout", async () => {
  const prior = globalThis.fetch;
  const priorClock = Date.now;
  let now = 1_800_000_000_000;
  Date.now = () => now;
  let forwarded = null;
  globalThis.fetch = async (url, options) => {
    if (url === "https://github.com/login/oauth/access_token")
      return Response.json({ access_token: "gho_reviewonly", scope: "" });
    if (url === "https://api.github.com/user") return Response.json({ id: 12345 });
    if (url.endsWith("/health/ready")) {
      now += 25_000; // Simulate a Render Free cold start after browser admission.
      return Response.json({ status: "ready", boot: "r".repeat(32) });
    }
    forwarded = options.headers;
    throw new DOMException("upstream timeout", "TimeoutError");
  };
  try {
    const login = await pilot.fetch(new Request(`${root}/auth/start`), env);
    const state = new URL(login.headers.get("Location")).searchParams.get("state");
    const callback = await pilot.fetch(new Request(`${root}/auth/callback?state=${state}&code=reviewCode1`,
      { headers: { Cookie: login.headers.get("Set-Cookie").split(";", 1)[0] } }), env);
    const session = callback.headers.getSetCookie().find(v => v.startsWith("__Host-CT8PilotSession="))?.split(";", 1)[0];
    const identity = await pilot.fetch(new Request(`${root}/auth/session`, { headers: { Cookie: session } }), env);
    const csrf = (await identity.json()).csrf;
    const response = await pilot.fetch(new Request(`${root}/api/pilot/v1/runs/catalogue`, {
      method: "POST", body: "{}", headers: { Cookie: session, Origin: root,
        "X-CT8-CSRF": csrf, "Content-Type": "application/json" },
    }), env);
    assert.equal(response.status, 504);
    assert.equal(forwarded.get("X-CT8-Assertion-Time"), String(Math.floor(now / 1000)));
    assert.equal(forwarded.get("X-CT8-Assertion-Boot"), "r".repeat(32));
  } finally { globalThis.fetch = prior; Date.now = priorClock; }
});

test("all callback denials clear the browser's login cookie", async () => {
  const prior = globalThis.fetch;
  try {
    const login = await pilot.fetch(new Request(`${root}/auth/start`), env);
    const state = new URL(login.headers.get("Location")).searchParams.get("state");
    const sessionCookie = login.headers.get("Set-Cookie").split(";", 1)[0];
    const invalid = await pilot.fetch(new Request(`${root}/auth/callback?state=${state}&code=bad?`,
      { headers: { Cookie: sessionCookie } }), env);
    assert.equal(invalid.status, 401);
    assert.match(invalid.headers.get("Set-Cookie"), /Max-Age=0/);
    globalThis.fetch = async () => Response.json({ error: "bad_verification_code" }, { status: 401 });
    const rejected = await pilot.fetch(new Request(`${root}/auth/callback?state=${state}&code=reviewCode1`,
      { headers: { Cookie: sessionCookie } }), env);
    assert.equal(rejected.status, 401);
    assert.match(rejected.headers.get("Set-Cookie"), /Max-Age=0/);
    assert.equal((await pilot.fetch(new Request(`${root}/guided`), {
      ...env, PILOT_ASSERTION_KEY: "a".repeat(64),
    })).status, 503);
  } finally { globalThis.fetch = prior; }
});

test("public-test switch admits a new GitHub ID but private mode still denies it", async () => {
  const prior = globalThis.fetch;
  globalThis.fetch = async (url) => {
    if (url === "https://github.com/login/oauth/access_token")
      return Response.json({ access_token: "gho_reviewonly", scope: "" });
    if (url === "https://api.github.com/user") return Response.json({ id: 98765 });
    throw Error("unexpected request");
  };
  try {
    async function login(settings) {
      const start = await pilot.fetch(new Request(`${root}/auth/start`), settings);
      const state = new URL(start.headers.get("Location")).searchParams.get("state");
      return pilot.fetch(new Request(`${root}/auth/callback?code=reviewCode1&state=${state}&iss=https%3A%2F%2Fgithub.com%2Flogin%2Foauth`,
        { headers: { Cookie: start.headers.get("Set-Cookie").split(";", 1)[0] } }), settings);
    }
    assert.equal((await login(env)).status, 401);
    const open = await login({ ...env, PILOT_PUBLIC_TEST_ENABLED: "true" });
    assert.equal(open.status, 303);
    const session = open.headers.getSetCookie().find(value => value.startsWith("__Host-CT8PilotSession="));
    assert.ok(session);
    assert.equal((await pilot.fetch(new Request(`${root}/auth/session`, {
      headers: { Cookie: session.split(";", 1)[0] },
    }), { ...env, PILOT_PUBLIC_TEST_ENABLED: "true" })).status, 200);
    assert.equal((await pilot.fetch(new Request(`${root}/auth/session`, {
      headers: { Cookie: session.split(";", 1)[0] },
    }), env)).status, 401);
  } finally { globalThis.fetch = prior; }
});
