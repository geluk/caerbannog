from typing import Any

from fontTools import ttLib

from caerbannog import context
from caerbannog.logging import *
from caerbannog.operations import *


class Font(Subject):
    def __init__(self, path) -> None:
        super().__init__()
        self._orig_path = path
        self._path = context.resolve_path(path)
        self._font = ttLib.TTFont(self._path)
        names: Any = self._font["name"]
        self._name = names.getDebugName(4)

    def is_installed_on_system(self):
        if context.system() == "Windows":
            raise NotImplementedError()
        if context.system() == "Linux":
            raise NotImplementedError()

        self.add_assertion(IsInstalled())
        return self

    def describe(self):
        return f"font {fmt.subject(self._name)}"


class IsInstalled(Assertion):
    def __init__(self) -> None:
        super().__init__("is installed on system")

    def apply(self):
        self.register_change(Installed())


class Installed(Change):
    def __init__(self):
        super().__init__("installed")
