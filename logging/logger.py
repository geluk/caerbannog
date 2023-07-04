import sys
import traceback

from .fmt import *


def info(msg):
    print(f"[{FG_GREEN}*{FG_RESET}] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[{FG_YELLOW}!{FG_RESET}] {msg}", file=sys.stderr)


def error(msg, exception):
    print(f"{BG_RED}[×]{BG_RESET} {msg}", file=sys.stderr)
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
