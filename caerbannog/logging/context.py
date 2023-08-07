import sys
from contextlib import contextmanager

from .fmt import *


class LogContext:
    def __init__(self) -> None:
        self._depth = 0

    @contextmanager
    def level(self):
        try:
            self._depth += 1
            yield
        finally:
            self._depth -= 1

    def no_change(self, msg):
        print(f"[{FG_GREEN}*{FG_RESET}] {self._indent()}{msg}", file=sys.stderr)

    def change(self, msg):
        print(f"[{FG_YELLOW}≈{FG_RESET}] {self._indent()}{msg}", file=sys.stderr)

    def assertion_fail(self, msg):
        print(f"{self._indent()}  {FG_RED}×{FG_RESET} {msg}", file=sys.stderr)

    def assertion_change(self, msg):
        print(f"{self._indent()}  {FG_YELLOW}⟳{FG_RESET} {msg}", file=sys.stderr)

    def assertion_pass(self, msg):
        print(f"{self._indent()}  {FG_GREEN}✓{FG_RESET} {msg}", file=sys.stderr)

    def detail(self, msg):
        print(f"    {self._indent()}{msg}", file=sys.stderr)

    def detail_red(self, msg):
        print(f"    {self._indent()}{FG_RED}{msg}{FG_RESET}", file=sys.stderr)

    def detail_green(self, msg):
        print(f"    {self._indent()}{FG_GREEN}{msg}{FG_RESET}", file=sys.stderr)

    def _indent(self) -> str:
        return "  " * self._depth

    def changes_are_errors(self) -> "ChangesAreErrors":
        return ChangesAreErrors(self._depth)


class ChangesAreErrors(LogContext):
    def __init__(self, depth: int) -> None:
        super().__init__()
        self._depth = depth

    def no_change(self, msg):
        print(f"[{FG_GREEN}*{FG_RESET}] {self._indent()}{msg}", file=sys.stderr)

    def change(self, msg):
        print(f"[{FG_RED}≈{FG_RESET}] {self._indent()}{msg}", file=sys.stderr)

    def assertion_fail(self, msg):
        print(f"{self._indent()}  {FG_RED}×{FG_RESET} {msg}", file=sys.stderr)

    def assertion_change(self, msg):
        print(f"{self._indent()}  {FG_RED}×{FG_RESET} {msg}", file=sys.stderr)

    def assertion_pass(self, msg):
        print(f"{self._indent()}  {FG_GREEN}✓{FG_RESET} {msg}", file=sys.stderr)

    def detail(self, msg):
        pass

    def detail_red(self, msg):
        pass

    def detail_green(self, msg):
        pass
