import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

const sourceRoot = new URL("../src", import.meta.url).pathname;
const violations = [];

function visit(directory) {
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) {
      visit(path);
      continue;
    }
    if (![".ts", ".tsx"].includes(extname(path)) || path.includes("/test/")) continue;
    const name = relative(sourceRoot, path).replaceAll("\\", "/");
    const source = readFileSync(path, "utf8");
    if (!name.startsWith("api/") && source.includes("api/generated/ct6")) {
      violations.push(`${name}: generated CT6 transport types may only be imported inside src/api`);
    }
    if (/\beval\s*\(|dangerouslySetInnerHTML/.test(source)) {
      violations.push(`${name}: dynamic/raw HTML execution is forbidden`);
    }
  }
}

visit(sourceRoot);

if (violations.length) {
  throw new Error(`CT7 source-boundary violations:\n${violations.join("\n")}`);
}

console.log("CT7 checkpoint 2 source boundaries: PASS");
