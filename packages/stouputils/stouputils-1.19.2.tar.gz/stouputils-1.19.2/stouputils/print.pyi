from collections.abc import Callable as Callable, Iterable, Iterator
from typing import Any, IO, TextIO

RESET: str
RED: str
GREEN: str
YELLOW: str
BLUE: str
MAGENTA: str
CYAN: str
LINE_UP: str
BOLD: str
BAR_FORMAT: str
previous_args_kwards: tuple[Any, Any]
nb_values: int
import_time: float

def colored_for_loop[T](iterable: Iterable[T], desc: str = 'Processing', color: str = ..., bar_format: str = ..., ascii: bool = False, smooth_tqdm: bool = True, **kwargs: Any) -> Iterator[T]:
    ''' Function to iterate over a list with a colored TQDM progress bar like the other functions in this module.

\tArgs:
\t\titerable\t(Iterable):\t\t\tList to iterate over
\t\tdesc\t\t(str):\t\t\t\tDescription of the function execution displayed in the progress bar
\t\tcolor\t\t(str):\t\t\t\tColor of the progress bar (Defaults to MAGENTA)
\t\tbar_format\t(str):\t\t\t\tFormat of the progress bar (Defaults to BAR_FORMAT)
\t\tascii\t\t(bool):\t\t\t\tWhether to use ASCII or Unicode characters for the progress bar (Defaults to False)
\t\tsmooth_tqdm\t(bool):\t\t\t\tWhether to enable smooth progress bar updates by setting miniters=1 and mininterval=0.0 (Defaults to True)
\t\t**kwargs:\t\t\t\t\t\tAdditional arguments to pass to the TQDM progress bar

\tYields:
\t\tT: Each item of the iterable

\tExamples:
\t\t>>> for i in colored_for_loop(range(10), desc="Time sleeping loop"):
\t\t...     time.sleep(0.01)
\t\t>>> # Time sleeping loop: 100%|██████████████████| 10/10 [ 95.72it/s, 00:00<00:00]
\t'''
def format_colored(*values: Any) -> str:
    ''' Format text with Python 3.14 style colored formatting.

\tDynamically colors text by analyzing each word:
\t- File paths in magenta
\t- Numbers in magenta
\t- Function names (built-in and callable objects) in magenta
\t- Exception names in bold magenta

\tArgs:
\t\tvalues\t(Any):\tValues to format (like the print function)

\tReturns:
\t\tstr: The formatted text with ANSI color codes

\tExamples:
\t\t>>> # Test function names with parentheses
\t\t>>> result = format_colored("Call print() with 42 items")
\t\t>>> result.count(MAGENTA)  # print and 42
\t\t2

\t\t>>> # Test function names without parentheses
\t\t>>> result = format_colored("Use len and sum functions")
\t\t>>> result.count(MAGENTA)  # len and sum
\t\t2

\t\t>>> # Test exceptions (bold magenta)
\t\t>>> result = format_colored("Got ValueError when parsing")
\t\t>>> result.count(MAGENTA), result.count(BOLD)  # ValueError in bold magenta
\t\t(1, 1)

\t\t>>> # Test file paths
\t\t>>> result = format_colored("Processing ./data.csv file")
\t\t>>> result.count(MAGENTA)  # ./data.csv
\t\t1

\t\t>>> # Test file paths with quotes
\t\t>>> result = format_colored(\'File "/path/to/script.py" line 42\')
\t\t>>> result.count(MAGENTA)  # /path/to/script.py and 42
\t\t2

\t\t>>> # Test numbers
\t\t>>> result = format_colored("Found 100 items and 3.14 value, 3.0e+10 is big")
\t\t>>> result.count(MAGENTA)  # 100 and 3.14
\t\t3

\t\t>>> # Test mixed content
\t\t>>> result = format_colored("Call sum() got IndexError at line 256 in utils.py")
\t\t>>> result.count(MAGENTA)  # sum, IndexError (bold), and 256
\t\t3
\t\t>>> result.count(BOLD)  # IndexError is bold
\t\t1

\t\t>>> # Test keywords always colored
\t\t>>> result = format_colored("Check class dtype type")
\t\t>>> result.count(MAGENTA)  # class, dtype, type
\t\t3

\t\t>>> # Test plain text (no coloring)
\t\t>>> result = format_colored("This is plain text")
\t\t>>> result.count(MAGENTA) == 0 and result == "This is plain text"
\t\tTrue

\t\t>>> # Affix punctuation should not be colored (assert exact coloring, punctuation uncolored)
\t\t>>> result = format_colored("<class")
\t\t>>> result == "<" + MAGENTA + "class" + RESET
\t\tTrue
\t\t>>> result = format_colored("(dtype:")
\t\t>>> result == "(" + MAGENTA + "dtype" + RESET + ":"
\t\tTrue
\t\t>>> result = format_colored("[1.")
\t\t>>> result == "[" + MAGENTA + "1" + RESET + "."
\t\tTrue

\t\t>>> # Test complex
\t\t>>> text = "<class \'numpy.ndarray\'>, <id 140357548266896>: (dtype: float32, shape: (6,), min: 0.0, max: 1.0) [1. 0. 0. 0. 1. 0.]"
\t\t>>> result = format_colored(text)
\t\t>>> result.count(MAGENTA)  # class, numpy, ndarray, float32, 6, 0.0, 1.0, 1. 0.
\t\t16
\t'''
def colored(*values: Any, file: TextIO | None = None, **print_kwargs: Any) -> None:
    ''' Print with Python 3.14 style colored formatting.

\tDynamically colors text by analyzing each word:
\t- File paths in magenta
\t- Numbers in magenta
\t- Function names (built-in and callable objects) in magenta
\t- Exception names in bold magenta

\tArgs:
\t\tvalues\t\t\t(Any):\t\tValues to print (like the print function)
\t\tfile\t\t\t(TextIO):\tFile to write the message to (default: sys.stdout)
\t\tprint_kwargs\t(dict):\t\tKeyword arguments to pass to the print function

\tExamples:
\t\t>>> colored("File \'/path/to/file.py\', line 42, in function_name")  # doctest: +SKIP
\t\t>>> colored("KeyboardInterrupt")  # doctest: +SKIP
\t\t>>> colored("Processing data.csv with 100 items")  # doctest: +SKIP
\t\t>>> colored("Using print and len functions")  # doctest: +SKIP
\t'''
def info(*values: Any, color: str = ..., text: str = 'INFO ', prefix: str = '', file: TextIO | list[TextIO] | None = None, use_colored: bool = False, **print_kwargs: Any) -> None:
    ''' Print an information message looking like "[INFO HH:MM:SS] message" in green by default.

\tArgs:
\t\tvalues\t\t\t(Any):\t\t\t\t\tValues to print (like the print function)
\t\tcolor\t\t\t(str):\t\t\t\t\tColor of the message (default: GREEN)
\t\ttext\t\t\t(str):\t\t\t\t\tText of the message (default: "INFO ")
\t\tprefix\t\t\t(str):\t\t\t\t\tPrefix to add to the values
\t\tfile\t\t\t(TextIO|list[TextIO]):\tFile(s) to write the message to (default: sys.stdout)
\t\tuse_colored\t\t(bool):\t\t\t\t\tWhether to use the colored() function to format the message
\t\tprint_kwargs\t(dict):\t\t\t\t\tKeyword arguments to pass to the print function
\t'''
def debug(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
    ''' Print a debug message looking like "[DEBUG HH:MM:SS] message" in cyan by default. '''
def alt_debug(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
    ''' Print a debug message looking like "[DEBUG HH:MM:SS] message" in blue by default. '''
def suggestion(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
    ''' Print a suggestion message looking like "[SUGGESTION HH:MM:SS] message" in cyan by default. '''
def progress(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
    ''' Print a progress message looking like "[PROGRESS HH:MM:SS] message" in magenta by default. '''
def warning(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
    ''' Print a warning message looking like "[WARNING HH:MM:SS] message" in yellow by default and in sys.stderr. '''
def error(*values: Any, exit: bool = False, flush: bool = True, **print_kwargs: Any) -> None:
    """ Print an error message (in sys.stderr and in red by default)
\tand optionally ask the user to continue or stop the program.

\tArgs:
\t\tvalues\t\t\t(Any):\t\tValues to print (like the print function)
\t\texit\t\t\t(bool):\t\tWhether to ask the user to continue or stop the program,
\t\t\tfalse to ignore the error automatically and continue
\t\tprint_kwargs\t(dict):\t\tKeyword arguments to pass to the print function
\t"""
def whatisit(*values: Any, print_function: Callable[..., None] = ..., flush: bool = True, max_length: int = 250, color: str = ..., **print_kwargs: Any) -> None:
    ''' Print the type of each value and the value itself, with its id and length/shape.

\tThe output format is: "type, <id id_number>:\t(length/shape) value"

\tArgs:
\t\tvalues\t\t\t(Any):\t\tValues to print
\t\tprint_function\t(Callable):\tFunction to use to print the values (default: debug())
\t\tmax_length\t\t(int):\t\tMaximum length of the value string to print (default: 250)
\t\tcolor\t\t\t(str):\t\tColor of the message (default: CYAN)
\t\tprint_kwargs\t(dict):\t\tKeyword arguments to pass to the print function
\t'''
def breakpoint(*values: Any, print_function: Callable[..., None] = ..., flush: bool = True, **print_kwargs: Any) -> None:
    """ Breakpoint function, pause the program and print the values.

\tArgs:
\t\tvalues\t\t\t(Any):\t\tValues to print
\t\tprint_function\t(Callable):\tFunction to use to print the values (default: warning())
\t\tprint_kwargs\t(dict):\t\tKeyword arguments to pass to the print function
\t"""

class TeeMultiOutput:
    ''' File-like object that duplicates output to multiple file-like objects.

\tArgs:
\t\t*files         (IO[Any]):  One or more file-like objects that have write and flush methods
\t\tstrip_colors   (bool):     Strip ANSI color codes from output sent to non-stdout/stderr files
\t\tascii_only     (bool):     Replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files
\t\tignore_lineup  (bool):     Ignore lines containing LINE_UP escape sequence in non-terminal outputs

\tExamples:
\t\t>>> f = open("logfile.txt", "w")
\t\t>>> sys.stdout = TeeMultiOutput(sys.stdout, f)
\t\t>>> print("Hello World")  # Output goes to both console and file
\t\tHello World
\t\t>>> f.close()\t# TeeMultiOutput will handle any future writes to closed files gracefully
\t'''
    files: tuple[IO[Any], ...]
    strip_colors: bool
    ascii_only: bool
    ignore_lineup: bool
    def __init__(self, *files: IO[Any], strip_colors: bool = True, ascii_only: bool = True, ignore_lineup: bool = True) -> None: ...
    @property
    def encoding(self) -> str:
        ''' Get the encoding of the first file, or "utf-8" as fallback.

\t\tReturns:
\t\t\tstr: The encoding, ex: "utf-8", "ascii", "latin1", etc.
\t\t'''
    def write(self, obj: str) -> int:
        """ Write the object to all files while stripping colors if needed.

\t\tArgs:
\t\t\tobj (str): String to write
\t\tReturns:
\t\t\tint: Number of characters written to the first file
\t\t"""
    def flush(self) -> None:
        """ Flush all files. """
    def fileno(self) -> int:
        """ Return the file descriptor of the first file. """

def remove_colors(text: str) -> str:
    """ Remove the colors from a text """
def is_same_print(*args: Any, **kwargs: Any) -> bool:
    """ Checks if the current print call is the same as the previous one. """
def current_time() -> str:
    ''' Get the current time as "HH:MM:SS" if less than 24 hours since import, else "YYYY-MM-DD HH:MM:SS" '''
def infoc(*args: Any, **kwargs: Any) -> None: ...
def debugc(*args: Any, **kwargs: Any) -> None: ...
def alt_debugc(*args: Any, **kwargs: Any) -> None: ...
def warningc(*args: Any, **kwargs: Any) -> None: ...
def errorc(*args: Any, **kwargs: Any) -> None: ...
def progressc(*args: Any, **kwargs: Any) -> None: ...
def suggestionc(*args: Any, **kwargs: Any) -> None: ...
def whatisitc(*args: Any, **kwargs: Any) -> None: ...
def breakpointc(*args: Any, **kwargs: Any) -> None: ...
