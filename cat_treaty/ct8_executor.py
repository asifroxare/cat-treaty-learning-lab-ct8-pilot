"""Opt-in CT8 process boundary around the frozen CT6 orchestration functions.

The application stays on the CT6 synchronous path unless CT8_ISOLATED_RUNS is
explicitly enabled. This module never changes treaty calculations.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import pickle
import subprocess
from queue import Queue, Empty
import threading
import time
from typing import Literal

from cat_treaty.ct6_hours import CT6HoursContractBlockedError
from cat_treaty.simulation import CT4PreflightError

MAX_RESULT_BYTES = 128 * 1024 * 1024


class CT8ExecutionTimeout(RuntimeError):
    """An isolated run exceeded the deployment deadline."""


class CT8ExecutionFailure(RuntimeError):
    """A child failed without a complete authoritative result."""


def _watch_parent_or_exit():
    """Make a child exit if its API worker dies without running cleanup."""
    parent = mp.parent_process()
    if parent is None:
        raise CT8ExecutionFailure("isolated child has no parent sentinel")

    def stop_on_parent_exit():
        parent.join()
        if os.name == "nt":
            # The calculation may have a launcher or another subprocess.
            # The worker's finally block cannot run after abrupt worker exit.
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(os.getpid())],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        os._exit(1)

    threading.Thread(target=stop_on_parent_exit, daemon=True).start()


def _child(sender, mode, request):
    _watch_parent_or_exit()
    try:
        if mode == "catalogue":
            from cat_treaty.ct6_orchestration import run_catalogue
            message = ("ok", run_catalogue(request))
        elif mode == "hours-clause":
            from cat_treaty.ct6_hours import run_hours_clause
            message = ("ok", run_hours_clause(request))
        else:
            message = ("internal", None)
    except CT4PreflightError as error:
        message = ("preflight", error.issues)
    except CT6HoursContractBlockedError as error:
        message = ("hours_blocked", error.result)
    except (TypeError, ValueError):
        message = ("domain", None)
    except BaseException:
        message = ("internal", None)
    try:
        serialized = pickle.dumps(message, protocol=5)
        if len(serialized) > MAX_RESULT_BYTES:
            serialized = pickle.dumps(("internal", None), protocol=5)
        sender.send_bytes(serialized)
    finally:
        sender.close()


def run_isolated(mode: Literal["catalogue", "hours-clause"], request: object, *, deadline_seconds: float):
    """Return a complete engine result or raise a reviewed CT6 error category."""
    if mode not in ("catalogue", "hours-clause") or not 1 <= deadline_seconds <= 300:
        raise ValueError("invalid CT8 execution configuration")
    payload = _run_process(_child, (mode, request), deadline_seconds)
    tag, value = pickle.loads(payload)  # trusted bytes from our spawned child only
    if tag == "ok":
        return value
    if tag == "preflight":
        raise CT4PreflightError(value)
    if tag == "hours_blocked":
        raise CT6HoursContractBlockedError(value)
    if tag == "domain":
        raise ValueError("isolated domain validation failed")
    raise CT8ExecutionFailure("isolated computation failed")


def _run_process(target, args: tuple, deadline_seconds: float) -> bytes:
    """One disposable process; internal seam for exact timeout tests."""
    if deadline_seconds <= 0:
        raise ValueError("deadline must be positive")
    context = mp.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    child = context.Process(target=target, args=(sender, *args), daemon=True)
    started = time.monotonic()
    try:
        child.start()
    except BaseException:
        sender.close()
        receiver.close()
        raise
    sender.close()
    completed: Queue = Queue(maxsize=1)

    def read_result():
        try:
            completed.put(("bytes", receiver.recv_bytes(MAX_RESULT_BYTES)))
        except (EOFError, OSError) as error:
            completed.put(("closed", type(error).__name__))

    reader = threading.Thread(target=read_result, daemon=True)
    reader.start()
    try:
        while True:
            remaining = deadline_seconds - (time.monotonic() - started)
            if remaining <= 0:
                raise CT8ExecutionTimeout("isolated deadline expired")
            try:
                state, payload = completed.get(timeout=min(remaining, 0.05))
                break
            except Empty:
                if not child.is_alive():
                    # Give a cleanly exiting child a moment to finish the pipe.
                    reader.join(timeout=0.05)
                    if not reader.is_alive():
                        try:
                            state, payload = completed.get_nowait()
                            break
                        except Empty:
                            raise CT8ExecutionFailure("child exited without a complete response")
        if state != "bytes":
            raise CT8ExecutionFailure("child pipe closed without a complete response")
        return payload
    finally:
        if child.is_alive() and os.name == "nt":
            # Windows virtualenv executables can launch a child interpreter.
            # Terminate the complete process tree, not just the launcher.
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(child.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        elif child.is_alive():
            child.terminate()
        child.join(timeout=2)
        if child.is_alive():
            child.kill()
            child.join(timeout=2)
        receiver.close()
        reader.join(timeout=0.1)
        if child.is_alive():
            raise CT8ExecutionFailure("could not terminate isolated child")
