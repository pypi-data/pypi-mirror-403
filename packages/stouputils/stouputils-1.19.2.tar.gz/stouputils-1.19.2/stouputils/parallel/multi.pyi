from ..ctx import SetMPStartMethod as SetMPStartMethod
from ..print import BAR_FORMAT as BAR_FORMAT, MAGENTA as MAGENTA
from .capturer import CaptureOutput as CaptureOutput
from .common import CPU_COUNT as CPU_COUNT, handle_parameters as handle_parameters, nice_wrapper as nice_wrapper
from collections.abc import Callable as Callable, Iterable
from typing import Any

def doctest_square(x: int) -> int: ...
def doctest_slow(x: int) -> int: ...
def multiprocessing[T, R](func: Callable[..., R] | list[Callable[..., R]], args: Iterable[T], use_starmap: bool = False, chunksize: int = 1, desc: str = '', max_workers: int | float = ..., capture_output: bool = False, delay_first_calls: float = 0, nice: int | None = None, color: str = ..., bar_format: str = ..., ascii: bool = False, smooth_tqdm: bool = True, **tqdm_kwargs: Any) -> list[R]:
    ''' Method to execute a function in parallel using multiprocessing

\t- For CPU-bound operations where the GIL (Global Interpreter Lock) is a bottleneck.
\t- When the task can be divided into smaller, independent sub-tasks that can be executed concurrently.
\t- For computationally intensive tasks like scientific simulations, data analysis, or machine learning workloads.

\tArgs:
\t\tfunc\t\t\t\t(Callable | list[Callable]):\tFunction to execute, or list of functions (one per argument)
\t\targs\t\t\t\t(Iterable):\t\t\tIterable of arguments to pass to the function(s)
\t\tuse_starmap\t\t\t(bool):\t\t\t\tWhether to use starmap or not (Defaults to False):
\t\t\tTrue means the function will be called like func(\\*args[i]) instead of func(args[i])
\t\tchunksize\t\t\t(int):\t\t\t\tNumber of arguments to process at a time
\t\t\t(Defaults to 1 for proper progress bar display)
\t\tdesc\t\t\t\t(str):\t\t\t\tDescription displayed in the progress bar
\t\t\t(if not provided no progress bar will be displayed)
\t\tmax_workers\t\t\t(int | float):\t\tNumber of workers to use (Defaults to CPU_COUNT), -1 means CPU_COUNT.
\t\t\tIf float between 0 and 1, it\'s treated as a percentage of CPU_COUNT.
\t\t\tIf negative float between -1 and 0, it\'s treated as a percentage of len(args).
\t\tcapture_output\t\t(bool):\t\t\t\tWhether to capture stdout/stderr from the worker processes (Defaults to True)
\t\tdelay_first_calls\t(float):\t\t\tApply i*delay_first_calls seconds delay to the first "max_workers" calls.
\t\t\tFor instance, the first process will be delayed by 0 seconds, the second by 1 second, etc.
\t\t\t(Defaults to 0): This can be useful to avoid functions being called in the same second.
\t\tnice\t\t\t\t(int | None):\t\tAdjust the priority of worker processes (Defaults to None).
\t\t\tUse Unix-style values: -20 (highest priority) to 19 (lowest priority).
\t\t\tPositive values reduce priority, negative values increase it.
\t\t\tAutomatically converted to appropriate priority class on Windows.
\t\t\tIf None, no priority adjustment is made.
\t\tcolor\t\t\t\t(str):\t\t\t\tColor of the progress bar (Defaults to MAGENTA)
\t\tbar_format\t\t\t(str):\t\t\t\tFormat of the progress bar (Defaults to BAR_FORMAT)
\t\tascii\t\t\t\t(bool):\t\t\t\tWhether to use ASCII or Unicode characters for the progress bar
\t\tsmooth_tqdm\t\t\t(bool):\t\t\t\tWhether to enable smooth progress bar updates by setting miniters and mininterval (Defaults to True)
\t\t**tqdm_kwargs\t\t(Any):\t\t\t\tAdditional keyword arguments to pass to tqdm

\tReturns:
\t\tlist[object]:\tResults of the function execution

\tExamples:
\t\t.. code-block:: python

\t\t\t> multiprocessing(doctest_square, args=[1, 2, 3])
\t\t\t[1, 4, 9]

\t\t\t> multiprocessing(int.__mul__, [(1,2), (3,4), (5,6)], use_starmap=True)
\t\t\t[2, 12, 30]

\t\t\t> # Using a list of functions (one per argument)
\t\t\t> multiprocessing([doctest_square, doctest_square, doctest_square], [1, 2, 3])
\t\t\t[1, 4, 9]

\t\t\t> # Will process in parallel with progress bar
\t\t\t> multiprocessing(doctest_slow, range(10), desc="Processing")
\t\t\t[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

\t\t\t> # Will process in parallel with progress bar and delay the first threads
\t\t\t> multiprocessing(
\t\t\t.     doctest_slow,
\t\t\t.     range(10),
\t\t\t.     desc="Processing with delay",
\t\t\t.     max_workers=2,
\t\t\t.     delay_first_calls=0.6
\t\t\t. )
\t\t\t[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
\t'''
def multithreading[T, R](func: Callable[..., R] | list[Callable[..., R]], args: Iterable[T], use_starmap: bool = False, desc: str = '', max_workers: int | float = ..., delay_first_calls: float = 0, color: str = ..., bar_format: str = ..., ascii: bool = False, smooth_tqdm: bool = True, **tqdm_kwargs: Any) -> list[R]:
    ''' Method to execute a function in parallel using multithreading, you should use it:

\t- For I/O-bound operations where the GIL is not a bottleneck, such as network requests or disk operations.
\t- When the task involves waiting for external resources, such as network responses or user input.
\t- For operations that involve a lot of waiting, such as GUI event handling or handling user input.

\tArgs:
\t\tfunc\t\t\t\t(Callable | list[Callable]):\tFunction to execute, or list of functions (one per argument)
\t\targs\t\t\t\t(Iterable):\t\t\tIterable of arguments to pass to the function(s)
\t\tuse_starmap\t\t\t(bool):\t\t\t\tWhether to use starmap or not (Defaults to False):
\t\t\tTrue means the function will be called like func(\\*args[i]) instead of func(args[i])
\t\tdesc\t\t\t\t(str):\t\t\t\tDescription displayed in the progress bar
\t\t\t(if not provided no progress bar will be displayed)
\t\tmax_workers\t\t\t(int | float):\t\tNumber of workers to use (Defaults to CPU_COUNT), -1 means CPU_COUNT.
\t\t\tIf float between 0 and 1, it\'s treated as a percentage of CPU_COUNT.
\t\t\tIf negative float between -1 and 0, it\'s treated as a percentage of len(args).
\t\tdelay_first_calls\t(float):\t\t\tApply i*delay_first_calls seconds delay to the first "max_workers" calls.
\t\t\tFor instance with value to 1, the first thread will be delayed by 0 seconds, the second by 1 second, etc.
\t\t\t(Defaults to 0): This can be useful to avoid functions being called in the same second.
\t\tcolor\t\t\t\t(str):\t\t\t\tColor of the progress bar (Defaults to MAGENTA)
\t\tbar_format\t\t\t(str):\t\t\t\tFormat of the progress bar (Defaults to BAR_FORMAT)
\t\tascii\t\t\t\t(bool):\t\t\t\tWhether to use ASCII or Unicode characters for the progress bar
\t\tsmooth_tqdm\t\t\t(bool):\t\t\t\tWhether to enable smooth progress bar updates by setting miniters and mininterval (Defaults to True)
\t\t**tqdm_kwargs\t\t(Any):\t\t\t\tAdditional keyword arguments to pass to tqdm

\tReturns:
\t\tlist[object]:\tResults of the function execution

\tExamples:
\t\t.. code-block:: python

\t\t\t> multithreading(doctest_square, args=[1, 2, 3])
\t\t\t[1, 4, 9]

\t\t\t> multithreading(int.__mul__, [(1,2), (3,4), (5,6)], use_starmap=True)
\t\t\t[2, 12, 30]

\t\t\t> # Using a list of functions (one per argument)
\t\t\t> multithreading([doctest_square, doctest_square, doctest_square], [1, 2, 3])
\t\t\t[1, 4, 9]

\t\t\t> # Will process in parallel with progress bar
\t\t\t> multithreading(doctest_slow, range(10), desc="Threading")
\t\t\t[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

\t\t\t> # Will process in parallel with progress bar and delay the first threads
\t\t\t> multithreading(
\t\t\t.     doctest_slow,
\t\t\t.     range(10),
\t\t\t.     desc="Threading with delay",
\t\t\t.     max_workers=2,
\t\t\t.     delay_first_calls=0.6
\t\t\t. )
\t\t\t[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
\t'''
def capture_subprocess_output[T, R](args: tuple[CaptureOutput, Callable[[T], R], T]) -> R:
    """ Wrapper function to execute the target function in a subprocess with optional output capture.

\tArgs:
\t\ttuple[CaptureOutput,Callable,T]: Tuple containing:
\t\t\tCaptureOutput: Capturer object to redirect stdout/stderr
\t\t\tCallable: Target function to execute
\t\t\tT: Argument to pass to the target function
\t"""
