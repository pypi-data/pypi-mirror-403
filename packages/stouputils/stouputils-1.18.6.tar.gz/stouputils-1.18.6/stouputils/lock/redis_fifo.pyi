import redis
from .shared import LockError as LockError, LockTimeoutError as LockTimeoutError
from _typeshed import Incomplete
from contextlib import AbstractContextManager
from typing import Any

class RedisLockFifo(AbstractContextManager['RedisLockFifo']):
    ''' A Redis-backed inter-process lock (requires `redis`).

    This lock provides optional Fifo fairness (enabled by default) and is
    implemented using atomic Redis primitives. Acquisition of the underlying
    lock uses an owner token and `SET NX` (with optional PX expiry when a
    timeout/TTL is specified). When Fifo is enabled the implementation uses
    a small ticket queue using `INCR` + `ZADD` and only the queue head attempts
    to `SET NX`. Release uses an atomic Lua script to ensure only the token
    owner can delete the lock key.

    Notes:
      - The lock stores a locally-generated random token; releasing without the
        correct token has no effect on the remote key.
      - When Fifo is enabled, queue entries are removed when the client acquires
        the lock; stale queue entries (from crashed clients) are removed lazily
        when their age exceeds ``fifo_stale_timeout`` (defaults to ``timeout`` if
        ``None``).
      - This class raises ``ImportError`` if the ``redis`` package is not
        installed and raises ``LockTimeoutError`` / ``LockError`` for runtime
        acquisition errors.

    Args:
        name               (str):           Redis key name used for the lock.
        redis_client       (redis.Redis | None): Optional Redis client. A client is created lazily if not provided.
        timeout            (float | None):  Maximum time to wait for the lock and (when provided) the lock TTL used by ``SET PX`` in seconds. ``None`` means block indefinitely and no automatic expiry.
        blocking           (bool):          Whether to block until acquired (subject to ``timeout``).
        check_interval     (float):         Poll interval while waiting for the lock, in seconds.
        fifo               (bool):          Whether to enforce Fifo ordering using a ZSET queue (default: True).
        fifo_stale_timeout (float | None):  Seconds after which a queue entry is considered stale; if ``None`` the lock\'s ``timeout`` value will be used; if both are ``None``, no stale cleanup is performed.

    Raises:
        ImportError: If the ``redis`` package is not installed.
        LockTimeoutError: If the lock cannot be acquired within ``timeout``.
        LockError: On unexpected redis errors.

    Examples:
        >>> # Redis-backed examples; run only on non-Windows environments
        >>> def _redis_doctest():
        ...     import redis, time
        ...     client = redis.Redis()
        ...
        ...     # Simple usage (assumes redis is available in the test environment)
        ...     with RedisLockFifo(\'test:lock\', timeout=1):
        ...         pass
        ...
        ...     # Non-Fifo usage example
        ...     with RedisLockFifo(\'test:lock\', fifo=False, timeout=1):
        ...         pass
        ...
        ...     # Fifo stale-ticket behaviour (requires a local redis server)
        ...     # Inject a stale head entry
        ...     name = \'doctest:lock:stale\'
        ...     _ = client.delete(f"{name}:queue")
        ...     _ = client.delete(f"{name}:seq")
        ...     _ = client.delete(name)
        ...     old_ts = int((time.time() - 10) * 1000)
        ...     _ = client.zadd(f"{name}:queue", {f"1:stale:{old_ts}": 1})
        ...     # Now acquire with small stale timeout which should remove head then succeed
        ...     with RedisLockFifo(name, fifo=True, fifo_stale_timeout=0.01, timeout=1):
        ...         print(\'acquired\')
        ...     _ = client.delete(f"{name}:queue")
        ...     _ = client.delete(f"{name}:seq")
        ...     _ = client.delete(name)
        ...     # After using the lock, the queue keys should be removed when empty
        ...     with RedisLockFifo(name, timeout=1):
        ...         pass
        ...     print(client.exists(f"{name}:queue") == 0 and client.exists(f"{name}:seq") == 0)
        ...
        ...     # Non-Fifo acquisition should not create queue keys
        ...     name2 = \'doctest:lock:nonfifo\'
        ...     _ = client.delete(f"{name2}:queue"); _ = client.delete(f"{name2}:seq")
        ...     with RedisLockFifo(name2, fifo=False, timeout=1):
        ...         pass
        ...     print(client.exists(f"{name2}:queue") == 0 and client.exists(f"{name2}:seq") == 0)
        ...
        >>> import os
        >>> if os.name != \'nt\':
        ...     _redis_doctest()
        ... else:
        ...     print("acquired\\nTrue\\nTrue")
        acquired
        True
        True
    '''
    RELEASE_SCRIPT: str
    name: str
    client: redis.Redis | None
    timeout: float | None
    blocking: bool
    check_interval: float
    fifo: bool
    fifo_stale_timeout: float | None
    token: str | None
    queue_member: str | None
    queue: Incomplete
    def __init__(self, name: str, redis_client: redis.Redis | None = None, timeout: float | None = None, blocking: bool = True, check_interval: float = 0.05, fifo: bool = True, fifo_stale_timeout: float | None = None) -> None: ...
    def ensure_client(self) -> redis.Redis:
        """ Ensure a ``redis.Redis`` client is available (lazy creation). """
    def _cleanup_stalequeue(self) -> None:
        """ Remove a stale head member from the queue if it exceeds the stale timeout. """
    def acquire(self, timeout: float | None = None, blocking: bool | None = None, check_interval: float | None = None) -> None:
        """ Acquire the Redis lock.

        When Fifo is enabled (default), this function obtains a ticket via INCR
        and registers it in a ZSET. The client waits until its ticket is the
        head of the queue and then attempts to SET NX the lock key.
        """
    def release(self) -> None:
        """ Release the lock if currently owned by this instance.

        Uses an atomic Lua script to check that the stored token matches the
        key value and deletes it only when owned. Additionally removes any
        lingering queue entry for this client.
        """
    def __enter__(self) -> RedisLockFifo: ...
    def __exit__(self, exc_type: type | None, exc: BaseException | None, tb: Any | None) -> None: ...
