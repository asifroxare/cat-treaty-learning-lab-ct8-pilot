# CT8 independent capacity and hosting review

**Date:** 27 September 2026. **Status:** predeployment review candidate.
**Deployment:** none. **Actuarial code:** CT0–CT7 remains frozen in Python.
**Frontend:** CT7 presentation and interaction remain unchanged.

## Verified evidence and limits

| Evidence | Result | Practical limit |
| --- | --- | --- |
| Owner Windows backend suite on watchdog review | 1,012 passed | This precedes later measurement-script-only changes. |
| Guided frontend, real local CT6 API and build audit | 72 frontend, one real API acceptance, audit PASS on earlier isolation review | Frontend source did not change in subsequent probe packages. |
| Frozen synthetic CT7 golden comparisons | Two full-response digests MATCH | Only catalogue and hours fixture scenarios; not actuarial proof for other inputs. |
| 1,000 full-detail isolated HTTP trials | 3.3565s, 7,409,041 response bytes, 231.46 MiB observed process-tree peak | Local one-occurrence, one-layer request; HTTP JSON bytes differ from pickle bytes. |
| 5,000 full-detail direct Python trials | 9.0436s, 21,972,222 pickled bytes, 255.04 MiB observed peak | Direct orchestration, not API ingress or staging. |
| 10,000 full-detail direct trials with one occurrence/layer | 18.5238s, 43,940,239 pickled bytes, 424.97 MiB observed peak | Exact trial count limit only. |
| Legal 10,000-trial/25,000-occurrence full-detail input | 22,705,383 request bytes; stopped at 30s | No authoritative result or completion size. |
| Same legal input, extended local probe | Stopped at observed 800 MiB process-tree guard, after 26s progress | No authoritative result or final peak. |

The process-tree probe sums sampled Windows working-set values; shared pages
can be double counted, and short peaks can be missed. No single figure above
is a guaranteed minimum RAM allocation. The 25,000-row fixture is within the
frozen 25 MiB input and full-detail-row limits. The 100,000-occurrence,
four-layer and hours-candidate maxima are still unmeasured.

## Current architecture candidate

Cloudflare Pages would serve an immutable Vite build; an exact HTTPS API
origin would serve CT6 on a dedicated Render service, separate from Cat XOL
Pricing Lab and the existing Quota Share Lab. The local opt-in process guard
uses a single app worker and one slot; its 30s default cannot serve the
measured legal row-limit fixture. Public `CT8_ISOLATED_RUNS` stays OFF.

Candidate ingress requires a Cloudflare-proxied API hostname and verified
direct-origin bypass prevention (including Render's `onrender.com` hostname),
exact CORS and trusted hosts, TLS, body streaming behavior, rate limiting and
global admission. One worker/one instance must be enforced and audited for
this per-process semaphore to be a global application slot. The Cloudflare
default 125s proxy read timeout constrains synchronous legal workloads.

Render currently lists 512 MB RAM for Free services and larger paid plan
sizes. Neither the Free plan nor any paid size is approved by these partial
measurements. The Free plan also idles after 15 minutes and can take about a
minute to restart. No billing, service, DNS or deployment has been created.

## Proposed decision

Preserve CT6's frozen legal input bounds. Do not enable the current isolated
executor publicly until a representative legal worst-case completes under a
reviewed memory limit and deadline on the selected host, with a result below
the validated IPC cap. Measure the response through the actual API and edge.
Size one host from that result, set explicit cost and global limits, then
stage the complete frontend/backend pair. If this proves unaffordable or
incompatible with the synchronous edge path, prepare a **separate versioned
transport proposal** for owner and independent review; never silently narrow
CT6 or alter CT0–CT7 actuarial results.

Do not deploy before security and precedence checks, real-browser and
accessibility acceptance, monitoring and incident ownership, exact immutable
artifact review, and a compatible rollback drill all pass. The owner must
approve the exact release digest, domains and costs as the final step.

## Exact questions for Claude

1. Given the documented completed 10,000-trial/one-occurrence result and the
   two independent stops on the legal 25,000-row fixture, is it correct to
   mark the 30s deadline and current public hosting candidate blocked? Which
   claims in this memo overstate the evidence?
2. Does summing sampled Windows process-tree working sets support excluding a
   512 MB Render Free instance, and what additional Linux host evidence is
   required before recommending a paid plan and a memory ceiling?
3. Does the 22,705,383-byte, 10,000-trial/25,000-occurrence fixture satisfy
   CT6's schema, domain, input and full-detail-row contracts? What combined
   legal workload dimensions are missing, especially four layers and hours
   candidate expansion?
4. How should the child-result 128 MiB cap and execution deadline be tested
   for a complete legal result without making the owner's 16 GB Windows
   computer or the future host unstable? Specify an abort and cleanup check.
5. For the proposed Cloudflare Pages plus Render API topology, can a single
   instance/worker plus the current semaphore enforce global active work?
   How would you verify no direct-origin bypass, edge rate controls, trusted
   proxy/host behavior and error precedence in staging?
6. Can a synchronous legal maximum complete comfortably before the relevant
   Cloudflare and Render timeouts? If not, identify the smallest versioned
   transport change needed, while preserving frozen CT0–CT7 calculations,
   deterministic identities, reconciliations and learning-integrity controls.
7. Identify any CT8 implementation defect or missing launch gate that should
   block an independent reviewer from recommending staging or public launch.

## Source documents

`CT8_ROW_LIMIT_EVIDENCE.md`, `CT8_TRIAL_LIMIT_EVIDENCE.md`,
`CT8_SERIALIZED_SIZE_EVIDENCE.md`, `CT8_ISOLATION_SCALING_EVIDENCE.md`,
`CT8_CLAUDE_REVIEW_DISPOSITION.md`, `CT8_HOSTING_CONTROL_DECISION.md`, and
`CT8_CAPACITY_DECISION.md` are included in the full repository package.

Provider documentation checked 27 September 2026:
- https://render.com/docs/compute-plans
- https://render.com/docs/free
- https://render.com/docs/custom-domains
- https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/
- https://developers.cloudflare.com/waf/rate-limiting-rules/
