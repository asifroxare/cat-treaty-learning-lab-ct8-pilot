# CT7 Checkpoint 8 Acceptance

**Specification:** CT7 v1.3 frozen  
**Checkpoint:** G84–G105 consolidated acceptance, calculation/geometry gates,
real CT6 API testing and production-build audit

## Result

Checkpoint 8 is accepted. CT7 retains CT6 as the sole actuarial authority. The
frontend only validates inputs, projects authoritative responses, formats
returned values and derives branded presentation geometry.

## Golden-case traceability

| Cases | Permanent evidence |
|---|---|
| G84–G89 | `App.test.tsx`, workflow, run-state and error tests |
| G90–G95 | `catalogueResults.test.tsx`, including exact empirical OEP point preservation |
| G96–G99 | comparison and hardened error-state tests |
| G100–G101 | axe, contrast and responsive hardening tests |
| G102 | `check-authoritative-types.mjs` plus passing geometry, failing actuarial-formula and failing geometry-leakage fixtures |
| G103 | `realApi.test.tsx` run by `run-real-api.mjs` against live catalogue and hours-clause CT6 routes |
| G104–G105 | evidence-resolution tests and guided-content neutrality lint |

`goldenTraceability.test.ts` enforces the complete, ordered G84–G105 inventory.

## Verified evidence

- Frontend: **72 normal tests passed**; the single environment-gated G103 test
  then passed separately against a real local CT6 HTTP process.
- Backend: **1003 passed**, preserving the frozen CT1–CT6 count.
- OpenAPI generation/compatibility, source-boundary and neutral-content gates:
  passed.
- Type-aware authority gate: passed. Legitimate branded geometry was accepted;
  the actuarial-formula and geometry-leakage fixtures were rejected.
- Production build: 56 modules; three output files; 344,014 bytes.
- Production artifact audit: no source maps, secrets, environment files or local
  filesystem paths.
- Dependency audit: zero vulnerabilities.

The G103 runner owns server startup, readiness polling, both HTTP runs and
shutdown, preventing a detached-process race. Rendering assertions execute on
the production React result components under the test DOM; physical-browser
matrix testing remains part of the later deployment-readiness milestone.

## Boundary retained

Checkpoint 8 does not deploy publicly, add persistence/authentication, or alter
any CT1–CT6 actuarial formula or backend test. Final CT7 installation packaging
and independent reproduction remain Checkpoint 9.
