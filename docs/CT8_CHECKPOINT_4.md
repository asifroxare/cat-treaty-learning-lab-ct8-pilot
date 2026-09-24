# CT8 checkpoint 4 — static staging policy and evidence status

Added a candidate split-origin Cloudflare Pages asset policy generator and
platform rationale. The generator rejects a compiled localhost API URL, emits
known-route rewrites without an `/assets/*` catch-all, and sets a script CSP
without inline script permission. Four standard-library tool tests pass.

Deployment remains blocked on independently reviewed goldens, full Windows
backend/frontend suites, worst-case workloads, tested computation termination,
resource/rate enforcement, provider selection and real staging, physical
browser/accessibility evidence, numeric monitoring and a rollback drill. A
rendered package cannot substitute for these checks. Do not call this a final
public deployment ZIP.

No CT0–CT7 source or frontend application files have been changed.
