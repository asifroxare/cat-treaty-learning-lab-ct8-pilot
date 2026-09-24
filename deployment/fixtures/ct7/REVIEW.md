# Synthetic CT7 baseline candidates — provenance reviewed, coverage limited

Generated on Windows by `deployment/export_ct7_goldens.py` from the clean exact
CT7 commit `2a45727b9621a860ee074d6b14172b65fd836ad3` and supplied by the
project owner. Both input file SHA-256 hashes match the manifest. The exporter
normalizes only the transport field `api.request_id` in the full response.
The response digests were produced by the user's CT7 installation and have
not yet been independently recalculated in the Work workspace.

Catalogue fixture: one supplied annual trial, one occurrence, one Cat XL
layer (20m xs 10m), 10% quota-share inuring cover, one excluded salvage
component, one paid reinstatement tranche and full response. The existing
CT6 G70 test independently expects a pre- and post-capacity gross recovery of
20m for this fixture constructor.

Hours fixture: two wind components linked to one causal storm at 10 and 100
hours, a 72-hour window, maximum-subject-loss election among the authorized
methods, one layer and a paid reinstatement tranche. This tests one selection
path. It does not exercise manual election, alternative peril/region exclusion,
annual exhaustion or the maximum legal catalogue workload.

The full-response digest detects changes to *any* retained response fields
including settlement components, warnings and candidate evidence for these
specific scenarios. It is a regression baseline, not independent validation
of treaty arithmetic or exhaustive boundary coverage. Keep the broader frozen
CT0–CT7 test suite and browser workflows as separate gates.
