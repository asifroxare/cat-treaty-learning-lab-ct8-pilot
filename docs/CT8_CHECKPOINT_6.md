# CT8 checkpoint 6 — Windows reproduction and supplied golden candidates

Owner Windows evidence for the prior CT8 candidate: backend 1003 passed;
frontend contract, boundary, authoritative-number and content gates PASS;
72 frontend tests passed (one environment-gated skip); build/audit PASS;
real CT6 catalogue and hours-clause test PASS; `npm ci` reported 0
vulnerabilities. The first backend attempt was interrupted at 629 tests; a
separate complete rerun passed 1003. The author has not independently rerun
those suites in the Work container because package dependencies were absent.

The owner exported two synthetic full-response candidates from the clean
exact CT7 commit. Both request digests match the manifest. The full response
hashes are provisional pending an in-process CT8 comparison on Windows and
independent review of scenario coverage. `deployment/verify_goldens.py`
implements that comparison and rejects altered source commit, input bytes,
response bytes or normalization policy. Five dependency-free tool tests pass.

No CT0–CT7 engine, API handler or React code changed. The package is still a
predeployment review candidate. The launch matrix remains OPEN for workload
bounds, worker termination, rate limiting, actual hosting, physical browsers,
monitoring and rollback.
