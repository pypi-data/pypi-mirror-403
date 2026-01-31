import redis
from ..decorators import abstract as abstract

class BaseTicketQueue:
    """ Base API for ticket queues. """
    @abstract
    def register(self) -> tuple[int, str]: ...
    @abstract
    def is_head(self, ticket: int) -> bool: ...
    @abstract
    def remove(self, member: str) -> None: ...
    @abstract
    def cleanup_stale(self) -> None: ...
    @abstract
    def is_empty(self) -> bool:
        ''' Return True if the queue currently has no waiting members.

        Implementations should consider the concrete storage details (e.g. on
        filesystem the "seq" file is not considered a queue member).
        '''
    @abstract
    def maybe_cleanup(self) -> None:
        """ Attempt to remove any on-disk or remote artifacts when the queue is empty.

        This should be a best-effort no-op if other clients are concurrently
        active. Implementations should handle errors internally and not raise.
        """

class FileTicketQueue(BaseTicketQueue):
    ''' File-system backed ticket queue.

    Tickets are assigned using a small ``seq`` file protected by an exclusive
    lock (via ``fcntl`` on POSIX). Each waiter creates a ticket file named
    ``{ticket:020d}.{pid}.{uuid}`` in the queue directory. The head of the
    sorted directory listing is considered the current owner.

    Examples:
        >>> # Basic filesystem queue behaviour and cleanup
        >>> import tempfile, os, time
        >>> tmp = tempfile.mkdtemp()
        >>> qd = tmp + "/q"
        >>> q = FileTicketQueue(qd, stale_timeout=0.01)
        >>> t1, m1 = q.register()
        >>> t2, m2 = q.register()
        >>> q.is_head(t1)
        True
        >>> q.remove(m1)
        >>> q.is_head(t2)
        True
        >>> # Make the remaining ticket appear stale and cleanup
        >>> p = os.path.join(qd, m2)
        >>> os.utime(p, (0, 0))
        >>> q.cleanup_stale()
        >>> q.is_empty()
        True
        >>> q.maybe_cleanup()
        >>> os.path.exists(qd)
        False
    '''
    queue_dir: str
    stale_timeout: float | None
    def __init__(self, queue_dir: str, stale_timeout: float | None = None) -> None: ...
    def _get_ticket(self) -> int: ...
    def register(self) -> tuple[int, str]: ...
    def is_head(self, ticket: int) -> bool: ...
    def remove(self, member: str) -> None: ...
    def cleanup_stale(self) -> None:
        """ Remove stale head ticket if its mtime exceeds the stale timeout. """
    def is_empty(self) -> bool:
        """Return True if the queue directory contains no ticket files.

        The sequence file ``seq`` is ignored when determining emptiness.
        """
    def maybe_cleanup(self) -> None:
        """ Try to remove sequence file and queue dir if the queue is empty.

        This is a best-effort operation: if other clients are active or a
        race occurs, the function simply returns without raising.
        """

class RedisTicketQueue(BaseTicketQueue):
    ''' Redis-backed ticket queue using INCR + ZADD.

    Member format: ``{ticket}:{token}:{ts_ms}`` where ``ts_ms`` is the
    insertion timestamp in milliseconds. The ZSET score is the ticket number
    which provides ordering. This class performs stale head cleanup based on
    the provided stale timeout.

    Examples:
        >>> # Redis queue examples; run only on non-Windows environments
        >>> def _redis_ticket_queue_doctest():
        ...     import time, redis
        ...     client = redis.Redis()
        ...     name = "doctest:rq"
        ...     # Ensure clean start
        ...     _ = client.delete(f"{name}:queue")
        ...     _ = client.delete(f"{name}:seq")
        ...     q = RedisTicketQueue(name, client, stale_timeout=0.01)
        ...     t1, m1 = q.register()
        ...     t2, m2 = q.register()
        ...     q.is_head(t1)
        ...     True
        ...     q.remove(m1)
        ...     q.is_head(t2)
        ...     True
        ...     q.remove(m2)
        ...     q.maybe_cleanup()
        ...     print(client.exists(f"{name}:queue") == 0 and client.exists(f"{name}:seq") == 0)
        >>> import os
        >>> if os.name != \'nt\':
        ...     _redis_ticket_queue_doctest()
        ... else:
        ...     print("True")
        True
    '''
    name: str
    client: redis.Redis | None
    stale_timeout: float | None
    def __init__(self, name: str, client: redis.Redis | None = None, stale_timeout: float | None = None) -> None: ...
    def ensure_client(self) -> redis.Redis: ...
    def register(self) -> tuple[int, str]: ...
    def is_head(self, ticket: int) -> bool: ...
    def remove(self, member: str) -> None: ...
    def cleanup_stale(self) -> None: ...
    def is_empty(self) -> bool: ...
    def maybe_cleanup(self) -> None:
        """Attempt to remove Redis keys used by the queue when it is empty.

        This is best effort: if concurrent clients are active the operation may
        be a no-op.
        """
