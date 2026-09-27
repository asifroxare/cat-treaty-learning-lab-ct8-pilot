/** Minimal invited-pilot proxy; configure Access on its public hostname. */
const paths = new Map([
  ["/api/pilot/v1/runs/catalogue", "POST"],
  ["/api/pilot/v1/runs/hours-clause", "POST"],
  ["/api/pilot/v1/capabilities", "GET"],
]);

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    if (!env.PILOT_PUBLIC_HOST || !env.PILOT_ORIGIN_HOST ||
        !env.PILOT_ORIGIN_SECRET || env.PILOT_ORIGIN_SECRET.length < 32 ||
        !env.PILOT_UI_ORIGIN || incoming.hostname !== env.PILOT_PUBLIC_HOST ||
        !paths.has(incoming.pathname) || incoming.search) {
      return new Response("Not found", { status: 404 });
    }
    const expected = paths.get(incoming.pathname);
    const cors = {
      "Access-Control-Allow-Origin": env.PILOT_UI_ORIGIN,
      "Access-Control-Allow-Credentials": "true",
      "Vary": "Origin",
      "Cache-Control": "no-store",
    };
    if (request.method === "OPTIONS" && request.headers.get("Origin") === env.PILOT_UI_ORIGIN &&
        request.headers.get("Access-Control-Request-Method") === expected) {
      return new Response(null, { status: 204, headers: { ...cors,
        "Access-Control-Allow-Methods": expected,
        "Access-Control-Allow-Headers": "Content-Type,X-Request-ID" } });
    }
    if (request.method !== expected ||
        (request.headers.has("Origin") && request.headers.get("Origin") !== env.PILOT_UI_ORIGIN) ||
        !request.headers.get("Cf-Access-Jwt-Assertion")) {
      return new Response("Not authorized", { status: 401, headers: { "Cache-Control": "no-store" } });
    }
    const destination = new URL(request.url);
    destination.hostname = env.PILOT_ORIGIN_HOST;
    destination.protocol = "https:";
    destination.port = "";
    const headers = new Headers(request.headers);
    for (const name of ["Host", "Forwarded", "X-Forwarded-Host", "X-Forwarded-Proto"])
      headers.delete(name);
    headers.delete("X-CT8-Pilot-Origin");
    headers.set("X-CT8-Pilot-Origin", env.PILOT_ORIGIN_SECRET);
    // Worker overrides an incoming proof; the Python API verifies both the
    // independent proof and the Access signature before reading a body.
    const upstream = new Request(destination, request);
    const forwarded = new Request(upstream, { headers, redirect: "manual" });
    const response = await fetch(forwarded);
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("Cache-Control", "no-store");
    responseHeaders.set("Access-Control-Allow-Origin", env.PILOT_UI_ORIGIN);
    responseHeaders.set("Access-Control-Allow-Credentials", "true");
    responseHeaders.set("Vary", "Origin");
    return new Response(response.body, { status: response.status, headers: responseHeaders });
  },
};
