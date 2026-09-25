# CT8 bounded workload generator correction

The first Windows run stopped with `CT6_DOMAIN_VALIDATION` because expanded
trials reused the same `event_id` across the simulation. CT6 freezes global
event ID uniqueness and requires the CT2 `loss_basis.occurrence_id` to match.
The generator now creates a unique identifier in both locations for each
trial. No API handler, treaty engine or frontend code changed. A new
standard-library test checks this invariant for 1, 10 and 100 trials.

The first failed run provides no resource result. Rerun the corrected bounded
measurement only; do not infer public workload safety from it.
