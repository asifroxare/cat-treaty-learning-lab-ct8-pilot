import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

const repository = new URL("../..", import.meta.url).pathname;
const url = "http://127.0.0.1:8765";
const python = process.env.PYTHON ?? "python";
const server = spawn(python, ["-m", "uvicorn", "cat_treaty.api:app", "--host", "127.0.0.1", "--port", "8765"], {
  cwd: repository, stdio: ["ignore", "pipe", "pipe"],
});
let serverOutput = "";
server.stdout.on("data", (chunk) => { serverOutput += chunk; });
server.stderr.on("data", (chunk) => { serverOutput += chunk; });

async function ready() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try { if ((await fetch(`${url}/health/ready`)).ok) return; } catch { /* retry */ }
    if (server.exitCode != null) throw new Error(`CT6 exited before readiness:\n${serverOutput}`);
    await delay(100);
  }
  throw new Error(`CT6 readiness timed out:\n${serverOutput}`);
}

function runTests() {
  return new Promise((resolve, reject) => {
    const test = spawn("npm", ["exec", "vitest", "run", "src/test/realApi.test.tsx"], {
      cwd: new URL("..", import.meta.url).pathname,
      env: { ...process.env, VITE_CT7_REAL_API_URL: url }, stdio: "inherit", shell: process.platform === "win32",
    });
    test.on("error", reject);
    test.on("exit", (code) => code === 0 ? resolve() : reject(new Error(`real-API tests exited ${code}`)));
  });
}

try {
  await ready();
  await runTests();
  console.log("CT7 G103 real CT6 API acceptance: PASS (catalogue + hours-clause)");
} finally {
  server.kill("SIGTERM");
}
