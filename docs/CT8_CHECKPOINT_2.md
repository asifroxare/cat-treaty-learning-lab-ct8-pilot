# CT8 checkpoint 2 — staging evidence gates

Parent CT8 checkpoint: `f6385b51472bce3a8dd0bc13933ecdcd5c1eef66`.
CT7 frozen parent: `2a45727b9621a860ee074d6b14172b65fd836ad3`.

Added staging HTTPS acceptance with approved input/output fixture hashes,
release source-commit verification, and a release gate matrix. The only
transport normalization allowed is `api.request_id`; changes to settlement
components and exclusion evidence alter the digest. No CT0–CT7 calculation,
API behavior or React component was modified.

Local verification: standard-library compile and CLI parsing PASS; digest
mutation smoke PASS; unapproved source commit rejected. The backend suite and
frontend suite could not be rerun because their dependencies were unavailable
in the current workspace; original CT7 Windows evidence remains historical,
not evidence of this CT8 checkpoint. No staging host, provider config or
physical browser was available. Every launch row remains OPEN.

Independent reviewer should check: (1) intended canonical business response
fields and the single request-ID normalization; (2) path and cache assertions
against the chosen hosting provider; (3) missing resource isolation, request
limit and error precedence implementation; and (4) that this checkpoint is
clearly labelled predeployment and does not overwrite CT7.
