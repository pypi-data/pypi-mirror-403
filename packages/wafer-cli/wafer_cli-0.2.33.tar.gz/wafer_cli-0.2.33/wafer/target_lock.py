"""Target locking for concurrent access control.

Uses file locks (fcntl.flock) to ensure only one process uses a target at a time.
Locks are automatically released when the process exits or crashes.

Usage:
    # Try to acquire a single target
    with try_acquire_target("mi300x-1") as acquired:
        if acquired:
            # Got the lock, run eval
            ...
        else:
            # Target busy
            ...

    # Acquire first available from a pool
    with acquire_from_pool(["mi300x-1", "mi300x-2", "mi300x-3"]) as target:
        if target:
            # Got a target, run eval
            ...
        else:
            # All targets busy
            ...
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC
from pathlib import Path


def _emit_gpu_event(event_type: str, **data: dict) -> None:
    """Emit structured GPU event to stderr as JSON.

    Events are written to stderr (not stdout) to avoid interfering with
    command output parsing. Format: JSON with newline.

    These events can be:
    1. Parsed from bash output in eval events.jsonl
    2. Piped to observability systems
    3. Aggregated for GPU utilization metrics
    """
    from datetime import datetime

    event = {
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "pid": os.getpid(),
        **data,
    }
    # Write to stderr so it doesn't interfere with stdout capture
    print(f"[GPU_EVENT] {json.dumps(event)}", file=sys.stderr, flush=True)


# Lock directory
LOCKS_DIR = Path.home() / ".wafer" / "locks"


def _ensure_locks_dir() -> None:
    """Ensure locks directory exists."""
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)


def _lock_path(target_name: str) -> Path:
    """Get path to lock file for a target."""
    return LOCKS_DIR / f"{target_name}.lock"


@contextmanager
def try_acquire_target(target_name: str) -> Iterator[bool]:
    """Try to acquire exclusive lock on a target.

    Args:
        target_name: Name of the target to lock

    Yields:
        True if lock was acquired, False if target is busy

    The lock is automatically released when the context exits,
    or if the process crashes.
    """
    _ensure_locks_dir()
    lock_file = _lock_path(target_name)

    # Open or create lock file
    fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)

    try:
        # Try non-blocking exclusive lock
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Write PID to lock file for debugging
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        acquire_time = time.time()
        _emit_gpu_event("gpu_acquire", target=target_name)
        try:
            yield True
        finally:
            # Release lock
            hold_duration_ms = (time.time() - acquire_time) * 1000
            _emit_gpu_event(
                "gpu_release",
                target=target_name,
                hold_duration_ms=round(hold_duration_ms, 1),
            )
            fcntl.flock(fd, fcntl.LOCK_UN)
    except BlockingIOError:
        # Lock is held by another process
        yield False
    finally:
        os.close(fd)


@contextmanager
def acquire_from_pool(
    target_names: list[str],
    timeout: float | None = None,
    poll_interval: float = 1.0,
) -> Iterator[str | None]:
    """Acquire first available target from a list.

    Tries each target in order, returns the first one that's available.
    If all targets are busy and timeout is set, waits and retries.

    Args:
        target_names: List of target names to try
        timeout: Max seconds to wait for a target. None = no waiting (fail immediately).
                 Use float('inf') to wait forever.
        poll_interval: Seconds between retries when waiting

    Yields:
        Name of acquired target, or None if all are busy (and timeout expired)

    Example:
        # Wait up to 5 minutes for a target
        with acquire_from_pool(["gpu-1", "gpu-2", "gpu-3"], timeout=300) as target:
            if target:
                print(f"Got {target}")
                run_eval(target)
            else:
                print("All targets busy after timeout")
    """
    _ensure_locks_dir()

    start_time = time.monotonic()

    while True:
        # Try each target in order
        for target_name in target_names:
            lock_file = _lock_path(target_name)
            fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)

            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Got the lock - write PID and yield
                os.ftruncate(fd, 0)
                os.write(fd, f"{os.getpid()}\n".encode())
                acquire_time = time.time()
                _emit_gpu_event("gpu_acquire", target=target_name, pool=target_names)
                try:
                    yield target_name
                    return  # Success - exit after context
                finally:
                    hold_duration_ms = (time.time() - acquire_time) * 1000
                    _emit_gpu_event(
                        "gpu_release",
                        target=target_name,
                        pool=target_names,
                        hold_duration_ms=round(hold_duration_ms, 1),
                    )
                    fcntl.flock(fd, fcntl.LOCK_UN)
                    os.close(fd)
            except BlockingIOError:
                # This target is busy, try next
                os.close(fd)
                continue

        # All targets busy - check if we should wait
        if timeout is None:
            # No waiting, fail immediately
            break

        elapsed = time.monotonic() - start_time
        if elapsed >= timeout:
            # Timeout expired
            break

        # Wait and retry
        remaining = timeout - elapsed
        print(f"  All targets busy, waiting... ({int(remaining)}s remaining)", file=sys.stderr)
        time.sleep(poll_interval)

    # All targets busy (timeout expired or no waiting)
    yield None


def is_target_locked(target_name: str) -> bool:
    """Check if a target is currently locked.

    Note: This is a point-in-time check - the lock status can change
    immediately after this returns.

    Args:
        target_name: Name of the target to check

    Returns:
        True if target is locked, False if available
    """
    _ensure_locks_dir()
    lock_file = _lock_path(target_name)

    if not lock_file.exists():
        return False

    fd = os.open(str(lock_file), os.O_RDONLY)
    try:
        # Try non-blocking lock
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Got it - so it wasn't locked
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    finally:
        os.close(fd)


def get_lock_holder(target_name: str) -> int | None:
    """Get PID of process holding lock on a target.

    Args:
        target_name: Name of the target

    Returns:
        PID of lock holder, or None if not locked or unknown
    """
    lock_file = _lock_path(target_name)

    if not lock_file.exists():
        return None

    try:
        content = lock_file.read_text().strip()
        return int(content)
    except (ValueError, OSError):
        return None


def list_locked_targets() -> list[str]:
    """List all currently locked targets.

    Returns:
        List of target names that are currently locked
    """
    _ensure_locks_dir()

    locked = []
    for lock_file in LOCKS_DIR.glob("*.lock"):
        target_name = lock_file.stem
        if is_target_locked(target_name):
            locked.append(target_name)

    return sorted(locked)
