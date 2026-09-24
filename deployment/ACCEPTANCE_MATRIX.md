# CT8 release gate record — blank until evidence is supplied

Every row requires date, environment, release SHA, reviewer, evidence location,
and PASS. A blank, skipped or failed row blocks public deployment. Do not use
this form as evidence by itself. Deployment requires a separate owner decision.

| Gate | Evidence to attach | Status |
| --- | --- | --- |
| Exact approved CT8 commit and ZIP SHA-256 | Git and archive output | OPEN |
| Frozen CT0–CT7 tests and CT7 checks | Full terminal results on Windows path with spaces | OPEN |
| CT6 real API workflow | Catalogue and hours-clause test output | OPEN |
| Provider, domains, costs, TLS and allowed origins | Configuration review without secrets | OPEN |
| Trusted hosts, forwarded IP trust and security headers | Staging probes and physical browser evidence | OPEN |
| Request memory/CPU single and concurrent maxima | Measured worst legal inputs and machine profile | OPEN |
| Termination of abandoned/over-time computation | Process-isolation and clean-failure demonstration | OPEN |
| Rate and global concurrency caps | Threshold and rejected/accepted traces | OPEN |
| Combined middleware error precedence | Recorded matrix and response traces | OPEN |
| Catalogue/hours golden fixtures | Approved input and response digests, independent field review | OPEN |
| SPA, cache, stale tab and CORS | Edge headers, old-tab test, blocked foreign origin | OPEN |
| Edge, Chrome, Firefox desktop | Browser/version/OS, screenshots and outcomes | OPEN |
| Mobile widths, keyboard, zoom, NVDA | Browser/version/OS, screenshots and outcomes | OPEN |
| Safari/VoiceOver or explicit coverage disposition | Device/browser evidence and signed assessment | OPEN |
| Reduced motion, high contrast, forced colors | Browser evidence and outcomes | OPEN |
| Monitoring, numeric alerts and incident owner | Dashboard/alert test and retention policy | OPEN |
| Compatible pair rollback with index purge | Timed drill, golden hashes and health after rollback | OPEN |
| Independent security and learning-integrity review | Reviewer findings and dispositions | OPEN |
| Owner approval of exact public deployment | Approval referring to release digest, domains and costs | OPEN |
