# CT6 Independent Audit Disposition

**Specification:** CT6 FastAPI Contract and Backend Orchestration v1.0  
**Baseline:** CT5 commit `a589d4a`  
**Disposition:** All review findings resolved; CT6 specification frozen

| ID | Review finding | Resolution |
|---|---|---|
| CT6-A | Seed nullability lacked a catalogue provenance discriminator | Added mandatory `catalogue_source_mode = generated | supplied`; generated requires a non-negative seed and supplied requires null. Both modes still carry explicit trials in CT6 v1. |
| CT6-B | Hours-clause orchestration handoff was underspecified | Added a separate 16-step hours sequence covering disclosed CT2 source validation, CT3 construction, admissibility, election, CT4 identity and CT5 processing. |
| CT6-C | 400/409/422 error precedence was implicit | Froze precedence and distinguished an unsupported string version (409) from a missing or wrong-typed version (422). |
| CT6-D | Full-detail cap could appear inconsistent with deterministic inputs | Declared it a presentation-only limit: summary may succeed where full receives 413; successful authoritative hashes remain projection-independent. |
| CT6-E | Hours bounds were only implicit | Confirmed catalogue count limits are catalogue-only; hours mode is exactly one trial and 1–12 components. |
| CT6-F | Synchronous limits were generous for a learning lab | Reduced the ceiling to 10,000 trials and 100,000 occurrences; retained 25,000 full-detail rows. |
| CT6-G | Free-text errors could leak internal information | Required all public title/detail/message text to come from a reviewed static catalogue without internal exception or client-value interpolation. |
| CT6-H | Version-conflict behavior lacked a golden case | Added G83 for 409 versus 422 version behavior. |
| CT6-I | Authoritative response field names were not pinned | Added the exact pre-capacity, post-capacity, settlement, shortfall and layer-capacity names in Section 11.8. |
| CT6-J | Ten reviewer questions remained open | Replaced them with frozen decisions in Section 23. |

The reviewer accepted raw CT2 catalogue inputs, separate catalogue/hours
routes, HTTP 422 for contractual blockage, cumulative warnings under HTTP 200,
and summary-mode audit evidence. G77 must include warnings and election evidence
in addition to a clean catalogue comparison.

No FastAPI implementation was added while resolving this audit. Implementation
may begin only through the checkpoint sequence in Section 21 of the frozen
specification.
