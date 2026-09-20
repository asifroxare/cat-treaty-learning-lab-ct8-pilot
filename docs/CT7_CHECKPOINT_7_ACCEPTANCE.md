# CT7 Checkpoint 7 Acceptance

**Checkpoint:** Accessibility, responsive behavior, errors and security hardening

**Frozen authority:** CT7 v1.3

**Status:** Accepted after consolidated verification

## Accessibility

- real skip link targets the focusable main landmark;
- visible focus treatment remains global;
- form labels, hints and errors retain programmatic associations;
- submitting and run-state changes remain live-region announced;
- terminal error headings receive focus when rendered;
- charts retain exact adjacent text/table alternatives;
- null, stale, warning and error states use text as well as colour;
- reduced-motion and forced-colors modes have explicit CSS safeguards;
- frozen text/background token pairs meet WCAG AA contrast ratios; and
- automated axe checks cover all six routes and a complete result hierarchy.

The jsdom axe colour rule is disabled because it cannot compute rendered CSS;
contrast is tested separately against the frozen hexadecimal tokens.

## Responsive behavior

- the document retains a 320 CSS-pixel minimum contract;
- navigation remains horizontally scrollable rather than clipped;
- shell, forms, result grids, experiments and comparison columns collapse at
  their declared breakpoints; and
- dense ledgers remain inside labelled horizontal scroll regions without
  dropping rows.

## Error hardening

- every terminal CT6 execution state uses a reviewed static public message;
- untrusted/free-text server titles and details are not rendered;
- structured code, request ID, safe path and rule evidence remain available;
- 413 explicitly asks the user to select summary and never retries silently;
- offline and server-error states remain distinct;
- contract blockage never renders a partial new result; and
- stale prior success stays independently labelled during failed reruns.

## Security hardening

The source gate rejects raw HTML, `eval`, dynamic code loading, direct transport
outside `src/api`, browser persistence, cookie access and application logging.
The build emits no source maps. React text rendering remains the only path for
CT6 strings, and the client fails closed on unrecognized success/error bodies.

## Deliberately deferred

- full type-aware G102 passing/failing fixture gate;
- real-browser keyboard, 200% zoom and 320px manual evidence;
- real local-API end-to-end runs; and
- consolidated G84–G105 acceptance.

Those are mandatory Checkpoint 8 gates, not waived requirements.

## Acceptance evidence

- CT6 OpenAPI snapshot equality: **PASS**;
- source/security and presentation-geometry boundaries: **PASS**;
- guided-content neutrality gate: **PASS**;
- automated axe route/result checks: **PASS**;
- frozen WCAG AA token-contrast checks: **PASS**;
- frontend suite: **70 tests passed in 17 files**;
- strict TypeScript and production build: **PASS**;
- production bundle: **54 transformed modules**, largest JavaScript artifact
  **324.51 kB** before gzip and **97.50 kB** after gzip;
- dependency audit: **0 vulnerabilities**; and
- complete CT1–CT6 regression: **1003 passed**, with the same two dependency
  deprecation warnings.
