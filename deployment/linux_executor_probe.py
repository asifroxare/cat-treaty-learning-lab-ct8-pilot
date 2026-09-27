"""Linux CT8 executor lifecycle test without importing FastAPI's app module."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# The project package initializer imports FastAPI. The actual executor and
# process-tree module do not need it for this lifecycle probe.
package = types.ModuleType("cat_treaty")
package.__path__ = [str(ROOT / "cat_treaty")]
sys.modules["cat_treaty"] = package

from cat_treaty.ct8_executor import CT8ExecutionTimeout, _run_process
from tests.ct8_child_fixtures import orphan_descendant


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def check(started, descendant, finished):
    if not started.is_file() or not descendant.is_file():
        raise RuntimeError("computation and descendant must both start")
    time.sleep(3.3)
    if finished.exists() or alive(int(started.read_text())) or alive(int(descendant.read_text())):
        raise RuntimeError("CT8 executor left a live calculation child or descendant")


def orphan_parent(started, descendant, finished):
    thread = threading.Thread(target=_run_process,
        args=(orphan_descendant, (str(started), str(finished), str(descendant)), 10), daemon=True)
    thread.start()
    for _ in range(200):
        if started.exists() and descendant.exists():
            os._exit(7)
        time.sleep(0.05)
    os._exit(8)


def main():
    if sys.platform != "linux":
        raise RuntimeError("Linux-only executor probe")
    with tempfile.TemporaryDirectory(prefix="ct8-linux-executor-") as directory:
        folder = Path(directory)
        for mode in ("deadline", "abrupt"):
            started = folder / f"{mode}-started.txt"
            descendant = folder / f"{mode}-descendant.txt"
            finished = folder / f"{mode}-finished.txt"
            if mode == "deadline":
                try:
                    _run_process(orphan_descendant,
                        (str(started), str(finished), str(descendant)), 1.5)
                except CT8ExecutionTimeout:
                    pass
                else:
                    raise RuntimeError("deadline did not expire")
            else:
                worker = subprocess.Popen([sys.executable, __file__, "--orphan",
                    str(started), str(descendant), str(finished)], cwd=ROOT)
                if worker.wait(timeout=15) != 7:
                    raise RuntimeError("abrupt worker failed before child started")
            check(started, descendant, finished)
            print(f"Linux CT8 executor {mode}: PASS (child and descendant stopped)")


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--orphan":
        orphan_parent(*(Path(item) for item in sys.argv[2:]))
    else:
        main()
