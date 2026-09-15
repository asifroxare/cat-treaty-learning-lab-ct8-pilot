# Catastrophe Treaty Learning Lab — CT4 Implementation Specification

**Milestone:** CT4 — Multi-Year Catalogue Application and Tail Analytics

**Version:** 1.1

**Status:** Frozen following independent validation

**Date:** 15 September 2026

**Product:** EdInsured Catastrophe Treaty Learning Lab

## 1. Authority and dependencies

This specification implements CT4 under:

1. *Catastrophe Treaty Learning Lab Master Architecture — CT0 Frozen
   Specification v1.0*;
2. *CT0 Implementation Integration Addendum v1.3*;
3. `docs/CT1_IMPLEMENTATION_SPEC.md` v1.1;
4. `docs/CT2_IMPLEMENTATION_SPEC.md` v1.1;
5. `docs/CT3_IMPLEMENTATION_SPEC.md` v1.1; and
6. `docs/CT3_ACCEPTANCE_REPORT.md`.

CT4 begins only from the installed CT3 commit `d58dccb`, for which 616 tests
passed on Windows and in an independently extracted distribution.

CT3 provenance is explicit: CT3 v1.0 was the review draft; the independent
review identified the missing uncoordinated-overlap classification. Commit
`5c61fb3` froze CT3 v1.1 after resolving that finding by separating topology
from eligibility, adding topology value `overlapping`, and returning structured
`uncoordinated_overlap` diagnostics with no recovery for G29. The implementation
and final acceptance at commit `d58dccb` are recorded in
`docs/CT3_AUDIT_DISPOSITION.md` and `docs/CT3_ACCEPTANCE_REPORT.md`.

## 2. Purpose

CT4 applies the completed one-occurrence treaty pipeline to an event-level,
multi-year stochastic catalogue and answers:

1. What subject loss, program recovery and insurer net loss occur in each
   annual trial?
2. What are the occurrence-exceedance and aggregate-exceedance views of each
   loss perspective?
3. How are AAL, empirical quantiles and tail means calculated?
4. How reproducible is a run, and how stable are selected estimates across
   declared sample sizes and seeds?
5. In dedicated timestamped teaching scenarios, which hours-clause occurrence
   groupings are contractually admissible and why are alternatives excluded?

CT4 remains a learning and experimentation engine. Every statistic must retain
its population, denominator, convention and trace to annual trials and
occurrences.

## 3. Milestone boundary

### 3.1 Included

- an explicit event-level catalogue covering one or more annual trials;
- explicit empty trials through a declared `trial_count`;
- deterministic chronological occurrence processing;
- one frozen CT3 program structure across the complete simulation;
- CT2 and CT3 evaluation for each selected occurrence;
- annual and occurrence ledgers;
- subject-loss, gross-recovery and insurer-net perspectives;
- OEP and AEP samples and empirical curves;
- AAL, standard deviation, coefficient of variation, nearest-rank VaR and
  empirical TVaR;
- attachment and exhaustion frequencies with disclosed denominators;
- deterministic metadata, canonical hashing and seed disclosure;
- exact-run reproducibility testing;
- stability testing across declared sample sizes and seeds;
- catalogue-defined occurrences by default; and
- a separate, bounded hours-clause teaching mode with timestamped components,
  valid-window generation, election and exclusion reasons.

### 3.2 Explicit exclusions

CT4 does not implement:

- annual aggregate limits, reinstatements, chronological capacity consumption
  or exhaustion across occurrences;
- net cash settlement or reinstatement-premium deduction;
- aggregate XL, cascading, drop-down or franchise layers;
- hazard-model vendor files or a production catastrophe-model replacement;
- portfolio geocoding, vulnerability science or financial-module uncertainty;
- technical pricing, rate on line, brokerage or expense loadings;
- capital, solvency or financing comparisons;
- API endpoints, frontend screens or deployment; or
- unrestricted hours-clause optimization over large stochastic catalogues.

Annual capacity and reinstatement begin in CT5. CT4 must not anticipate them.

## 4. Product and catalogue boundary

The Cat XOL Pricing Lab and Cat Treaty Learning Lab remain separate products.
CT4 may consume a versioned event-level catalogue through the frozen canonical
adapter contract, but it must not import the pricing product, its API or its
frontend at runtime.

CT4 does not claim to generate an industry catastrophe model. Its primary
input is a supplied stochastic catalogue whose provenance, version, simulation
seed and trial population are explicit. A deterministic synthetic reference
catalogue fixture may be used for learning examples and stability tests, but it
must be labelled synthetic and unsuitable for underwriting or regulatory use.

## 5. Immutable simulation input

`CT4SimulationInput` contains:

- unique nonblank `simulation_id`;
- positive integer `trial_count`;
- tuple of `CT4AnnualTrialInput` values with IDs exactly `1..trial_count`;
- catalogue version and source version;
- non-negative integer simulation seed, or explicit null for an externally
  supplied deterministic catalogue;
- one frozen program-term fingerprint shared by every occurrence;
- tail probability levels and return periods;
- an explicit `occurrence_definition_mode`;
- numerical-tolerance profile; and
- description, source and rule references excluded from actuarial hashing.

`CT4AnnualTrialInput` contains:

- positive `annual_trial_id`;
- zero or more event-level occurrence inputs;
- catalogue-source identity; and
- no annual-capacity state.

Every default-mode event record contains:

- unique nonblank `event_id` across the simulation;
- matching CT2 occurrence ID;
- annual trial ID;
- finite non-negative event time;
- positive event sequence;
- peril and region;
- immutable CT2 loss-stage input or an already verified CT3 program input;
- optional timestamp and causal-event metadata for disclosure; and
- source and trace references.

Raw scalar losses and annual-only aggregate losses are invalid. Event-level
occurrences are a mandatory CT4 entry requirement.

## 6. Fixed-program requirement

All occurrences in one simulation use the same:

- layer IDs, attachments and occurrence limits;
- layer currencies;
- ceded shares and placement shares;
- gap acknowledgement;
- overlap coordination mode and priority order; and
- CT3 engine and schema versions.

Occurrence-specific CT2 loss values and occurrence IDs necessarily differ and
are excluded from the program-term fingerprint. A mid-simulation change in any
program term is rejected; it is not averaged or treated as a new scenario.

Each alternative program is a separate CT4 simulation with a separate input
hash, permitting transparent scenario comparison later.

## 7. Occurrence definition

### 7.1 Default — catalogue-defined occurrence

`occurrence_definition_mode = catalogue_defined` is the production default for
CT4. Every validated catalogue event is one occurrence. CT4 does not regroup,
split or optimize those events.

The default preserves the CT1 compatibility rule that events are processed by
event time and stable identifiers. The UI must describe these as
"catalogue-defined occurrences," not as legally adjudicated hours-clause
events.

### 7.2 Dedicated hours-clause teaching mode

`occurrence_definition_mode = hours_clause_teaching` is confined to a separate
timestamped scenario with at most 12 loss components in one annual trial. It
is not silently applied to a large stochastic catalogue.

The occurrence-definition mode is fixed once for the entire simulation. An
`hours_clause_teaching` request must have `trial_count = 1`; catalogue-defined
and hours-clause trials cannot be mixed in one run.

The scenario declares:

- treaty-term start and end timestamps;
- hours-window duration;
- permitted peril or cause;
- permitted geographic scope;
- causal-link rule;
- inclusive-start/exclusive-end boundary convention;
- election method; and
- manual candidate-set IDs where manual election is selected.

Each raw component declares an ID, loss, timestamp, peril, region, causal-event
ID and treaty-term status. Missing timestamps or rule attributes are invalid;
they are never imputed.

## 8. Hours-window validity before election

The hours-clause engine first generates candidate windows anchored at each
eligible component timestamp. It then generates candidate non-overlapping
window sets. Election occurs only after this admissibility stage.

A candidate window is valid only when:

1. its start and end obey the declared duration and boundary convention;
2. every component lies within the treaty term;
3. every component satisfies the declared peril/cause rule;
4. every component satisfies the geographic rule;
5. every component satisfies the causal-link rule;
6. no component is duplicated; and
7. the full candidate set contains no overlapping elected windows.

Every excluded window or window set remains in an immutable audit ledger with:

- stable candidate ID;
- proposed start/end and component IDs;
- admissibility status;
- one or more stable exclusion codes;
- human-readable reason;
- affected component/window IDs; and
- rule reference.

Frozen exclusion codes include:

- `outside_hours_duration`;
- `outside_treaty_term`;
- `peril_or_cause_mismatch`;
- `geographic_mismatch`;
- `causal_link_failure`;
- `duplicate_component`;
- `overlapping_windows`; and
- `manual_selection_invalid`.

An inadmissible higher-recovery split must be shown and rejected; it must never
enter the election comparison.

## 9. Hours-window election

Election methods are:

- `earliest_valid_window` — lexicographically earliest valid set by window
  start, end and candidate ID;
- `maximum_subject_loss` — greatest total valid occurrence subject loss, with
  the earliest-valid rule as tie-breaker;
- `maximum_contractual_recovery` — greatest CT3 contractual recovery among
  valid candidate sets only, with subject loss then earliest-valid tie-breaks;
  and
- `manual` — the user identifies one complete valid generated candidate set.

The response discloses the selected method, every valid alternative, recovery
under every valid alternative, deterministic tie-break facts and the selected
candidate-set ID. Maximum recovery is an optional contractual election method,
not the engine default and not a cedant entitlement inferred by CT4.

If the wording does not contractually authorize the requested election method,
the scenario is blocked. The engine never substitutes a preferred economic
outcome for contractual authorization.

## 10. Deterministic annual ordering

After occurrence definition, each annual trial is processed by:

1. ascending occurrence start/event time;
2. ascending event sequence; and
3. ascending occurrence/event ID.

Input order cannot change results or serialization. Duplicate IDs, duplicate
sequences at identical times without a stable ID, cross-trial ID mismatches or
non-contiguous annual trial IDs fail explicitly.

CT4 applies CT2 and CT3 independently to every selected occurrence. Any blocked
or unreconciled occurrence blocks the complete simulation; it is not treated as
zero recovery.

The engine performs a preflight pass over trial IDs, event identities,
program-term fingerprints, occurrence rules and CT3 geometry before the
expensive occurrence loop. A later CT2 data failure still invalidates the full
run and returns a structured failure manifest without partial tail analytics.
This fail-loudly rule can require correction and rerun of a large catalogue;
that operational cost is accepted for v1 to prevent a bad record from silently
entering the empirical distribution as zero.

## 11. Pre-annual-capacity convention

Because CT5 has not yet been implemented, every CT4 recovery is explicitly:

`gross_contractual_recovery_pre_annual_capacity`

Multiple occurrence recoveries in one trial do not consume a shared annual
limit and do not trigger reinstatements. CT4 AEP recovery is therefore the sum
of independent occurrence entitlements before annual capacity.

Every result, chart label, explanation and export must display this convention.
The unqualified phrases "annual treaty recovery" and "net settlement" are
prohibited in CT4 output.

The exact field name is mandatory in backend and any future API schema; a
presentation alias cannot replace it.

## 12. Annual-trial formulas

For occurrence (j) in annual trial (y), let:

- (S_{yj}) = completed CT2 Cat XL subject loss;
- (R_{yj}) = CT3 gross contractual recovery before annual capacity; and
- (N_{yj}=S_{yj}-R_{yj}) = insurer net occurrence loss before annual
  capacity.

For metric perspective (X\in\{S,R,N\}), define an empty trial's maximum and
sum as zero.

### F17 — Annual occurrence maximum (OEP sample)

\[
O_y^X = \max_j X_{yj}, \qquad O_y^X=0\text{ for an empty trial}
\]

OEP uses the largest applicable occurrence in each annual trial. It does not
use the largest raw component inside an elected hours-clause occurrence.

Because program terms and shares are fixed across the simulation, both
recovery and insurer net loss are non-decreasing functions of subject loss.
Therefore an occurrence with maximum subject loss must also attain the maximum
recovery and maximum net-loss values, although smaller occurrences may tie on
a plateau. CT4 asserts this invariant. For driver attribution, ties are broken
first by greatest subject loss and then by deterministic occurrence order, so
all three F17 perspectives identify the same driver occurrence.

### F18 — Annual aggregate (AEP sample)

\[
A_y^X = \sum_j X_{yj}, \qquad A_y^X=0\text{ for an empty trial}
\]

All sums use `math.fsum` in deterministic occurrence order.

### F19 — Annual average loss

\[
\operatorname{AAL}^X = \frac{1}{Y}\sum_{y=1}^{Y} A_y^X
\]

where (Y) is declared `trial_count`. Zero-event and zero-loss trials remain in
the denominator. Layer/program AAL in CT4 always refers to recovery before
annual capacity.

### F20 — Annual reconciliation

\[
A_y^S=A_y^R+A_y^N
\]

F20 must pass for every trial and for portfolio AAL totals within the frozen
numerical tolerance.

## 13. OEP and AEP empirical distributions

CT4 produces six annual samples:

- subject-loss OEP and AEP;
- pre-annual-capacity recovery OEP and AEP; and
- insurer-net-loss OEP and AEP.

Every sample contains exactly `trial_count` values, including explicit zeros,
and is sorted only in the analytics stage. The annual ledger retains trial-ID
order.

### F21 — Nearest-rank empirical quantile

For ascending observations
(x_{(1)}\le\dots\le x_{(Y)}) and probability (p\in(0,1)):

\[
Q_p=x_{(\lceil pY\rceil)}
\]

No interpolation is used. VaR levels default to 95%, 99% and 99.5% and are
fully disclosed.

For return period (T>1), the loss estimate is:

\[
\operatorname{EP}(T)=Q_{1-1/T}
\]

Default teaching return periods are 2, 5, 10, 20, 50, 100 and 200 years.

### F22 — Empirical exceedance curve

For descending observation (x_{[r]}), rank (r=1..Y):

\[
\operatorname{EP}_r=\frac{r}{Y}
\]

Duplicate loss values remain separate ranked observations. The curve response
may additionally consolidate equal loss values for display, but the underlying
ranked sample and quantiles remain authoritative.

CT4 freezes `r/Y`, rather than `r/(Y+1)`, because the curve represents the
observed empirical exceedance frequency over the complete declared trial
population, including zero years. The resulting 100% endpoint for the smallest
observation is intentional. A chart may visually de-emphasize that endpoint but
must not change the authoritative probability or use another plotting position.

### F23 — Empirical TVaR

For nearest-rank index (m=\lceil pY\rceil):

\[
\operatorname{TVaR}_p=
\frac{1}{Y-m+1}\sum_{k=m}^{Y}x_{(k)}
\]

This deliberately includes the quantile observation and all observations above
it. It is not an interpolated expected-shortfall estimator. Default TVaR is
99%; additional configured levels use the same convention.

### F24 — Volatility and coefficient of variation

\[
\sigma_X=\sqrt{\frac{1}{Y}\sum_y(A_y^X-\operatorname{AAL}^X)^2}
\]

\[
\operatorname{CV}_X=
\begin{cases}
\sigma_X/\operatorname{AAL}^X,&\operatorname{AAL}^X>0\\
\text{null},&\operatorname{AAL}^X=0
\end{cases}
\]

The response uses `not_applicable_zero_mean` when CV is null. It never returns
NaN, infinity or a fabricated 0% CV.

## 14. Frequency denominators

CT4 exposes both occurrence and annual frequencies; labels may not omit the
denominator:

- occurrence attachment frequency = occurrences with positive program
  recovery divided by evaluated occurrences;
- annual attachment frequency = trials with at least one positive recovery
  divided by `trial_count`;
- occurrence layer-exhaustion frequency = occurrences reaching that layer's
  exhaustion divided by evaluated occurrences; and
- annual layer-exhaustion frequency = trials with at least one exhaustion of
  that layer divided by `trial_count`.

If there are zero evaluated occurrences, occurrence-denominator metrics are
null with `not_applicable_no_occurrences`; annual metrics remain zero over the
declared trial population.

## 15. Sample adequacy and tail warnings

An empirical return-period estimate is computed when mathematically defined,
but credibility is disclosed separately.

- `observations_per_return_period = Y / T`;
- fewer than 20 observations per return period produces
  `limited_tail_credibility`;
- fewer than 5 produces `severe_tail_credibility_warning`; and
- (T>Y) produces `return_period_exceeds_sample`.

Warnings do not silently suppress a result. The lab explains that simulation
length, model assumptions and sampling error limit tail interpretation.
All applicable warning codes attach cumulatively. For example, `T > Y` also
produces both limited and severe credibility warnings; the most severe warning
does not replace the others.

## 16. Exact reproducibility gate

For identical normalized inputs, catalogue version, source version, seed,
engine version and schema version, CT4 must reproduce exactly:

- occurrence ordering and elected occurrences;
- occurrence and annual ledgers;
- all six annual samples;
- quantiles, TVaR, curves and frequency metrics;
- warnings and deterministic explanations; and
- normalized-input and result hashes.

Input permutation that has no contractual meaning must canonicalize identically.
A change in seed or actuarially relevant input must change the input hash. A
different seed is not required to change every output in a small or degenerate
catalogue.

## 17. Stability-across-sample-size-and-seed gate

Exact reproducibility is necessary but does not establish statistical
stability. CT4 therefore includes a separate, mandatory gate using a frozen,
synthetic reference catalogue generator and declared tolerances.

### 17.1 Frozen validation experiment

The validation fixture is frozen in this specification before CT4 code exists:

- generator ID: `ct4_discrete_reference_v1`;
- RNG: Python `random.Random` MT19937 with the supplied integer seed;
- annual event count: Poisson with lambda `0.8`, generated by inverse CDF from
  one uniform variate per trial;
- event subject loss: one further uniform variate per event selecting USD 15m
  with probability 70%, USD 35m with probability 25% or USD 80m with
  probability 5%;
- event time: one further uniform variate on `[0, 365)`, used only for
  deterministic ordering;
- CT2 template: subject loss enters as initial insured loss, with no additions,
  deductions or inuring covers;
- CT3 program: USD 20m xs USD 10m followed by USD 30m xs USD 30m, with 100%
  ceded share and 100% placement share;
- occurrence mode: `catalogue_defined`;
- baseline: 500,000 trials with seed `20260915`;
- comparisons: 25,000 and 100,000 trials for each seed `11`, `29`, `47`, `71`
  and `101`; and
- currency: USD, with no rounding before comparison.

Poisson inverse-CDF evaluation uses probabilities beginning with
`P(N=0)=exp(-0.8)` and the recurrence
`P(N=k+1)=P(N=k)*0.8/(k+1)` until the cumulative probability first equals or
exceeds the uniform draw. Random draws are consumed in the declared order, so
the fixture does not depend on vectorized-library behavior.

The following two-sided tolerances compare each candidate estimate with the
fixed large-baseline estimate:

| Metric | 25,000-trial tolerance | 100,000-trial tolerance | Basis |
|---|---:|---:|---|
| Recovery AAL | 3.0% | 1.5% | Relative |
| Annual attachment frequency | 0.015 | 0.0075 | Absolute probability |
| Recovery OEP, 10-year | 5.0% | 5.0% | Relative |
| Recovery OEP, 20-year | 5.0% | 5.0% | Relative |
| Recovery AEP, 10-year | 10.0% | 5.0% | Relative |
| Recovery AEP, 20-year | 10.0% | 5.0% | Relative |
| Recovery AEP TVaR 99% | 10.0% | 6.0% | Relative |

The OEP tolerances primarily detect a wrong discrete tail category; AEP and
TVaR tolerances are wider because annual event-count variation compounds
severity variation. If a baseline value is zero, the comparison must use an
absolute USD tolerance declared in a versioned specification amendment rather
than divide by zero. No frozen metric above is expected to have a zero baseline.

The large baseline is an engineering reference, not a claim of actuarial truth.
No tolerance may be chosen after observing a failed candidate implementation.

### 17.2 Required comparisons

At minimum the experiment tests:

1. recovery AAL;
2. annual attachment frequency;
3. recovery OEP at 10- and 20-year return periods;
4. recovery AEP at 10- and 20-year return periods; and
5. recovery AEP TVaR 99% when the declared sample supports it.

Each comparison result records baseline, candidate, difference, tolerance and
pass/fail. The gate passes only when every predeclared comparison passes for
every required seed/sample pair.

### 17.3 Stability interpretation

This gate detects implementation instability, ordering defects and inadequate
reference sample choices. It does not prove that an input catastrophe model is
calibrated, unbiased or suitable for commercial pricing.

## 18. Immutable response contract

### 18.1 Occurrence ledger

Each selected occurrence returns:

- annual trial ID and deterministic sequence;
- source component/event IDs;
- occurrence-definition mode and elected candidate ID where applicable;
- CT2 subject loss and metadata identity;
- CT3 geometry, layer results and metadata identity;
- gross contractual recovery before annual capacity;
- insurer net occurrence loss before annual capacity;
- attachment/exhaustion indicators; and
- explanation and trace references.

### 18.2 Annual ledger

Every trial, including empty trials, returns:

- occurrence count;
- subject, recovery and net OEP observations;
- subject, recovery and net AEP observations;
- F20 reconciliation result;
- attachment/exhaustion indicators; and
- ordered occurrence references.

### 18.3 Analytics response

For each subject/recovery/net perspective:

- AAL, population standard deviation and CV/status;
- OEP and AEP sample size;
- configured VaR and TVaR values;
- return-period estimates and credibility warnings;
- empirical OEP and AEP curves; and
- calculation conventions and formula references.

### 18.4 Hours-clause teaching response

- all generated candidate windows and window sets;
- every validity test and exclusion reason;
- recovery under every valid election alternative;
- selected election method and deterministic tie-break facts;
- selected occurrence composition; and
- an explicit explanation of any rejected higher-recovery alternative.

## 19. Metadata and hashing

Frozen defaults:

- `CT4_ENGINE_VERSION = "ct4.0.0"`;
- `CT4_SCHEMA_VERSION = "ct4.0"`;
- existing treaty `PRODUCT_ID` and `PRODUCT_ROUTE`; and
- SHA-256 canonical input and result hashes.

The normalized input hash includes:

- simulation and catalogue identities;
- catalogue/source version and seed;
- declared trial population, including empty trials;
- every event-level actuarial input and occurrence-definition attribute;
- fixed CT2 loss-stage and CT3 program fingerprints;
- hours-clause terms and election authorization where applicable;
- probability levels, return periods and numerical tolerance profile; and
- CT4 engine/schema versions.

It excludes descriptions, display labels, formatting, explanation wording and
UI state. Non-contractual event input order is canonicalized; manual elections
and authorized election methods are preserved because they are contractual.

The result hash covers canonical occurrence and annual ledgers, elected
occurrences, analytics values, warnings, engine/schema versions and the input
hash. It excludes display-only text.

## 20. Numerical and validation rules

- all monetary values are finite and non-negative;
- trial IDs are contiguous positive integers;
- event and component IDs are unique in their declared scope;
- configured probabilities lie strictly in `(0, 1)` and are unique;
- return periods are finite, greater than one and unique;
- hours durations are finite and strictly positive;
- timestamps and window boundaries use one declared unit and timezone;
- every CT2, CT3, F20 and portfolio reconciliation must pass;
- `math.fsum` is used for deterministic monetary aggregation;
- population variance uses the two-pass formula in F24;
- relative tolerance is `1e-12` and absolute USD tolerance is `1e-6` for
  reconciliation only;
- no tolerance converts invalid negative or non-finite input into valid input;
  and
- sorting and hashing never round actuarial values.

## 21. Learning and experimentation requirements

Every result explains:

- why OEP and AEP differ;
- why zero years affect AAL and quantiles;
- why recovery AEP is pre-annual-capacity in CT4;
- which occurrences drive the selected tail point;
- how shares and tower geometry affect gross and net tails;
- why a return-period estimate has limited credibility;
- why changing a seed changes a stochastic realization but not contract terms;
  and
- in teaching mode, why each invalid occurrence grouping was rejected.

Scenario comparison may show two completed CT4 runs side by side, but it may
not pool them into one empirical distribution.

## 22. Golden cases

Existing G01–G34 retain their frozen meanings and IDs.

G11 and G13 were reserved before CT3: CT1's frozen golden-case traceability
assigns G11 to CT4 catalogue/reproducibility work and identifies G13 as the CT0
occurrence-election scenario. CT3 deliberately preserved G11–G13 for these
later milestones; it did not redefine them.

| ID | Scenario | Expected CT4 check |
|---|---|---|
| G11 | Seeded catalogue reproducibility | Same normalized input and seed produce byte-identical annual samples and hashes |
| G13 | Combined vs split occurrence | Valid window sets are evaluated; invalid higher-recovery split is rejected with rule-specific reasons |
| G35 | Empty annual trial | All six annual observations are zero and the trial remains in every denominator |
| G36 | Two occurrences in one trial | OEP is the maximum occurrence value; AEP is their sum for subject, recovery and net |
| G37 | Annual reconciliation | Subject AEP equals recovery AEP plus net AEP for every trial and at AAL level |
| G38 | Nearest-rank boundary | Small declared sample reproduces F21 exactly without interpolation |
| G39 | TVaR boundary | F23 includes the nearest-rank quantile observation and all larger observations |
| G40 | Input permutation | Non-contractual event order does not alter ledgers, analytics or hashes |
| G41 | Seed change | Input hash changes and both seeds remain disclosed |
| G42 | Stability experiment | Every predeclared sample-size/seed comparison reports its tolerance and passes |
| G43 | Valid hours election | All authorized election methods compare valid candidates only and disclose tie-breaks |
| G44 | Invalid higher recovery | Higher-recovery inadmissible window set is visible with exclusion codes and cannot win |
| G45 | Invalid manual election | Unknown, incomplete, duplicated or overlapping manual selection is blocked |
| G46 | Blocked occurrence | One blocked CT3 occurrence blocks the simulation instead of entering as zero |

## 23. Acceptance gates

| Gate | Pass condition |
|---|---|
| CT1–CT3 regression | All 616 installed tests remain passing |
| Event-level entry | Raw scalar and annual-only aggregate input are rejected |
| Fixed program | Every occurrence uses one program-term fingerprint |
| Empty trials | Exactly `trial_count` annual rows and six samples are emitted |
| Ordering | Input permutation cannot alter canonical results |
| Occurrence definition | Catalogue mode never silently regroups events |
| Hours validity | Every candidate is valid or has stable exclusion reasons before election |
| Hours election | Only valid non-overlapping candidate sets enter authorized election |
| Pre-capacity boundary | Every recovery is labelled and calculated before annual capacity |
| OEP/AEP | F17/F18 recompute independently for subject, recovery and net |
| Reconciliation | F20 passes for every trial and at AAL level |
| Tail statistics | F21–F24 reproduce hand-worked boundary samples |
| Frequencies | Occurrence and annual denominators remain separate and visible |
| Credibility | Return-period warnings follow observations-per-return-period rules |
| Reproducibility | Identical normalized input and seed reproduce exactly |
| Stability | Frozen multi-seed/sample experiment passes declared tolerances |
| Metadata | Contractual/version changes alter hashes; display changes do not |
| Source boundary | CT4 modules do not import pricing, API or frontend engines |
| Golden cases | G11, G13 and G35–G46 pass with permanent trace IDs |
| Repository | Full suite passes and extracted distribution is clean |

## 24. Planned implementation units

| Unit | Responsibility |
|---|---|
| `cat_treaty/ct4_models.py` | Immutable catalogue, trial, occurrence, analytics and hours-clause contracts |
| `cat_treaty/occurrence_definition.py` | Catalogue identity and bounded valid-window generation/election |
| `cat_treaty/simulation.py` | Deterministic CT2/CT3 application and annual ledgers |
| `cat_treaty/tail.py` | F17–F24 OEP/AEP, quantiles, TVaR, volatility and warnings |
| `cat_treaty/ct4_metadata.py` | CT4 canonical serialization and input/result hashes |
| `cat_treaty/ct4_explanations.py` | Deterministic learning facts and tail-driver traces |
| `tests/test_ct4_models.py` | Input, collection, immutability and fixed-program validation |
| `tests/test_ct4_occurrence_definition.py` | Hours candidates, exclusions, election and G13/G43–G45 |
| `tests/test_ct4_simulation.py` | Ordering, empty years, ledgers and F17–F20 |
| `tests/test_ct4_tail.py` | F21–F24 hand-worked analytics and credibility warnings |
| `tests/test_ct4_metadata.py` | Canonical hashes, seed and permutation behavior |
| `tests/test_ct4_stability.py` | Frozen G11/G42 reproducibility and stability experiment |
| `tests/test_ct4_golden_cases.py` | G11, G13 and G35–G46 consolidated acceptance |
| `tests/test_ct4_boundaries.py` | Source, product and milestone boundaries |

## 25. Implementation order

1. Independently validate and freeze this specification, including the
   reference stability experiment and tolerances in section 17.1.
2. Add immutable CT4 catalogue, trial and analytics models.
3. Implement catalogue-defined occurrence application and annual ledgers.
4. Implement F17–F24 tail analytics and credibility warnings.
5. Implement bounded hours-clause teaching scenarios and election audit.
6. Add CT4 canonical metadata and result hashing.
7. Implement the already-frozen reference generator and execute every
   sample-size/seed comparison without changing tolerances.
8. Add G11, G13 and G35–G46 acceptance tests.
9. Run the complete CT1–CT4 regression and source-boundary audit.
10. Record acceptance, commit and package the final CT4 archive.

No CT5 annual-capacity or reinstatement implementation begins until every CT4
gate passes.

## 26. Independent-validation questions

The reviewer should answer explicitly:

1. Is accepting a supplied event-level stochastic catalogue—rather than
   claiming to build a catastrophe model—the correct CT4 product boundary?
2. Is requiring explicit empty trials and using `trial_count` as every annual
   denominator correct?
3. Is one frozen program-term fingerprint across the simulation necessary for
   interpretable tail analytics?
4. Is labelling all CT4 recovery as pre-annual-capacity sufficient to prevent
   confusion before CT5?
5. Are F17/F18 the correct OEP/AEP definitions for subject, recovery and net
   perspectives?
6. Is nearest-rank F21 without interpolation consistent with the existing
   simulator contract?
7. Is the F23 TVaR convention—quantile observation plus all larger
   observations—clear and suitable for v1?
8. Is the now-frozen empirical curve rank `r/Y`, including its intentional 100%
   endpoint, preferable for representing observed trial frequency in this lab?
9. Are the return-period credibility thresholds informative without blocking
   computation?
10. Is exact reproducibility correctly separated from statistical stability?
11. Is the stability experiment sufficiently protected against choosing
    tolerances after observing results?
12. Is hours-clause regrouping appropriately confined to a bounded teaching
    mode, with catalogue-defined occurrences as default?
13. Does the two-step validity-then-election design prevent an inadmissible
    higher-recovery split from being selected?
14. Should one blocked occurrence invalidate the full simulation rather than
    enter the annual sample as zero?
15. Are annual capacity, reinstatement and cash settlement correctly deferred
    to CT5?

Approval freezes F17–F24, annual denominators, empirical-tail conventions,
pre-annual-capacity labelling, occurrence-validity/election behavior, golden
case IDs G35–G46 and CT4 milestone boundaries. Any actuarial change requires a
versioned review before coding.
