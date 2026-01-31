from ..io import safe_close as safe_close
from _typeshed import Incomplete
from typing import Any, IO

class PipeWriter:
    """ A writer that sends data to a multiprocessing Connection. """
    conn: Any
    encoding: str
    errors: str
    def __init__(self, conn: Any, encoding: str, errors: str) -> None: ...
    def write(self, data: str) -> int: ...
    def flush(self) -> None: ...

class CaptureOutput:
    """ Utility to capture stdout/stderr from a subprocess and relay it to the parent's stdout.

\tThe class creates an os.pipe(), marks fds as inheritable (for spawn method),
\tprovides methods to start a listener thread that reads from the pipe and writes
\tto the main process's sys.stdout/sys.stderr, and to close/join the listener.
\t"""
    encoding: str
    errors: str
    chunk_size: int
    read_fd: Incomplete
    write_fd: Incomplete
    _thread: threading.Thread | None
    _reader_file: IO[Any] | None
    def __init__(self, encoding: str = 'utf-8', errors: str = 'replace', chunk_size: int = 1024) -> None: ...
    def __repr__(self) -> str: ...
    def __getstate__(self) -> dict[str, Any]: ...
    def redirect(self) -> None:
        """ Redirect sys.stdout and sys.stderr to the pipe's write end. """
    def parent_close_write(self) -> None:
        """ Close the parent's copy of the write end; the child's copy remains. """
    def start_listener(self) -> None:
        """ Start a daemon thread that forwards data from the pipe to sys.stdout/sys.stderr. """
    def join_listener(self, timeout: float | None = None) -> None:
        """ Wait for the listener thread to finish (until EOF). """
