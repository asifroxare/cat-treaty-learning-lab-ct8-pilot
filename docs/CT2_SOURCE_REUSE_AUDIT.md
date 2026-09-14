# CT2 Source-Reuse Audit

**Status:** Complete  
**Date:** 14 September 2026  
**Purpose:** Close deferred finding CT1-C before CT2 implementation

## Conclusion

The completed Cat XOL Pricing Lab remains the authority for its existing
synthetic catalogue and validated pricing-product results. Its occurrence
recovery function must **not** be called as the Cat Treaty program engine once
Ultimate Net Loss or inuring reinsurance applies.

## Source-level findings

| Source component | Finding | CT2 decision |
|---|---|---|
| `catalogue.py` | Produces `gross_event_loss` using pricing-product peril, region and vulnerability assumptions | May supply the initial event loss through the CT1 adapter; never label it Ultimate Net Loss automatically |
| `recovery.apply_occurrence_treaty` | Applies attachment directly to `event.gross_event_loss` | Do not reuse for post-inuring Cat XL recovery |
| `recovery.apply_occurrence_treaty` | Assumes one occurrence layer and one annual capacity ledger | Do not generalize inside CT2; CT3 owns the new program engine |
| `recovery.apply_occurrence_treaty` | Embeds two-risk warranty, reinstatement and chronological annual processing | Keep behind the pricing compatibility boundary only |
| `ProcessedEventRecord.net_event_loss` | Means pricing-product gross event loss less its current layer recovery | Preserve as legacy output; never overload as an intermediate CT2 loss stage |
| `analytics.py` | Reads pricing-product gross and recovery records directly | Do not reuse until later program analytics receive a separate canonical input contract |
| `pricing.py` | Uses one occurrence limit as the ROL, payback and capital-loading basis | Do not call for a multi-layer program; later pricing must declare its limit and participation basis |
| Validation and deterministic ordering patterns | Product-agnostic | Reuse the patterns, not pricing-specific objects or hidden assumptions |

## Enforced boundary

CT2 creates pure modules for named loss-basis construction and ordered inuring.
They may depend on canonical CT1 domain types, but they must not import
`cat_xol.recovery`, `cat_xol.analytics`, `cat_xol.pricing`, an API module, a
frontend module or a user-specific filesystem path.

The CT3 Cat XL tower may consume only a CT2 result whose
`inuring_completion_status` is complete. This prevents the original
`gross_event_loss` shortcut from returning through a later integration path.

