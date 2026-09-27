"""Dependency-free Linux process-group cleanup experiment; not wired to CT6."""
import importlib.util
import multiprocessing as mp
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time

module_path = Path(__file__).resolve().parents[1] / "cat_treaty" / "ct8_process_tree.py"
spec = importlib.util.spec_from_file_location("ct8_process_tree_probe", module_path)
tree = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tree)


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def child(started, descendant, finished):
    tree.enter_child_group()
    parent = mp.parent_process()
    if parent is None:
        os._exit(2)

    def watchdog():
        parent.join()
        tree.stop_own_group()

    threading.Thread(target=watchdog, daemon=True).start()
    grandchild = subprocess.Popen([sys.executable, "-c",
        "import pathlib,sys,time;time.sleep(2);pathlib.Path(sys.argv[1]).write_text('survived')",
        finished], stdin=subprocess.DEVNULL)
    Path(descendant).write_text(str(grandchild.pid), encoding="ascii")
    Path(started).write_text(str(os.getpid()), encoding="ascii")
    time.sleep(5)


def worker(mode, started, descendant, finished):
    process = mp.get_context("spawn").Process(target=child, args=(started, descendant, finished))
    process.start()
    for _ in range(100):
        if Path(started).exists():
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("calculation child did not start")
    if mode == "abrupt":
        os._exit(7)
    tree.stop_spawned_group(process.pid)
    process.join(timeout=3)
    if process.is_alive():
        raise RuntimeError("calculation child survived group kill")


def main():
    if sys.platform != "linux":
        raise RuntimeError("Linux-only experiment")
    with tempfile.TemporaryDirectory(prefix="ct8-linux-tree-") as directory:
        root = Path(directory)
        for mode in ("deadline", "abrupt"):
            started, descendant, finished = [root / f"{mode}-{name}.txt"
                for name in ("started", "descendant", "finished")]
            worker_process = subprocess.Popen([sys.executable, __file__, "--worker", mode,
                str(started), str(descendant), str(finished)], stdin=subprocess.DEVNULL)
            try:
                if worker_process.wait(timeout=12) != (7 if mode == "abrupt" else 0):
                    raise RuntimeError(f"{mode} worker did not reach expected exit")
                if not started.exists() or not descendant.exists():
                    raise RuntimeError(f"{mode} missed a started calculation or descendant")
                time.sleep(2.3)
                child_live = alive(int(started.read_text()))
                descendant_live = alive(int(descendant.read_text()))
                if finished.exists() or child_live or descendant_live:
                    raise RuntimeError(f"{mode} left live work: finished={finished.exists()}, "
                        f"child={child_live}, descendant={descendant_live}")
                print(f"Linux process-group {mode}: PASS (child and descendant stopped)")
            finally:
                if worker_process.poll() is None:
                    worker_process.kill()
                    worker_process.wait()


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--worker":
        worker(*sys.argv[2:])
    else:
        main()
