# CT8 Linux process-tree experiment — unconnected prototype

The reviewer identified that Windows `taskkill /T /F` does not establish
Linux process-tree cleanup. `deployment/linux_tree_probe.py` is a dependency-
free experiment, deliberately separate from production `ct8_executor.py`.
It starts a spawned calculation child in its own POSIX session and process
group, then starts a descendant. It runs two cases: a deadline-style
`killpg(SIGKILL)` by the worker, and abrupt worker `os._exit(7)` followed by
a child watchdog waiting on the multiprocessing parent sentinel and killing
its own process group. Each case verifies no completion marker and that both
PIDs are no longer addressable through `os.kill(pid, 0)` in the same PID
namespace. Both cases passed in the Work Linux execution container on
27 September 2026. A deployment-tool unit test repeats the experiment.

The tested helpers are now in `cat_treaty/ct8_process_tree.py` and the optional
executor invokes them through a spawned-child entry function. This is an
implementation candidate, still OFF publicly. This container has an 8 GiB
cgroup limit but lacks Docker and the FastAPI, Uvicorn and pytest backend
dependencies. The same dependency-free Linux container also exercised the
actual CT8 `_run_process` with a spawned descendant: deadline expiration and
abrupt API-worker exit both stopped the child and descendant. This path
passed in `deployment/linux_executor_probe.py`. It is **not** a full-engine
Linux capacity result or a Linux API test. A full backend suite on Windows,
full API Linux integration, and a reviewed Linux run under an OS-enforced
resource limit remain OPEN.

The harness imports the exact production helper module by filesystem path so
it does not import the package's FastAPI-dependent `__init__` in this
dependency-free environment. The execution container presents a `/proc` view whose PID numbers differ
from `os.getpid()` in the probe's PID namespace. The test uses `os.kill(pid,
0)` in the same namespace to avoid a false liveness verdict; on the real
staging host, separately inspect cgroup processes and descendants.
