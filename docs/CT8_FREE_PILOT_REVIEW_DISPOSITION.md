# CT8 invited free-pilot implementation — independent review disposition

**Received 27 September 2026. Status: implementation review accepted for
continued work; staging and invited release remain blocked.** The reviewer
read the security-sensitive code and found no new blocking code defect, but
could not install dependencies and did not independently run the tests. The
Work Linux suite of 1,021 backend passes, one Windows-only skip, 73 standard
frontend passes and one real-CT6-API acceptance pass is separate evidence;
it does not substitute for a live pilot topology test.

| Finding | Disposition |
| --- | --- |
| Auth, host/origin proof, early body/shape limits and separate routes | Accepted as static implementation review only. Verify actual Cloudflare Access JWT, Worker secret replacement, Render Host handling, cross-origin preflight and direct-origin negative tests before invitations. |
| One worker / one instance | Mandatory configuration and staging check. The semaphore is per Python process; additional workers or instances would multiply capacity. Do not advertise a global slot until deployment settings are inspected and probed. |
| OS resource cap | Open launch gate. The opt-in computation has a deadline and serialized-result cap but no child-specific hard memory/CPU limit. Render Free's instance memory bound may terminate the entire service; measure the *whole* API process tree and rejection behavior under an actual free-sized limit before choosing pilot dimensions. |
| Busy/deadline/crash operator diagnosis | Distinct pilot busy response exists; timeout and crash map to a generic client failure. Record safe internal reason categories and counters without payloads, identities or exception text before enabling monitoring; do not silently change CT6 public errors. |
| Test evidence | Reviewer performed static inspection, not a reproduction. Pilot test suite and baseline were run in Work Linux; Windows and actual provider topology remain separate. |
| Frozen actuarial and learning evidence | CT0–CT7 calculations and CT6 reference endpoints remain unchanged. Continue golden and reconciliation comparisons for enabled pilot routes and browser learning paths. |

**Numerical correction to the review text:** the 10,000-trial/25,000-row
*one-layer Linux* direct-engine run was **27.529 seconds**, **91,939,829
pickled bytes** and **835,600 KiB worker peak RSS**. The **18.5238-second**
Windows run was the separate 10,000-trial, *one occurrence per trial*
fixture, with **43,940,239 pickled bytes**. The four-layer, 25,000-row Linux
run was **36.497 seconds**, **120,092,827 pickled bytes**, and **1,150,288
KiB worker peak RSS**. None of these included a full Free-host API process
tree. See `CT8_LINUX_CAPACITY_EVIDENCE.md` and
`CT8_TRIAL_LIMIT_EVIDENCE.md`.

**Next gate:** prepare the exact staging settings and measurement/checklist
for a dedicated 512 MB/0.1 CPU Render Free instance **without deploying**;
define numerical pilot limits only after whole-API measurement with safe
stops. Confirm audience, DNS and any cost before the owner approves any
staging/test URL. Do not create a host, modify DNS or invite testers from
this review alone.
