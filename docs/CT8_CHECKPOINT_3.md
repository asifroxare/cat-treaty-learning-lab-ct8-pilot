# CT8 checkpoint 3 — frozen baseline and error evidence

Added a fixture-candidate exporter that works only when pointed at the exact
clean CT7 commit, outside its working tree. This prevents CT8 code from
silently becoming its own approval baseline. Extended staging acceptance to
check small structured CT6 errors and correlation IDs. Standard-library tests
verify that golden hashing still notices independent settlement-component and
exclusion changes. No backend engine, CT6 handler or React code was modified.

Verification in the Work workspace: 3 dependency-free unit tests PASS;
Python compile PASS; CLI help PASS; Git diff against frozen CT7 is confined
to deployment tooling and CT8 documentation. Full backend and frontend suites
remain unrun here because required dependencies were unavailable. No real
staging hostname or physical browser matrix has been exercised.

**Status: predeployment candidate only.** Missing evidence: CT7/CT8 Windows
full suites, approved baseline export and independent fixture review, measured
worst-case workload and proven termination, production ingress/rate controls,
CSP/TLS/cache checks, browser accessibility matrix, alert thresholds and
rollback drill. None may be checked off by this document.
