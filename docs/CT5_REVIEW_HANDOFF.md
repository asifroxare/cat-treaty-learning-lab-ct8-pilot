# CT5 Independent Review Handoff

Please review `CT5_IMPLEMENTATION_SPEC.md` as a proposed actuarial and software
contract, not as implemented behavior.

Focus especially on:

- F25–F29 annual-capacity state transitions;
- same-occurrence versus later-occurrence reinstatement availability;
- partial and ordered tranche allocation;
- F30 amount/time premium mechanics;
- premium after the final observed event;
- F31 paid-separately versus deducted presentation;
- F32–F36 event, annual, capacity and reserve reconciliations;
- utilization denominators and zero-capacity conventions;
- the five post-capacity analytics perspectives; and
- the sufficiency of G47–G62.

For each finding, provide:

| Field | Required content |
|---|---|
| ID | Stable reference such as CT5-A |
| Section/formula | Exact location |
| Severity | Blocking, material, low or cosmetic |
| Finding | Concrete contradiction, ambiguity or omission |
| Required revision | Exact behavior or wording needed |
| Test | Golden or regression evidence required |

Please also answer all fifteen questions in section 23 and state one verdict:

- fit to freeze as written;
- fit to freeze after listed revisions; or
- structural revision required.

No CT5 code should be reviewed or requested at this stage because implementation
has not begun.
