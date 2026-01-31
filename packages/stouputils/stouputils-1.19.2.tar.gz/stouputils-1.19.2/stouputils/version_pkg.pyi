from .print import CYAN as CYAN, GREEN as GREEN, RESET as RESET, YELLOW as YELLOW

def show_version(main_package: str = 'stouputils', primary_color: str = ..., secondary_color: str = ..., max_depth: int = 2) -> None:
    ''' Print the version of the main package and its dependencies.

\tUsed by the "stouputils --version" command.

\tArgs:
\t\tmain_package\t(str):\tName of the main package to show version for
\t\tprimary_color\t(str):\tColor to use for the primary package name
\t\tsecondary_color\t(str):\tColor to use for the secondary package names
\t\tmax_depth\t\t(int):\tMaximum depth for dependency tree (<= 2 for flat, >=3 for tree)
\t'''
def show_version_cli() -> None:
    ''' Handle the "stouputils --version" CLI command '''
