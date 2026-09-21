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
if (forbiddenNames.length || leaked.length) {
  throw new Error(`CT7 production-build audit failed: ${[...forbiddenNames, ...leaked].join(", ")}`);
}
const bytes = files.reduce((total, path) => total + statSync(path).size, 0);
console.log(`CT7 production-build audit: PASS (${files.length} files, ${bytes} bytes, no maps/secrets/local paths)`);
