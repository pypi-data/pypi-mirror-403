from ..typing import JsonDict as JsonDict
from .capturer import CaptureOutput as CaptureOutput
from _typeshed import Incomplete
from collections.abc import Callable as Callable
from typing import Any

class RemoteSubprocessError(RuntimeError):
    """ Raised in the parent when the child raised an exception - contains the child's formatted traceback. """
    remote_type: Incomplete
    remote_repr: Incomplete
    remote_traceback: Incomplete
    def __init__(self, exc_type: str, exc_repr: str, traceback_str: str) -> None: ...

def run_in_subprocess[R](func: Callable[..., R], *args: Any, timeout: float | None = None, no_join: bool = False, capture_output: bool = False, **kwargs: Any) -> R:
    ''' Execute a function in a subprocess with positional and keyword arguments.

\tThis is useful when you need to run a function in isolation to avoid memory leaks,
\tresource conflicts, or to ensure a clean execution environment. The subprocess will
\tbe created, run the function with the provided arguments, and return the result.

\tArgs:
\t\tfunc           (Callable):     The function to execute in a subprocess.
\t\t\t(SHOULD BE A TOP-LEVEL FUNCTION TO BE PICKLABLE)
\t\t*args          (Any):          Positional arguments to pass to the function.
\t\ttimeout        (float | None): Maximum time in seconds to wait for the subprocess.
\t\t\tIf None, wait indefinitely. If the subprocess exceeds this time, it will be terminated.
\t\tno_join        (bool):         If True, do not wait for the subprocess to finish (fire-and-forget).
\t\tcapture_output (bool):         If True, capture the subprocess\' stdout/stderr and relay it
\t\t\tin real time to the parent\'s stdout. This enables seeing print() output
\t\t\tfrom the subprocess in the main process.
\t\t**kwargs       (Any):          Keyword arguments to pass to the function.

\tReturns:
\t\tR: The return value of the function.

\tRaises:
\t\tRemoteSubprocessError: If the child raised an exception - contains the child\'s formatted traceback.
\t\tRuntimeError: If the subprocess exits with a non-zero exit code or did not return a result.
\t\tTimeoutError: If the subprocess exceeds the specified timeout.

\tExamples:
\t\t.. code-block:: python

\t\t\t> # Simple function execution
\t\t\t> run_in_subprocess(doctest_square, 5)
\t\t\t25

\t\t\t> # Function with multiple arguments
\t\t\t> def add(a: int, b: int) -> int:
\t\t\t.     return a + b
\t\t\t> run_in_subprocess(add, 10, 20)
\t\t\t30

\t\t\t> # Function with keyword arguments
\t\t\t> def greet(name: str, greeting: str = "Hello") -> str:
\t\t\t.     return f"{greeting}, {name}!"
\t\t\t> run_in_subprocess(greet, "World", greeting="Hi")
\t\t\t\'Hi, World!\'

\t\t\t> # With timeout to prevent hanging
\t\t\t> run_in_subprocess(some_gpu_func, data, timeout=300.0)
\t'''
def _subprocess_wrapper[R](result_queue: Any, func: Callable[..., R], args: tuple[Any, ...], kwargs: dict[str, Any], _capturer: CaptureOutput | None = None) -> None:
    """ Wrapper function to execute the target function and store the result in the queue.

\tMust be at module level to be pickable on Windows (spawn context).

\tArgs:
\t\tresult_queue (multiprocessing.Queue | None):  Queue to store the result or exception (None if detached).
\t\tfunc         (Callable):                      The target function to execute.
\t\targs         (tuple):                         Positional arguments for the function.
\t\tkwargs       (dict):                          Keyword arguments for the function.
\t\t_capturer    (CaptureOutput | None):          Optional CaptureOutput instance for stdout capture.
\t"""
