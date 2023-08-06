import sys
import traceback
from typing import cast

from caerbannog.error import CaerbannogError

from .fmt import *


def info(msg):
    print(f"[{FG_GREEN}*{FG_RESET}] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[{FG_YELLOW}!{FG_RESET}] {msg}", file=sys.stderr)


def error(msg, exception: Exception):
    print(f"{BG_RED}[×]{BG_RESET} {msg}", file=sys.stderr)
    exception_type = type(exception)

    if exception_type == CaerbannogError:
        exception = cast(CaerbannogError, exception)

        print(f"    {exception}", file=sys.stderr)
        context = exception.context()
        if context is not None:
            line = context._line.replace("\t", "    ")
            print(f"      In '{context._filename}' at line {context._lineno}:")
            print()
            print(f"      {line}")
            print(f"      {'^' * len(line)}")
            print()
    else:
        print(f"    {type(exception).__name__}: {exception}", file=sys.stderr)
        for line in traceback.format_exception(exception):
            for sub_line in line.splitlines():
                print(f"      {sub_line}")


def debug(msg):
    print(msg, file=sys.stderr)


def fatal(msg):
    print(f"[{BG_RED}E{BG_RESET}] {msg}", file=sys.stderr)
    print(f"[{BG_RED}E{BG_RESET}] Exiting...", file=sys.stderr)
    sys.exit(1)
