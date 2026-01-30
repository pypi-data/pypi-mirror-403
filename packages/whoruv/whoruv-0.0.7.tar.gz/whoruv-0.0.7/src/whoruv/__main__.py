import argparse

from . import __version__
from ._core import format_python_info, whoruv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Display Python version, executable path, and script path"
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s v{__version__}"
    )
    parser.parse_args()

    print(format_python_info(whoruv()))


if __name__ == "__main__":
    main()
