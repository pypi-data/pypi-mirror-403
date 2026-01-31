from ..io import super_open as super_open
from typing import Any

def read_pyproject(pyproject_path: str) -> dict[str, Any]:
    ''' Read the pyproject.toml file.

\tArgs:
\t\tpyproject_path: Path to the pyproject.toml file.
\tReturns:
\t\tdict[str, Any]: The content of the pyproject.toml file.
\tExample:
\t\t>>> content = read_pyproject("pyproject.toml")
\t\t>>> "." in content["project"]["version"]
\t\tTrue
\t'''
def format_toml_lists(content: str) -> str:
    ''' Format TOML lists with indentation.

\tArgs:
\t\tcontent (str): The content of the pyproject.toml file.
\tReturns:
\t\tstr: The formatted content with properly indented lists.
\tExample:
\t\t>>> toml_content = \'\'\'[project]
\t\t... dependencies = [ "tqdm>=4.0.0", "requests>=2.20.0", "pyyaml>=6.0.0", ]\'\'\'
\t\t>>> format_toml_lists(toml_content).replace("\\t", "    ") == \'\'\'[project]
\t\t... dependencies = [
\t\t...     "tqdm>=4.0.0",
\t\t...     "requests>=2.20.0",
\t\t...     "pyyaml>=6.0.0",
\t\t... ]\'\'\'
\t\tTrue
\t'''
def write_pyproject(path: str, content: dict[str, Any]) -> None:
    """ Write to the pyproject.toml file with properly indented lists.

\tArgs:
\t\tpath: Path to the pyproject.toml file.
\t\tcontent: Content to write to the pyproject.toml file.
\t"""
def increment_version_from_input(version: str) -> str:
    ''' Increment the version.

\tArgs:
\t\tversion: The version to increment. (ex: "0.1.0")
\tReturns:
\t\tstr: The incremented version. (ex: "0.1.1")
\tExample:
\t\t>>> increment_version_from_input("0.1.0")
\t\t\'0.1.1\'
\t\t>>> increment_version_from_input("1.2.9")
\t\t\'1.2.10\'
\t'''
def increment_version_from_pyproject(path: str) -> None:
    """ Increment the version in the pyproject.toml file.

\tArgs:
\t\tpath: Path to the pyproject.toml file.
\t"""
def get_version_from_pyproject(path: str) -> str:
    ''' Get the version from the pyproject.toml file.

\tArgs:
\t\tpath: Path to the pyproject.toml file.
\tReturns:
\t\tstr: The version. (ex: "0.1.0")
\t'''
