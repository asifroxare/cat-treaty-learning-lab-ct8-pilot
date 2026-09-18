# CT7 Specification Freeze Record

**Specification:** CT7 Learning Lab Frontend, Interactive Experiments and Explanation Experience  
**Frozen version:** v1.3  
**Specification SHA-256:** `5defc13a724fcdfd2fb27a3db3ad2e068e30ade30f37bdc03251074e04871514`  
**Review outcome:** F01–F10 closed; no open findings  
**Authorization:** CT7 checkpoint 2 may begin

## Review history

| Revision | Findings resolved | Outcome |
|---|---|---|
| v1.0 | Initial independent review raised F01–F08 | Revision required |
| v1.1 | Learning integrity, stale state, error mapping, static gate and documentation controls | F01–F08 closed; F09 raised |
| v1.2 | Checked presentation-geometry boundary and expanded G102 | F09 closed; F10 text-sync raised |
| v1.3 | §23 synchronized with §7.2 and G102 fixture requirements | F10 closed; ready to freeze |

## Frozen authorities

- frontend performs no actuarial calculation;
- CT6 remains the sole source of authoritative numerical results;
- Catastrophe Treaty and Cat XOL Pricing labs remain distinct products;
- execution state and result freshness remain separate;
- CT6 error codes map deterministically to frontend states;
- explanations require resolvable evidence and neutral learning content;
- comparison is side-by-side without output deltas or difference badges;
- visualization arithmetic is restricted to the checked branded geometry
  boundary;
- G84–G105 are mandatory; and
- public deployment remains outside CT7 until later deployment-readiness work.

## Verification at freeze

```text
CT7 v1.3 structural gates: PASS
CT1–CT6 regression: 1003 passed, 2 upstream deprecation warnings
Frontend implementation: not started
```

## Change control

Any behavioral change requires a versioned addendum, impact analysis and
independent review. This record authorizes only the checkpoint sequence frozen
in §25, beginning with checkpoint 2: frontend foundation, design tokens,
routing and CT6 client contract.
