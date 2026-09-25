"""Abruptly end a worker after it spawns a monitored calculation child."""
import os
from pathlib import Path
import sys
import threading
import time

from cat_treaty.ct8_executor import _run_process
from tests.ct8_child_fixtures import orphan_marker


def main():
    started, completed = sys.argv[1:]
    thread = threading.Thread(target=_run_process,
        args=(orphan_marker, (started, completed), 10), daemon=True)
    thread.start()
    for _ in range(100):
        if Path(started).exists():
            os._exit(7)  # no atexit, no graceful multiprocessing cleanup
        time.sleep(0.05)
    os._exit(8)


if __name__ == "__main__":
    main()
