"""Process-boundary fixtures; never called by the public API."""
import os
from pathlib import Path
import time


def delayed_marker(sender, started_path: str, completed_path: str):
    Path(started_path).write_text(str(os.getpid()), encoding="utf-8")
    time.sleep(2)
    Path(completed_path).write_text("unexpected completion", encoding="utf-8")
    sender.send_bytes(b"unexpected authoritative result")


def orphan_marker(sender, started_path: str, completed_path: str):
    from cat_treaty.ct8_executor import _watch_parent_or_exit
    _watch_parent_or_exit()
    Path(started_path).write_text(str(os.getpid()), encoding="utf-8")
    time.sleep(2)
    Path(completed_path).write_text("orphan survived", encoding="utf-8")
    sender.send_bytes(b"unexpected")
