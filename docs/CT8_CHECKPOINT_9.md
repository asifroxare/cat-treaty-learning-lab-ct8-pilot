# CT8 checkpoint 9 — independent review fixes

The independent reviewer confirmed the isolation guard is off by default and
preserves the two ordinary success scenarios, but identified launch blockers
for maximum-size requests, multiple workers, busy/deadline HTTP outcomes,
abrupt worker death, and ingress controls. This checkpoint adds HTTP tests for
busy and deadline outcomes and a child watchdog for parent death. These new
tests require Windows validation. See `CT8_CLAUDE_REVIEW_DISPOSITION.md`.
No CT0–CT7 calculation code or React component changed. Public deployment
remains blocked.
