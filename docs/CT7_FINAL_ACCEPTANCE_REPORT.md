# CT7 Final Acceptance Report

**Specification:** CT7 v1.3 frozen  
**Release milestone:** Checkpoint 9 — final installation package and independent reproduction

## Disposition

CT7 is complete and accepted for installation. This acceptance does not
authorize public deployment.

## Independent reproduction gate

The release was reproduced from a new extraction of the committed installation
archive, without reusing the development virtual environment, frontend
dependencies, build output or caches.

| Gate | Result |
|---|---|
| Embedded Git commit and clean source state | Pass |
| Python installation and dependency integrity | Pass |
| Frozen CT1–CT6 backend suite | **1003 passed** |
| OpenAPI compatibility and exact field names | Pass |
| CT7 ordinary frontend suite | **72 passed; G103 environment test intentionally gated** |
| G102 type-aware calculation/geometry fixtures | Pass |
| G104 explanation traceability and G105 neutrality | Pass |
| Production TypeScript/Vite build and artifact audit | Pass |
| Frontend dependency audit | **0 vulnerabilities** |
| Live CT6 catalogue and hours-clause G103 run | Pass |

## Package exclusions

The release contains source, frozen specifications, lockfiles, tests and Git
history. It excludes virtual environments, `node_modules`, production build
output, caches, coverage output, local environment files and secrets.

## Remaining deployment work

Physical-browser matrix testing is intentionally deferred to deployment
readiness, together with hosting configuration, production CORS/TLS/security
headers, deployment smoke testing and rollback verification.
