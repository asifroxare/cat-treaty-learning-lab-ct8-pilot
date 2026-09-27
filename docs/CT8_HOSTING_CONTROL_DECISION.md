# CT8 hosting control decision — draft for independent review

**Status:** candidate configuration only, no deployment or paid-plan selection.

The validated one-slot semaphore is per Python API worker. Candidate staging
launch therefore requires exactly one Render service instance and one Uvicorn
worker, with autoscaling disabled. The intended public hostname should be a
Cloudflare-proxied custom API subdomain belonging only to the Catastrophe
Treaty Learning Lab. The `onrender.com` default address must be disabled (or
otherwise demonstrably inaccessible) before Cloudflare rate rules can count
as an effective public API ingress control. Render documents an option to
disable its default subdomain after adding a custom domain. A direct-address
probe must prove that bypass is blocked.

Cloudflare's rate limiting rules can target API routes, but the actual plan,
available rule features, thresholds, response codes and global active-run cap
remain unselected. A rate rule based only on visitor IP is not equivalent to
a global count of active computations; do not claim it solves concurrency.
The application's single worker plus one isolated slot rejects simultaneous
runs on that one instance, but these guards must be tested at the deployed
host with edge behavior. Validate ingress 25 MiB body handling, streaming
rejections, forwarded-header trust, trusted hosts, TLS and exact CORS origins.
Record which failures come from the edge rather than the CT6 problem schema.

Render documents that Free web services spin down after 15 idle minutes and
can take about one minute to spin up. This is a material usability and
availability consideration for the interactive lab; a free tier has not been
approved as suitable. Compute RAM, CPU, instance count and cost need the
remaining worst-legal workload measurements. Do not buy a plan based on the
current 5,000-trial sample.

Official references checked 27 September 2026:
- https://render.com/docs/custom-domains
- https://render.com/docs/scaling
- https://render.com/docs/free
- https://developers.cloudflare.com/waf/rate-limiting-rules/
- https://developers.cloudflare.com/workers/platform/limits/

Open reviewer questions: Does the intended Render plan support disabling the
default subdomain and holding instance count to one? Can the intended
Cloudflare zone enforce a reviewed rate policy at the API hostname? What
global active-run and rate thresholds are supported by measured worst-case
capacity? What distinct edge error and CT6 error precedence will users see?
