import { readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const dist = join(root, "dist");
const files = [];
function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) walk(path); else files.push(path);
  }
}
walk(dist);
const forbiddenNames = files.filter((path) => /(?:\.map|\.env|\.pem|\.key)$/i.test(path));
const textFiles = files.filter((path) => [".html", ".js", ".css", ".json"].includes(extname(path)));
const forbiddenContent = /(?:BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|\/workspace\/|C:\\Aasif\\|VITE_.*(?:SECRET|TOKEN|KEY))/;
const leaked = textFiles.filter((path) => forbiddenContent.test(readFileSync(path, "utf8")));
const compiled = textFiles.filter((path) => extname(path) === ".js")
  .map((path) => readFileSync(path, "utf8")).join("\n");
if (forbiddenNames.length || leaked.length) {
  throw new Error(`CT7 production-build audit failed: ${[...forbiddenNames, ...leaked].join(", ")}`);
}
if (process.env.VITE_CT8_PILOT_MODE === "true" && process.env.VITE_CT8_NOCARD_MODE !== "true") {
  const origin = process.env.VITE_CT6_API_BASE_URL ?? "";
  if (!/^https:\/\/[a-z0-9.-]+$/i.test(origin))
    throw new Error("CT8 pilot build requires an exact HTTPS API origin");
  if (!compiled.includes(origin) || !compiled.includes("/api/pilot/v1") ||
      compiled.includes("localhost:8000"))
    throw new Error("CT8 pilot build has an unreviewed origin or route");
}
if (process.env.VITE_CT8_NOCARD_MODE === "true" && process.env.VITE_CT8_PILOT_MODE !== "true") {
  throw new Error("no-card mode requires a separate CT8 pilot build");
}
if (process.env.VITE_CT8_NOCARD_MODE === "true") {
  if (process.env.VITE_CT6_API_BASE_URL || !compiled.includes("/api/pilot/v1") ||
      !compiled.includes("/auth/session") || !compiled.includes("/auth/start") ||
      compiled.includes("localhost:8000") || compiled.includes(".onrender.com"))
    throw new Error("no-card build requires relative same-origin API and auth routes");
}
const bytes = files.reduce((total, path) => total + statSync(path).size, 0);
console.log(`CT7 production-build audit: PASS (${files.length} files, ${bytes} bytes, no maps/secrets/local paths)`);
