import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const sourceRoot = fileURLToPath(new URL("../src", import.meta.url));
const violations = [];

function visit(directory) {
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) {
      visit(path);
      continue;
    }
    if (![".ts", ".tsx"].includes(extname(path))) continue;
    const name = relative(sourceRoot, path).replaceAll("\\", "/");
    if (name.startsWith("test/")) continue;
    const source = readFileSync(path, "utf8");
    if (!name.startsWith("api/") && source.includes("api/generated/ct6")) {
      violations.push(`${name}: generated CT6 transport types may only be imported inside src/api`);
    }
    if (/\beval\s*\(|dangerouslySetInnerHTML/.test(source)) {
      violations.push(`${name}: dynamic/raw HTML execution is forbidden`);
    }
    if (/\b(localStorage|sessionStorage|indexedDB|document\.cookie)\b/.test(source)) {
      violations.push(`${name}: browser persistence is forbidden in CT7 v1`);
    }
    if (/\bconsole\.(log|debug|info|warn|error)\s*\(/.test(source)) {
      violations.push(`${name}: application source must not log request or loss data`);
    }
    if (!name.startsWith("api/") && /\bfetch\s*\(/.test(source)) {
      violations.push(`${name}: direct transport is confined to src/api`);
    }
    if (/\bnew\s+Function\s*\(|\bimport\s*\(\s*[^'\"]/.test(source)) {
      violations.push(`${name}: dynamic code loading is forbidden`);
    }
    if (/^(api|scenarios)\//.test(name) && source.includes("visualization/geometry")) {
      violations.push(`${name}: API and scenario modules cannot import presentation geometry`);
    }
    if ((name.includes("catalogueForm") || name.includes("learning") || name.includes("comparison")) && source.includes("visualization/geometry")) {
      violations.push(`${name}: request, learning and comparison modules cannot import presentation geometry`);
    }
  }
}

visit(sourceRoot);

if (violations.length) {
  throw new Error(`CT7 source-boundary violations:\n${violations.join("\n")}`);
}

console.log("CT7 source boundaries: PASS");
