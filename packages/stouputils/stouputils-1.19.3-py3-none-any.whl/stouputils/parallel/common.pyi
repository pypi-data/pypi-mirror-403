from collections.abc import Callable

CPU_COUNT: int

def nice_wrapper[T, R](args: tuple[int, Callable[[T], R], T]) -> R:
    """ Wrapper that applies nice priority then executes the function.

\tArgs:
\t\targs (tuple): Tuple containing (nice_value, func, arg)

\tReturns:
\t\tR: Result of the function execution
\t"""
def set_process_priority(nice_value: int) -> None:
    """ Set the priority of the current process.

\tArgs:
\t\tnice_value (int): Unix-style priority value (-20 to 19)
\t"""
def starmap[T, R](args: tuple[Callable[[T], R], list[T]]) -> R:
    """ Private function to use starmap using args[0](\\*args[1])

\tArgs:
\t\targs (tuple): Tuple containing the function and the arguments list to pass to the function
\tReturns:
\t\tobject: Result of the function execution
\t"""
def delayed_call[T, R](args: tuple[Callable[[T], R], float, T]) -> R:
    """ Private function to apply delay before calling the target function

\tArgs:
\t\targs (tuple): Tuple containing the function, delay in seconds, and the argument to pass to the function
\tReturns:
\t\tobject: Result of the function execution
\t"""
def handle_parameters[T, R](func: Callable[[T], R] | list[Callable[[T], R]], args: list[T], use_starmap: bool, delay_first_calls: float, max_workers: int, desc: str, color: str) -> tuple[str, Callable[[T], R], list[T]]:
    ''' Private function to handle the parameters for multiprocessing or multithreading functions

\tArgs:
\t\tfunc\t\t\t\t(Callable | list[Callable]):\tFunction to execute, or list of functions (one per argument)
\t\targs\t\t\t\t(list):\t\t\t\tList of arguments to pass to the function(s)
\t\tuse_starmap\t\t\t(bool):\t\t\t\tWhether to use starmap or not (Defaults to False):
\t\t\tTrue means the function will be called like func(\\*args[i]) instead of func(args[i])
\t\tdelay_first_calls\t(int):\t\t\t\tApply i*delay_first_calls seconds delay to the first "max_workers" calls.
\t\t\tFor instance, the first process will be delayed by 0 seconds, the second by 1 second, etc. (Defaults to 0):
\t\t\tThis can be useful to avoid functions being called in the same second.
\t\tmax_workers\t\t\t(int):\t\t\t\tNumber of workers to use
\t\tdesc\t\t\t\t(str):\t\t\t\tDescription of the function execution displayed in the progress bar
\t\tcolor\t\t\t\t(str):\t\t\t\tColor of the progress bar

\tReturns:
\t\ttuple[str, Callable[[T], R], list[T]]:\tTuple containing the description, function, and arguments
\t'''
