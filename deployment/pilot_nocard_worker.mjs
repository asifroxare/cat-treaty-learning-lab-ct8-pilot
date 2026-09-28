/** Disabled-by-default no-card private pilot. Never use the Access Worker for this mode. */
const routes = new Map([
  ["/api/pilot/v1/capabilities", "GET"],
  ["/api/pilot/v1/runs/catalogue", "POST"],
  ["/api/pilot/v1/runs/hours-clause", "POST"],
]);
const pages = new Set(["/", "/guided", "/explore", "/hours-clause", "/compare", "/audit"]);
const sessionName = "__Host-CT8PilotSession";
const loginName = "__Host-CT8PilotLogin";
const encoder = new TextEncoder();
const discardLogin = `${loginName}=; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=0`;

function bytes64(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}
function from64(value) {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw Error("bad base64url");
  const padded = value.replaceAll("-", "+").replaceAll("_", "/");
  return Uint8Array.from(atob(padded + "=".repeat((4 - padded.length % 4) % 4)), c => c.charCodeAt(0));
}
function random64(size = 24) {
  return bytes64(crypto.getRandomValues(new Uint8Array(size)));
}
function hex(bytes) {
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}
async function key(value) {
  return crypto.subtle.importKey("raw", encoder.encode(value), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}
async function signed(payload, secret) {
  const content = bytes64(encoder.encode(JSON.stringify(payload)));
  const mac = await crypto.subtle.sign("HMAC", await key(secret), encoder.encode(content));
  return `${content}.${bytes64(mac)}`;
}
async function verifySigned(value, secret) {
  const bits = value?.split(".");
  if (bits?.length !== 2 || bits[0].length > 1024 || bits[1].length > 100) return null;
  try {
    const ok = await crypto.subtle.verify("HMAC", await key(secret), from64(bits[1]), encoder.encode(bits[0]));
    return ok ? JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(from64(bits[0]))) : null;
  } catch { return null; }
}
function cookie(request, name) {
  const matches = (request.headers.get("Cookie") ?? "").split(";").map(s => s.trim())
    .filter(s => s.startsWith(name + "="));
  return matches.length === 1 ? matches[0].slice(name.length + 1) : null;
}
function security(headers = {}) {
  return { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000", ...headers };
}
function deny(status = 401) {
  return new Response("Private pilot access required", { status, headers: security() });
}
function failedCallback(status = 401) {
  return new Response("Private pilot access required", { status, headers: security({ "Set-Cookie": discardLogin }) });
}
function randomSecret(value) {
  try {
    if (typeof value !== "string" || value.length < 43 || value.length > 256) return false;
    const raw = from64(value);
    return raw.length >= 32 && bytes64(raw) === value && new Set(raw).size >= 16 &&
      new Set(raw.slice(0, 32)).size >= 16;
  } catch { return false; }
}
function configured(env, hostname) {
  const ids = (env.PILOT_ID_ALLOWLIST ?? "").split(",");
  return env.PILOT_NOCARD_ENABLED === "true" && env.PILOT_PUBLIC_HOST === hostname &&
    /^[a-z0-9-]+\.onrender\.com$/.test(env.PILOT_ORIGIN_HOST ?? "") &&
    /^[a-z0-9-]+\.asif-rox\.workers\.dev$/.test(hostname) &&
    [env.PILOT_ASSERTION_KEY, env.PILOT_SESSION_KEY, env.PILOT_LOGIN_KEY].every(randomSecret) &&
    new Set([env.PILOT_ASSERTION_KEY, env.PILOT_SESSION_KEY, env.PILOT_LOGIN_KEY]).size === 3 &&
    /^[A-Za-z0-9_-]{1,32}$/.test(env.PILOT_ASSERTION_KEY_ID ?? "") &&
    typeof env.PILOT_OAUTH_CLIENT_SECRET === "string" && env.PILOT_OAUTH_CLIENT_SECRET.length >= 32 &&
    env.PILOT_OAUTH_CLIENT_SECRET.length <= 256 &&
    /^[A-Za-z0-9._-]{5,128}$/.test(env.PILOT_OAUTH_CLIENT_ID ?? "") &&
    /^[a-zA-Z0-9_-]{8,64}$/.test(env.PILOT_EPOCH ?? "") &&
    ids.length > 0 && ids.length <= 25 && ids.every(s => /^[1-9][0-9]{0,19}$/.test(s)) &&
    Number.isInteger(Number(env.PILOT_MAX_BODY_BYTES)) &&
    Number(env.PILOT_MAX_BODY_BYTES) >= 1 && Number(env.PILOT_MAX_BODY_BYTES) <= 1048576 &&
    typeof env.PILOT_RATE_LIMITER?.limit === "function";
}
async function admitted(env, request, label, uid = "") {
  try {
    const ip = request.headers.get("CF-Connecting-IP") ?? "unknown";
    return (await env.PILOT_RATE_LIMITER.limit({ key: `${label}:${uid || ip}` }))?.success === true;
  } catch { return false; }
}
async function identity(request, env) {
  const payload = await verifySigned(cookie(request, sessionName), env.PILOT_SESSION_KEY);
  const now = Math.floor(Date.now() / 1000);
  if (!payload || typeof payload !== "object" || !/^[1-9][0-9]{0,19}$/.test(payload.id ?? "") ||
      !Number.isInteger(payload.iat) || !Number.isInteger(payload.exp) ||
      payload.iat > now || payload.exp <= now || payload.exp - payload.iat > 900 ||
      payload.epoch !== env.PILOT_EPOCH || !/^[A-Za-z0-9_-]{32}$/.test(payload.csrf ?? "") ||
      !(env.PILOT_ID_ALLOWLIST ?? "").split(",").includes(payload.id)) return null;
  return payload;
}
async function limitedBody(request, limit) {
  const length = request.headers.get("Content-Length");
  if (length && (!/^\d+$/.test(length) || Number(length) > limit)) return null;
  const reader = request.body?.getReader();
  if (!reader) return null;
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) { await reader.cancel(); return null; }
    chunks.push(value);
  }
  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
  return body;
}
async function begin(request, env, origin) {
  if (!await admitted(env, request, "login")) return deny(429);
  const state = random64();
  const verifier = random64(32);
  const challenge = bytes64(await crypto.subtle.digest("SHA-256", encoder.encode(verifier)));
  const callback = `${origin}/auth/callback`;
  const params = new URLSearchParams({ client_id: env.PILOT_OAUTH_CLIENT_ID,
    redirect_uri: callback, state, code_challenge: challenge, code_challenge_method: "S256" });
  const login = await signed({ state, verifier, exp: Math.floor(Date.now()/1000)+300 }, env.PILOT_LOGIN_KEY);
  return new Response(null, { status: 302, headers: security({
    Location: `https://github.com/login/oauth/authorize?${params}`,
    "Set-Cookie": `${loginName}=${login}; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=300`,
  }) });
}
async function callback(request, env, url, origin) {
  if (!await admitted(env, request, "callback")) return failedCallback(429);
  const state = await verifySigned(cookie(request, loginName), env.PILOT_LOGIN_KEY);
  const code = url.searchParams.get("code") ?? "";
  const received = url.searchParams.get("state") ?? "";
  if (url.searchParams.size !== 2 || !state || typeof state !== "object" ||
      state.exp <= Math.floor(Date.now()/1000) || state.exp > Math.floor(Date.now()/1000)+300 ||
      !/^[A-Za-z0-9_-]{43}$/.test(state.verifier ?? "") ||
      !/^[A-Za-z0-9_-]{32}$/.test(received) || received !== state.state ||
      !/^[A-Za-z0-9_-]{5,256}$/.test(code)) return failedCallback();
  try {
    const response = await fetch("https://github.com/login/oauth/access_token", {
      method: "POST", redirect: "manual", signal: AbortSignal.timeout(6000),
      headers: { Accept: "application/json", "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ client_id: env.PILOT_OAUTH_CLIENT_ID,
        client_secret: env.PILOT_OAUTH_CLIENT_SECRET, code,
        redirect_uri: `${origin}/auth/callback`, code_verifier: state.verifier }),
    });
    if (!response.ok) return failedCallback();
    const token = await response.json();
    if (!/^[A-Za-z0-9_]+$/.test(token.access_token ?? "") || token.scope) return failedCallback();
    const user = await fetch("https://api.github.com/user", {
      signal: AbortSignal.timeout(6000), redirect: "manual",
      headers: { Authorization: `Bearer ${token.access_token}`, Accept: "application/vnd.github+json",
        "User-Agent": "CT8-private-pilot" },
    });
    if (!user.ok) return failedCallback();
    const profile = await user.json();
    const id = String(profile.id);
    if (!Number.isSafeInteger(profile.id) || !(env.PILOT_ID_ALLOWLIST ?? "").split(",").includes(id)) return failedCallback();
    const now = Math.floor(Date.now()/1000);
    const session = await signed({ id, iat: now, exp: now+900, epoch: env.PILOT_EPOCH,
      csrf: random64() }, env.PILOT_SESSION_KEY);
    const headers = new Headers(security({ Location: "/" }));
    headers.append("Set-Cookie", discardLogin);
    headers.append("Set-Cookie", `${sessionName}=${session}; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=900`);
    return new Response(null, { status: 303, headers });
  } catch { return failedCallback(); }
}

async function readyBoot(env) {
  // A cold Render Free instance may take longer than the assertion's 15 s skew.
  // Wake it first, then sign for the specific process that answered readiness.
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const response = await fetch(`https://${env.PILOT_ORIGIN_HOST}/health/ready`, {
        redirect: "manual", signal: AbortSignal.timeout(attempt ? 10000 : 75000),
        headers: { "Cache-Control": "no-store" },
      });
      if (response.ok) {
        const data = await response.json();
        if (data.status === "ready" && /^[A-Za-z0-9_-]{32}$/.test(data.boot ?? "")) return data.boot;
      }
    } catch { /* Never forward an assertion without a current boot token. */ }
  }
  return null;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!configured(env, url.hostname) || url.protocol !== "https:") return deny(503);
    const origin = `https://${url.hostname}`;
    if (url.pathname === "/auth/start" && request.method === "GET" && !url.search)
      return begin(request, env, origin);
    if (url.pathname === "/auth/callback" && request.method === "GET")
      return callback(request, env, url, origin);
    if (url.pathname === "/auth/session" && request.method === "GET" && !url.search) {
      const who = await identity(request, env);
      return who ? Response.json({ authenticated: true, csrf: who.csrf }, { headers: security() }) : deny();
    }
    if (url.pathname === "/auth/logout" && request.method === "POST" && !url.search) {
      const who = await identity(request, env);
      if (!who || request.headers.get("Origin") !== origin ||
          request.headers.get("X-CT8-CSRF") !== who.csrf) return deny();
      return new Response(null, { status: 204, headers: security({
        "Set-Cookie": `${sessionName}=; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=0`,
      }) });
    }
    if (url.search || !routes.has(url.pathname)) {
      if (url.search || !["GET", "HEAD"].includes(request.method) ||
          (!pages.has(url.pathname) && !/^\/assets\/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:js|css|svg|png|woff2?)$/.test(url.pathname)) ||
          typeof env.ASSETS?.fetch !== "function") return new Response("Not found", { status: 404, headers: security() });
      const asset = await env.ASSETS.fetch(request);
      const headers = new Headers(asset.headers);
      for (const [name, value] of Object.entries(security())) headers.set(name, value);
      headers.set("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; " +
        "connect-src 'self'; img-src 'self' data:; font-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'");
      return new Response(asset.body, { status: asset.status, headers });
    }
    const expected = routes.get(url.pathname);
    const who = await identity(request, env);
    if (request.method !== expected || !who) return deny();
    if (!await admitted(env, request, "api", who.id)) return deny(429);
    let body = null;
    if (expected === "POST") {
      if (request.headers.get("Origin") !== origin || request.headers.get("X-CT8-CSRF") !== who.csrf ||
          request.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase() !== "application/json") return deny();
      body = await limitedBody(request, Number(env.PILOT_MAX_BODY_BYTES));
      if (!body) return deny(413);
    }
    const digest = hex(await crypto.subtle.digest("SHA-256", body ?? new Uint8Array()));
    const boot = await readyBoot(env);
    if (!boot) return new Response("Pilot temporarily unavailable", { status: 504, headers: security() });
    const timestamp = String(Math.floor(Date.now()/1000));
    const nonce = random64();
    const message = ["ct8.1", env.PILOT_ASSERTION_KEY_ID, expected, url.pathname, env.PILOT_ORIGIN_HOST,
      url.hostname, who.id, digest, timestamp, nonce, boot].join("\n");
    const signature = hex(await crypto.subtle.sign("HMAC", await key(env.PILOT_ASSERTION_KEY), encoder.encode(message)));
    const headers = new Headers({ "X-CT8-Assertion-Key": env.PILOT_ASSERTION_KEY_ID, "X-CT8-Assertion-ID": who.id,
      "X-CT8-Assertion-Nonce": nonce, "X-CT8-Assertion-Time": timestamp,
      "X-CT8-Assertion-Signature": signature, "X-CT8-Assertion-Digest": digest,
      "X-CT8-Assertion-Boot": boot });
    if (body) headers.set("Content-Type", "application/json");
    let upstream;
    try {
      upstream = await fetch(`https://${env.PILOT_ORIGIN_HOST}${url.pathname}`, {
        method: expected, headers, body, redirect: "manual", signal: AbortSignal.timeout(45000),
      });
    } catch {
      return new Response("Pilot temporarily unavailable", { status: 504, headers: security() });
    }
    const output = new Headers(upstream.headers);
    output.delete("Set-Cookie");
    for (const [name, value] of Object.entries(security())) output.set(name, value);
    output.delete("Access-Control-Allow-Origin");
    output.delete("Access-Control-Allow-Credentials");
    return new Response(upstream.body, { status: upstream.status, headers: output });
  },
};
