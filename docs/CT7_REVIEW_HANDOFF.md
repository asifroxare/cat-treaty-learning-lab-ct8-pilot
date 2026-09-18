# CT7 Independent Review Handoff

Please review `CT7_IMPLEMENTATION_SPEC.md` as a contract, not as a UI style
proposal. Identify contradictions, missing states, calculation leakage,
misleading educational behavior or untestable completion gates.

## Review priorities

1. **Actuarial authority:** all monetary and statistical results must originate
   in CT6; frontend formatting must not become calculation.
2. **Product separation:** this treaty lab must remain distinct from the Cat
   XOL Pricing Learning Lab.
3. **Learning integrity:** explanations must answer why without inventing
   results or optimizing a contractual choice.
4. **Occurrence integrity:** hours-clause admissibility must gate election and
   invalid higher-recovery splits must remain visible as rejected evidence.
5. **Capacity integrity:** pre-capacity entitlement, post-capacity recovery,
   shortfall, reinstatement premium and net cash must remain distinct.
6. **Boundary integrity:** negative cash and null utilization statuses must
   survive presentation unchanged.
7. **Failure integrity:** invalid, blocked, stale, offline and internal-error
   states must never masquerade as successful current results.
8. **Testability:** G84–G103 and the completion gate must be objectively
   implementable.

## Requested response format

For each finding provide:

- ID;
- affected section;
- severity: blocking, major, minor or cosmetic;
- finding and why it matters;
- required revision; and
- required regression/golden-case evidence.

Then answer all questions in Section 27 and give one verdict:

- ready to freeze;
- ready after listed revisions; or
- structural revision required.

No frontend implementation should be reviewed or generated during this
specification review.
