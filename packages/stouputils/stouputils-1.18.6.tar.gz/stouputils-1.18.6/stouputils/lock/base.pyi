from .shared import LockError as LockError, LockTimeoutError as LockTimeoutError, resolve_path as resolve_path
from _typeshed import Incomplete
from contextlib import AbstractContextManager
from typing import Any, IO

def _lock_fd(fd: int, blocking: bool, timeout: float | None) -> None:
    """Try to acquire an exclusive lock on an open file descriptor.

    This helper attempts POSIX `fcntl` first, then Windows `msvcrt`.
    It raises BlockingIOError when the lock is busy, ImportError if neither
    backend is available, or OSError for unexpected errors.
    """
def _unlock_fd(fd: int | None) -> None:
    """Unlock an open file descriptor using the available backend."""
def _remove_file_if_unlocked(path: str) -> None:
    """Attempt to remove a file only if we can confirm nobody holds the lock.

    Uses a non-blocking lock test via fcntl or msvcrt. This is best-effort and
    will not raise on failure.
    """
def _worker(lp: str, op: str, idx: int) -> None:
    """ Module-level helper used by doctests as a multiprocessing target. """
def _hold(path: str) -> None:
    """ Module-level helper used by doctests as a multiprocessing target.

    This creates a small readiness marker file while holding the lock so
    doctests can reliably detect when the child process has acquired it
    (useful on Windows spawn semantics).
    """

class LockFifo(AbstractContextManager['LockFifo']):
    ''' A simple cross-platform inter-process lock backed by a file.

    This implementation supports optional Fifo ordering via a small ticket queue
    stored alongside the lock file. Fifo is enabled by default to avoid
    starvation. Fifo behaviour is implemented with a small sequence file and
    per-ticket files in ``<lockpath>.queue/``. On platforms without fcntl the
    implementation falls back to a timestamp-based ticket.

    Args:
        name               (str):           Lock filename or path. If a simple name is given,
            it is created in the system temporary directory.
        timeout            (float | None):  Seconds to wait for the lock. ``None`` means block indefinitely.
        blocking           (bool):          Whether to block until acquired (subject to ``timeout``).
        check_interval     (float):         Interval between lock attempts, in seconds.
        fifo               (bool):          Whether to enforce Fifo ordering (default: True).
        fifo_stale_timeout (float | None):  Seconds after which a ticket is considered stale; if ``None`` the lock\'s ``timeout`` value will be used.

    Raises:
        LockTimeoutError: If the lock could not be acquired within the timeout (LockError & TimeoutError subclass)
        LockError: On unexpected locking errors. (RunTimeError subclass)

    Examples:
        >>> # Basic context-manager usage (Fifo enabled by default)
        >>> with LockFifo("my.lock", timeout=1):
        ...     pass

        >>> # Explicit acquire/release
        >>> lock = LockFifo("my.lock", timeout=1)
        >>> lock.acquire()
        >>> lock.release()

        >>> # Doctest: simple multi-process Fifo check (fast and deterministic)
        >>> import tempfile, multiprocessing, time
        >>> tmpdir = tempfile.mkdtemp()
        >>> lockpath = tmpdir + "/t.lock"
        >>> out = tmpdir + "/out.txt"
        >>> # Worker function is module-level: `_worker`
        >>> # (Defined at module scope so it can be pickled on Windows)
        >>> procs = []
        >>> for i in range(3):
        ...     p = multiprocessing.Process(target=_worker, args=(lockpath, out, i))
        ...     p.start(); procs.append(p); time.sleep(0.05)
        >>> for p in procs: p.join(1)
        >>> with open(out) as f: print([int(x) for x in f.read().splitlines()])
        [0, 1, 2]

        >>> # Doctest: cleanup of artifacts on close
        >>> import tempfile, os
        >>> tmp = tempfile.mkdtemp()
        >>> p = tmp + "/tlock"
        >>> l = LockFifo(p, timeout=1)
        >>> l.acquire(); l.release(); l.close()
        >>> import os
        >>> # The lock file should not remain on any platform after close()
        >>> assert not os.path.exists(p)
        >>> assert not os.path.exists(p + ".queue")

        >>> # Non-Fifo fast-path should not create a queue directory
        >>> tmp2 = tempfile.mkdtemp()
        >>> p2 = tmp2 + "/tlock2"
        >>> l2 = LockFifo(p2, fifo=False, timeout=1)
        >>> l2.acquire(); l2.release(); l2.close()
        >>> os.path.exists(p2 + ".queue")
        False

        >>> # Attempting a non-blocking acquire while another process holds the lock raises LockTimeoutError
        >>> import multiprocessing, time
        >>> # Hold function is module-level: `_hold`
        >>> # (Defined at module scope so it can be pickled on Windows)
        >>> p = multiprocessing.Process(target=_hold, args=(p2,))
        >>> p.start()
        >>> import time, os
        >>> deadline = time.time() + 1.0
        >>> while not os.path.exists(p2 + ".held") and time.time() < deadline:
        ...     time.sleep(0.01)
        >>> l3 = LockFifo(p2, timeout=1)
        >>> try:
        ...     l3.acquire(blocking=False)
        ... except LockTimeoutError:
        ...     print("timeout")
        ... finally:
        ...     p.terminate(); p.join()
        timeout
    '''
    path: str
    timeout: float | None
    blocking: bool
    check_interval: float
    file: IO[bytes] | None
    fd: int | None
    is_locked: bool
    fifo: bool
    fifo_stale_timeout: float | None
    queue_dir: str
    queue: Incomplete
    def __init__(self, name: str, timeout: float | None = None, blocking: bool = True, check_interval: float = 0.05, fifo: bool = True, fifo_stale_timeout: float | None = None) -> None: ...
    def _get_ticket(self) -> int:
        """ Obtain a monotonically increasing ticket number.

        Uses a small sequence file protected by an exclusive lock (fcntl) when
        available. When fcntl is not available, falls back to a timestamp-based
        ticket (still monotonic enough on typical systems).
        """
    def _cleanup_stale_tickets(self) -> None:
        """ Remove stale ticket files from the queue directory.

        A ticket is considered stale when its mtime is older than the effective
        stale timeout. If ``self.fifo_stale_timeout`` is ``None``, the lock's
        ``timeout`` value is used; if that is also ``None``, no cleanup is
        performed.
        """
    def perform_lock(self, blocking: bool, timeout: float | None, check_interval: float) -> None:
        """ Core platform-specific lock acquisition. This contains the original
        flock-based implementation and is used both by Fifo and non-Fifo
        paths.
        """
    def acquire(self, timeout: float | None = None, blocking: bool | None = None, check_interval: float | None = None) -> None:
        """ Acquire the lock, optionally using Fifo ordering.

        When Fifo is enabled (default), a ticket file is created and the caller
        waits until its ticket becomes head of the queue before attempting the
        actual underlying lock. This avoids starvation by ensuring waiters are
        served in arrival order.
        """
    def release(self) -> None:
        """ Release the lock. """
    def __enter__(self) -> LockFifo: ...
    def __exit__(self, exc_type: type | None, exc: BaseException | None, tb: Any | None) -> None: ...
    def close(self) -> None:
        """ Release and close underlying file descriptor.

        Also attempts best-effort cleanup of queue artifacts and the lock file
        itself when it is safe to do so (no waiting clients and the lock is not
        held). This avoids leaving behind ``<lock>.queue/`` and ``<lock>``
        files when they are no longer in use.
        """
    def __del__(self) -> None: ...
    def __repr__(self) -> str: ...
