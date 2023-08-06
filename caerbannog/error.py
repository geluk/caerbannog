from traceback import FrameSummary
from typing import Optional


class CaerbannogError(Exception):
    def __init__(self, message: str, context: Optional["ErrorContext"] = None) -> None:
        self._error_context = context
        super().__init__(message)

    def context(self):
        return self._error_context

    @staticmethod
    def from_frame(message: str, frame: FrameSummary):
        return CaerbannogError(message, ErrorContext(frame.filename, frame.line or "", frame.lineno or -1))

class ErrorContext():
    def __init__(self, filename: str, line: str, lineno: int) -> None:
        self._filename = filename
        self._line = line
        self._lineno = lineno
