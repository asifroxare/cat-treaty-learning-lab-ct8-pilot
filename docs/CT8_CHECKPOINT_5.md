# CT8 checkpoint 5 — Windows reproduction driver

The candidate includes a single-command reproduction driver that points at the
existing CT7 Python virtual environment, tests the extracted CT8 candidate,
installs frontend dependencies only in its own folder and executes the real
CT6 API integration. The existing CT7 repository and environment remain
unmodified. Local standard-library tooling tests: 4 passed. Full Windows
backend/frontend/live-API results are pending execution by the project owner.

The candidate cannot be called a final deployment-ready ZIP while provider
controls, measured workloads, physical browsers and rollback remain OPEN.
