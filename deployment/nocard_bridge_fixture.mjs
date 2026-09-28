/** Test-only: pass one frozen synthetic request through Worker authentication. */
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import pilot from "./pilot_nocard_worker.mjs";

const publicHost = "ct8-cat.asif-rox.workers.dev";
const env = {
  PILOT_NOCARD_ENABLED: "true", PILOT_PUBLIC_HOST: publicHost,
  PILOT_ORIGIN_HOST: "cat-treaty-learning-lab-ct8-pilot.onrender.com",
  PILOT_ASSERTION_KEY: createHash("sha256").update("review-only-assertion-key").digest("base64url"),
  PILOT_ASSERTION_KEY_ID: "k1",
  PILOT_SESSION_KEY: createHash("sha256").update("review-session-key").digest("base64url"),
  PILOT_LOGIN_KEY: createHash("sha256").update("review-login-key").digest("base64url"),
  PILOT_OAUTH_CLIENT_SECRET: "c".repeat(40),
  PILOT_OAUTH_CLIENT_ID: "Iv1.abcdef012345", PILOT_ID_ALLOWLIST: "12345",
  PILOT_EPOCH: "reviewonly2026", PILOT_MAX_BODY_BYTES: "4096",
  PILOT_RATE_LIMITER: { limit: async () => ({ success: true }) },
};
const origin = `https://${publicHost}`;
let forwarded = null;
globalThis.fetch = async (url, options) => {
  if (url === `https://${env.PILOT_ORIGIN_HOST}/health/ready`)
    return Response.json({ status: "ready", boot: process.env.CT8_TEST_BOOT });
  if (url === "https://github.com/login/oauth/access_token")
    return Response.json({ access_token: "gho_reviewonly", scope: "" });
  if (url === "https://api.github.com/user") return Response.json({ id: 12345 });
  forwarded = { url, method: options.method, headers: Object.fromEntries(options.headers),
    body: options.body ? new TextDecoder().decode(options.body) : "" };
  return Response.json({ ok: true });
};
const login = await pilot.fetch(new Request(`${origin}/auth/start`), env);
const authorize = new URL(login.headers.get("Location"));
const prelogin = login.headers.get("Set-Cookie").split(";", 1)[0];
const callback = await pilot.fetch(new Request(`${origin}/auth/callback?state=${authorize.searchParams.get("state")}&code=reviewCode1`,
  { headers: { Cookie: prelogin } }), env);
const session = callback.headers.getSetCookie().find(v => v.startsWith("__Host-CT8PilotSession="))?.split(";", 1)[0];
const sessionReply = await pilot.fetch(new Request(`${origin}/auth/session`, { headers: { Cookie: session } }), env);
const csrf = (await sessionReply.json()).csrf;
const route = process.argv[2];
if (!(["catalogue", "hours-clause"].includes(route))) throw Error("test route required");
const body = readFileSync(new URL(`./fixtures/ct7/approved-${route}.json`, import.meta.url));
const response = await pilot.fetch(new Request(`${origin}/api/pilot/v1/runs/${route}`, {
  method: "POST", body, headers: { Cookie: session, Origin: origin,
    "X-CT8-CSRF": csrf, "Content-Type": "application/json" },
}), env);
if (response.status !== 200 || !forwarded) throw Error("Worker forwarding failed");
process.stdout.write(JSON.stringify(forwarded));
