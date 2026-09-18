# CT7 Learning Lab Frontend, Interactive Experiments and Explanation Experience

**Version:** Draft v1.0 for independent validation  
**Product:** EdInsured Catastrophe Treaty Learning Lab  
**Authority:** CT0 master architecture and frozen CT1–CT6 contracts  
**Implementation status:** Not authorized until this specification is independently reviewed, revised where necessary and frozen

## 1. Purpose

CT7 turns the CT6 catastrophe treaty API into a learning and experimentation
experience. It is not a pricing calculator and does not replace the separate
Cat XOL Pricing Learning Lab. Its purpose is to help a learner understand how
loss stages, inuring covers, Cat XL program geometry, occurrence definition,
annual capacity, reinstatements, settlement presentation and tail analytics
interact.

The frontend explains and visualizes authoritative CT6 results. Every
actuarial value originates in the Python backend.

## 2. Governing documents

1. `docs/CT0_REPRODUCTION_GATE.md` and the frozen CT0 master architecture;
2. `docs/CT1_IMPLEMENTATION_SPEC.md` through
   `docs/CT5_IMPLEMENTATION_SPEC.md`;
3. `docs/CT6_IMPLEMENTATION_SPEC.md` v1.0;
4. `docs/CT6_AUDIT_DISPOSITION.md`;
5. `docs/CT6_FINAL_ACCEPTANCE_REPORT.md`; and
6. CT6 OpenAPI generated from commit `b5476c6` or its explicitly reviewed
   successor.

If UI wording conflicts with an authoritative API field or reconciliation,
the API wins. CT7 must expose the conflict as a defect; it must not silently
reinterpret the result.

## 3. Frozen product separation

The Catastrophe Treaty Learning Lab and Cat XOL Pricing Learning Lab remain
different products.

| Treaty Learning Lab | Cat XOL Pricing Learning Lab |
|---|---|
| Starts from disclosed occurrence loss stages and treaty terms | Builds a synthetic catastrophe catalogue and technical price |
| Teaches inuring, tower geometry, hours clauses and annual capacity | Teaches AAL, OEP/AEP, technical premium, RoL and pricing sensitivity |
| Uses CT2–CT6 treaty-engine authority | Uses its independently frozen pricing-engine authority |
| Does not calculate a technical premium in CT7 | Does not become the source of CT7 treaty recoveries |

Navigation may link between products later, but the applications, APIs,
identities and disclaimers must remain distinguishable.

## 4. In scope

- a React/Vite single-page frontend consuming CT6;
- catalogue and hours-clause run modes;
- Guided Lab and Explore modes;
- curated, editable teaching scenarios;
- side-by-side baseline/scenario runs;
- structured explanations and reconciliation evidence;
- pre-capacity versus post-capacity visual separation;
- the three settlement values shown separately;
- tail and frequency visualizations;
- candidate-window admissibility and election evidence;
- validation, blocked-contract and internal-error experiences;
- responsive desktop/tablet/mobile layouts;
- accessible keyboard, screen-reader and non-colour operation;
- deterministic frontend fixtures and contract tests; and
- production-build readiness without public deployment.

## 5. Out of scope

- actuarial formulas or treaty calculations in JavaScript;
- catastrophe pricing, rate-on-line or technical premium calculation;
- commercial catastrophe-model output;
- user accounts, saved cloud portfolios or collaboration;
- authentication, billing or production rate limiting;
- file ingestion, spreadsheets or arbitrary JSON editing;
- asynchronous simulation jobs;
- multi-currency conversion;
- legal contract interpretation or automated treaty wording advice;
- AI-generated numerical explanations; and
- public deployment.

## 6. Users and learning outcomes

Primary users are students, junior underwriters, brokers, claims
professionals, actuaries and experienced practitioners testing an unfamiliar
structure.

After a guided session a learner should be able to explain:

1. why the Cat XL subject loss differs from initial insured loss;
2. how attachment, limit, gaps, overlaps and shares affect occurrence recovery;
3. why pre-annual-capacity entitlement can exceed post-capacity recovery;
4. when and how reinstatement capacity becomes available;
5. why reinstatement premium and net cash settlement are not recovery aliases;
6. why two hours-clause elections can produce different valid outcomes;
7. why an attractive split may be contractually inadmissible; and
8. why empirical tail estimates carry credibility warnings.

## 7. Non-negotiable calculation boundary

CT7 may:

- validate basic presentation state such as an empty text box;
- serialize CT6 request fields;
- format authoritative numbers, dates and percentages;
- sort rows only where the API declares ordering non-contractual;
- filter already-returned rows for display; and
- select which authoritative series to chart.

CT7 must not:

- calculate loss stages, recoveries, capacity, reinstatement premium, net cash,
  quantiles, TVaR, return-period values, utilization, exhaustion or
  reconciliation;
- infer a missing authoritative field;
- clamp negative cash or replace null utilization with zero;
- calculate baseline/scenario monetary or percentage deltas; or
- manufacture explanations from raw monetary inputs.

Baseline and scenario comparison in CT7 v1 is therefore side-by-side. Any
future delta metric requires a reviewed backend contract.

## 8. Technical architecture

- React with Vite and TypeScript;
- an API client generated from or contract-checked against CT6 OpenAPI;
- no global state framework unless implementation evidence shows React state
  and context are insufficient;
- no charting library that performs undisclosed aggregation or sampling;
- semantic HTML before custom ARIA;
- CSS design tokens and responsive layout without inline calculation logic;
- finite JSON only; and
- no direct import or translation of Python formulas into frontend code.

Proposed frontend structure:

```text
frontend/
  src/
    api/            CT6 transport client and generated/checked types
    app/            routing, providers and run-state controller
    components/     reusable presentation components
    features/       catalogue, hours, compare, audit and learning modules
    scenarios/      curated request templates and educational metadata
    formatting/     display-only currency, number and percentage formatters
    accessibility/  focus and announcement helpers
    test/           fixtures, contract, interaction and accessibility tests
```

## 9. Information architecture

CT7 v1 has six primary destinations:

1. **Start** — purpose, scope, disclaimer and route into guided/explore modes;
2. **Guided Lab** — sequenced experiments with learning question, action,
   prediction prompt, result and takeaway;
3. **Explore Treaty** — editable catalogue-mode treaty and event inputs;
4. **Hours-Clause Lab** — timestamped components, candidate windows,
   admissibility and election;
5. **Compare** — baseline and scenario displayed side-by-side using two
   complete CT6 responses; and
6. **Audit Trail** — versions, hashes, request ID, warnings, reconciliations,
   exclusions and authoritative field definitions.

## 10. Run-state machine

Each run panel has exactly one state:

| State | Required behavior |
|---|---|
| `editing` | Inputs editable; no stale result labelled current |
| `submitting` | Controls protected against duplicate submission; accessible progress announcement |
| `success` | Complete authoritative response shown with request ID and hashes |
| `schema_error` | Field/path evidence mapped to inputs where possible |
| `domain_error` | Treaty-rule problem shown without inventing a correction |
| `contract_blocked` | Geometry/election evidence shown; no partial recovery panel |
| `too_large` | Explicit summary-mode guidance; no silent downgrade |
| `server_error` | Sanitized recovery path; no stale response represented as new |
| `offline` | Clear connectivity state and retry; no simulated fallback result |

Changing any contractual input marks the prior result `stale` until a new
successful run completes. A stale result may remain visible for comparison but
must be labelled and visually distinct.

## 11. Input experience

Inputs are grouped by meaning rather than DTO nesting:

- simulation and provenance;
- occurrence loss basis and included/excluded components;
- inuring covers and order;
- Cat XL layers and coordination controls;
- annual capacity and reinstatement terms;
- settlement mode;
- tail configuration; and
- hours-clause terms and loss components.

Every field provides:

- plain-language label;
- unit and valid range;
- concise definition;
- whether it is contractual, presentation-only or provenance;
- source/rule reference where relevant; and
- backend error placement using the CT6 error path.

The UI may prevent obviously incomplete submission but CT6 remains the
authoritative validator.

## 12. Authoritative result hierarchy

Results are displayed in this order:

1. completion status, warnings and learning question;
2. loss-stage bridge to Cat XL subject loss;
3. program geometry and occurrence recovery;
4. pre-annual-capacity entitlement;
5. post-capacity recovery and shortfall;
6. reinstatement usage and premium;
7. three-way settlement;
8. annual summaries and utilization statuses;
9. tail/frequency analytics; and
10. audit/reconciliation evidence.

The interface must never label a pre-capacity result as final treaty recovery.

## 13. Mandatory visual components

### 13.1 Loss-stage bridge

Displays initial insured loss, included additions/deductions, Ultimate Net Loss,
ordered inuring recovery and Cat XL subject loss. Excluded components remain
visible as excluded, not deleted.

### 13.2 Program tower

Displays attachment, exhaustion, gaps, overlaps, shares and recovery by layer.
Gaps, base retention and above-tower retention must use distinct labels.
Blocked overlap shows the affected layer/segment evidence without a recovery.

### 13.3 Capacity timeline

Displays event order, active capacity before recovery, recovery, capacity
shortfall, post-event reinstatement and capacity available to the next event.
The visual must not imply same-event reinstatement benefit.

### 13.4 Settlement card

Always displays separate rows for:

- gross contractual recovery;
- reinstatement premium payable; and
- net cash settlement.

Negative net cash remains negative and is accompanied by explanatory text; it
is never floored, hidden or styled as a calculation error.

### 13.5 Tail analytics

OEP and AEP views identify perspective, probability/return-period convention,
sample size and all credibility warnings. The UI charts returned curve points
without client-side rebucketing or interpolation.

### 13.6 Hours-clause evidence

Shows components on a timeline, every candidate window/set, valid/excluded
status, exclusion codes/reasons, selected method and selected set. Invalid
higher-recovery alternatives remain visible as rejected evidence.

## 14. Guided experiments

CT7 v1 includes at least these seven experiments:

| ID | Experiment | Controlled change | Required learning evidence |
|---|---|---|---|
| E01 | From insured loss to subject loss | Include/exclude one disclosed component or alter one inuring cover | F03–F09 reconciliation and changed subject loss |
| E02 | Move attachment and limit | Change one layer while holding the occurrence fixed | Tower geometry, layer recovery and retained buckets |
| E03 | Shares are different controls | Change ceded share and placement share separately | Recovery/capacity effect and fixed-share caveat |
| E04 | Annual capacity across events | Add/change a later event | Pre-/post-capacity difference, exhaustion and shortfall |
| E05 | Reinstatement economics | Switch free/paid or time basis | Capacity unchanged by presentation; premium and cash effect disclosed |
| E06 | Tail credibility | Change annual-trial sample or selected return period | Cumulative warnings and sample-size explanation |
| E07 | Contractual occurrence election | Use a bounded timestamped scenario | Valid set, elected set and rejected invalid split evidence |

Each experiment uses a baseline and one controlled scenario, asks the learner
to predict the direction before running, and ends with API-backed facts plus a
short takeaway. CT7 does not grade free-text answers.

## 15. Scenario catalogue

Curated scenarios are versioned frontend fixtures containing:

- stable scenario ID and version;
- complete valid CT6 request;
- intended learner level;
- learning objective;
- controlled fields allowed to change;
- prediction prompt;
- expected qualitative teaching points; and
- disclaimer/source notes.

Expected numerical outputs are not hard-coded into production scenario files.
Tests may freeze response fixtures tied to an explicit CT6 commit and schema.

## 16. Explanation contract

The frontend renders `learning.facts`, reconciliations, warnings, geometry and
election evidence. Explanations follow a four-part structure:

1. **What happened** — authoritative result;
2. **Why** — returned driver statement and trace references;
3. **What changed** — controlled input differences, not calculated result
   deltas; and
4. **What to inspect next** — relevant panel or audit record.

Static educational text must be reviewed content. It may explain a concept but
must not assert a numerical conclusion that was not returned by CT6.

## 17. Comparison contract

- Baseline and scenario are separate complete requests and responses.
- Both request IDs and all CT4/CT5 hashes remain visible.
- A failed scenario cannot replace a successful baseline.
- Side-by-side values use identical units, precision and perspective.
- The UI may identify fields the user changed.
- The UI may not calculate or display result deltas in CT7 v1.
- Comparison is disabled across different reporting currencies or incompatible
  CT6 schema versions.

## 18. Formatting and null semantics

- Reporting currency comes from the response; USD is the default teaching
  currency but is not hard-coded into authoritative values.
- Full precision remains available in audit detail; display precision is
  consistent and disclosed.
- `null` utilization plus `not_applicable_zero_capacity` displays
  **N/A – no payable capacity**, never `0%`.
- Negative net cash retains its minus sign.
- Zero, null, unavailable and omitted are visually and semantically distinct.
- Large values use locale-aware separators without changing the value.

## 19. Accessibility

CT7 targets WCAG 2.2 AA:

- complete keyboard operation and visible focus;
- logical headings, landmarks and tab order;
- form labels and programmatic error association;
- status updates through restrained live regions;
- charts with equivalent table/text views;
- no meaning conveyed by colour alone;
- minimum contrast compliance;
- reduced-motion support; and
- responsive operation at 320 CSS pixels and 200% zoom.

Automated accessibility tests are mandatory but do not replace keyboard and
screen-reader manual checks.

## 20. Safety, disclaimers and privacy

Every primary page makes clear that the lab:

- is educational and not a commercial catastrophe model;
- uses user-entered or synthetic teaching data;
- does not estimate actual portfolio or territorial catastrophe risk;
- does not provide underwriting, pricing, reserving, claims, capital,
  regulatory or legal advice; and
- requires independent professional validation for real decisions.

CT7 stores no server-side user data. Browser persistence is off by default.
If local scenario persistence is later added, it requires separate consent,
clear deletion and a security review.

## 21. Security and transport

- same-origin production API is preferred;
- development API origin is explicit configuration;
- no wildcard credentialed CORS;
- no raw HTML from API or scenario content;
- no `eval`, dynamic code loading or arbitrary remote URLs;
- no secrets in frontend environment variables;
- request/response logging excludes full loss data by default;
- dependencies are lockfile-pinned and audited; and
- production build emits no source-map exposure unless deliberately approved.

## 22. Performance and limits

- CT7 honours CT6 synchronous and response-detail limits.
- Large full-detail requests are not automatically retried as summary; the
  user chooses after seeing the 413 guidance.
- Tables use rendering virtualization only where needed; all authoritative
  rows remain available through accessible navigation/export only if a future
  export contract is approved.
- Charts never silently sample or aggregate returned points.
- Performance tests measure initial load, interaction and representative
  response rendering; v1 freezes measurements, not a machine-independent hard
  time threshold.

## 23. Testing strategy

Required test groups:

- API/OpenAPI compatibility and strict field-name tests;
- request-builder serialization tests;
- no-actuarial-calculation static source gate;
- run-state and stale-result tests;
- catalogue and hours end-to-end mocked transport tests;
- three-way settlement and negative-cash presentation tests;
- null/status utilization tests;
- warning, exclusion, reconciliation and audit-evidence tests;
- guided experiment tests;
- responsive component tests;
- automated accessibility tests;
- production build and bundle checks; and
- browser end-to-end tests against a real local CT6 API before acceptance.

No CT1–CT6 backend test may be weakened, skipped or replaced by a frontend
test.

## 24. CT7 golden cases

| ID | Scenario | Expected check |
|---|---|---|
| G84 | Product separation | Treaty lab identity/disclaimer cannot be confused with pricing lab |
| G85 | Catalogue happy path | Complete CT6 result renders every result tier |
| G86 | Hours happy path | Candidate, exclusion and election evidence render completely |
| G87 | Strict schema error | Path evidence maps to the relevant input and no result renders |
| G88 | Contract blocked | Blocking evidence renders without partial recovery |
| G89 | Stale result | Input edit marks prior result stale until rerun |
| G90 | Three-way settlement | Recovery, premium and cash remain separate |
| G91 | Negative cash | Negative value remains visible and unfloored |
| G92 | Zero capacity | Null plus status displays N/A, not zero |
| G93 | Full versus summary | Both modes preserve identity/audit evidence; omitted rows are clear |
| G94 | Cumulative warnings | Every CT6 credibility warning remains visible |
| G95 | Tail series integrity | Returned points chart without interpolation/rebucketing |
| G96 | Comparison | Two complete runs remain independent; no client result delta |
| G97 | Request identity | Request ID and CT4/CT5 hashes visible in audit trail |
| G98 | API unavailable | Offline state contains no fabricated result |
| G99 | Sanitized server error | No stack/path/internal detail appears |
| G100 | Accessibility | Keyboard path, focus, names, contrast and chart alternative pass |
| G101 | Responsive layout | Core workflows operate at desktop, tablet and 320px width |
| G102 | No calculation duplication | Static gate finds no frozen actuarial formulas in frontend |
| G103 | Real API end to end | Production build completes catalogue and hours runs against CT6 |

## 25. Implementation checkpoints

1. independent review, disposition and CT7 specification freeze;
2. frontend foundation, design tokens, routing and CT6 client contract;
3. request builders and catalogue Explore workflow;
4. authoritative catalogue result visualizations and audit trail;
5. hours-clause workflow and election evidence;
6. Guided Lab experiments and side-by-side comparison;
7. accessibility, responsive behavior, errors and security hardening;
8. G84–G103, real-API end-to-end acceptance and production build; and
9. final CT7 installation package and independent reproduction.

Every implementation checkpoint requires frontend tests, the complete CT1–CT6
backend suite and a clean commit.

## 26. Completion gate

CT7 closes only when:

- independent review findings are resolved in a disposition document;
- G84–G103 pass with permanent trace IDs;
- no actuarial formula exists in frontend source;
- both run modes pass real-API browser tests;
- OpenAPI compatibility and exact authoritative names pass;
- negative cash, null utilization and all warnings/exclusions reconcile;
- accessibility and responsive manual checks are documented;
- dependency audit and production build pass;
- all 1003 CT1–CT6 tests continue to pass or an explicitly reviewed successor
  count is documented; and
- a clean installation package is reproduced independently.

## 27. Questions for independent reviewer

1. Is the separation from the Cat XOL Pricing Learning Lab sufficiently clear?
2. Does the calculation boundary prevent meaningful actuarial duplication?
3. Is side-by-side comparison without client-calculated deltas the right CT7
   v1 decision?
4. Does the result hierarchy keep pre-capacity entitlement distinct from
   post-capacity recovery?
5. Are annual layer utilization/status fields exposed clearly enough?
6. Does the hours-clause experience preserve invalid higher-recovery evidence?
7. Are the seven guided experiments sufficient and properly controlled?
8. Does the explanation contract prevent invented numerical conclusions?
9. Are error and stale-result states safe against misleading partial results?
10. Are full/summary semantics faithfully represented?
11. Are the accessibility requirements testable and proportionate?
12. Are security and local-persistence boundaries appropriate before public
    deployment?
13. Are G84–G103 sufficient for frontend closure?
14. Should any CT7 item be deferred to deployment readiness rather than the
    frontend milestone?
15. What finding, if any, blocks freezing this specification?

## 28. Freeze rule

This draft authorizes review only. React scaffolding, dependency installation
and frontend implementation must not begin until reviewer findings are
dispositioned and the document is explicitly marked frozen.
