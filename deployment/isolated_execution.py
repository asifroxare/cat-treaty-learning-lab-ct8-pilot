"""CT8 prototype: bound one CPU-bound task in a disposable child process.

Not connected to the frozen CT6 API. Review transport/error behavior before use.
"""
from dataclasses import dataclass
import importlib
import multiprocessing as mp
import time


class ExecutionExpired(RuntimeError):
    pass


class ExecutionFailed(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionEvidence:
    value: object
    elapsed_seconds: float
    child_pid: int


def _child(sender, module_name, function_name, payload):
    try:
        if not module_name.startswith(("cat_treaty.", "isolation_fixtures")):
            raise ValueError("module is not an approved CT8 execution target")
        function = getattr(importlib.import_module(module_name), function_name)
        value = function(payload)
        sender.send(("ok", value))
    except BaseException:
        # Do not send exception text or user payload back across this boundary.
        sender.send(("error", None))
    finally:
        sender.close()


def execute(module_name: str, function_name: str, payload: object, *, timeout_seconds: float) -> ExecutionEvidence:
    if not 0.05 <= timeout_seconds <= 300:
        raise ValueError("deadline must be between 0.05 and 300 seconds")
    if not module_name.startswith(("cat_treaty.", "isolation_fixtures")):
        raise ValueError("module is not an approved CT8 execution target")
    receiver, sender = mp.get_context("spawn").Pipe(duplex=False)
    process = mp.get_context("spawn").Process(target=_child,
        args=(sender, module_name, function_name, payload), daemon=True)
    start = time.monotonic()
    process.start()
    sender.close()
    try:
        if not receiver.poll(timeout_seconds):
            raise ExecutionExpired("isolated calculation deadline expired")
        try:
            status, value = receiver.recv()
        except EOFError as error:
            raise ExecutionFailed("isolated calculation exited without a complete result") from error
        if status != "ok":
            raise ExecutionFailed("isolated calculation failed")
        return ExecutionEvidence(value, time.monotonic() - start, process.pid)
    finally:
        receiver.close()
        if process.is_alive():
            process.terminate()
        process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join(timeout=2)
        if process.is_alive():
            raise ExecutionFailed("isolated child could not be stopped")
