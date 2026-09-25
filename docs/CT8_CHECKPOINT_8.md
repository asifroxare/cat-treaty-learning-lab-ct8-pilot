# CT8 checkpoint 8 — optional process boundary candidate

Starting state: CT7 exact release frozen; CT8 Windows baseline 1003 backend
passed, 72 frontend passed, real catalogue/hours acceptance passed and two
full-response goldens matched CT7. Local bounded workload samples are in
`CT8_RESOURCE_EVIDENCE.md`.

Added opt-in child-process execution for the two CT6 run routes. It is OFF by
default and does not alter CT2–CT5 formulas or React. The existing parent API
still validates requests and projects complete authoritative responses.
When enabled, a child returns the complete engine result or a classified
block/domain failure. Timeouts, broken children and a busy slot use the
existing static CT6 500 problem response. This new behavior is a proposed
CT6 transport amendment, subject to independent review; it must not be
enabled on a public host based on this checkpoint alone.

Local verification: standard-library process-boundary tests 7 passed;
Python compilation and diff whitespace checks passed. New FastAPI integration
tests have not been run here because backend dependencies are absent. Windows
reproduction, large-result bound, timeout and disconnect behavior, error
precedence, ingress controls, browser acceptance and rollback remain OPEN.
See `CT8_EXECUTION_BOUNDARY_REVIEW.md` for exact review questions and risks.
