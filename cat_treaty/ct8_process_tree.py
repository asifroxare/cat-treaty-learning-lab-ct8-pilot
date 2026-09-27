"""Small OS process-tree boundary for optional CT8 isolation."""
import os
import signal
import subprocess


def enter_child_group():
    """Make a POSIX spawned computation the leader of a separate session."""
    if os.name == "posix":
        os.setsid()


def stop_own_group():
    """Called by a child watchdog after its API worker exits abruptly."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(os.getpid())],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        os.killpg(os.getpgrp(), signal.SIGKILL)
    os._exit(1)


def stop_spawned_group(pid):
    """Stop a spawned calculation and its descendants, including a launcher."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            # Child may be killed before enter_child_group() executes.
            pass
