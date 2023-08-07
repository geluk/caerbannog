import subprocess
from typing import Set

from caerbannog import context
from caerbannog.logging import *
from caerbannog.operations import *


class PsGetModule(Subject):
    def __init__(self, *names: str) -> None:
        super().__init__()
        self._names = list(names)

    def is_installed(self):
        for name in self._names:
            self.add_assertion(IsInstalled(name))
        return self

    def describe(self):
        joined = ", ".join(map(fmt.subject, self._names))
        if len(self._names) > 1:
            return f"PsGet modules {joined}"
        return f"PsGet module {joined}"

    def clone(self) -> Self:
        return PsGetModule(*self._names)


class IsInstalled(Assertion):
    _cache: Union[Set[str], None] = None

    def __init__(self, name: str) -> None:
        descr = "is installed"
        super().__init__(descr)
        self._package_name = name

    def apply(self, log: LogContext):
        present = IsInstalled._load_installed()

        if self._package_name in present:
            self._display(log)
            return

        if context.should_modify():
            repository = subprocess.run(
                _powershell(f"(Find-Module {self._package_name}).Repository"),
                check=True,
                text=True,
                capture_output=True,
            )

            install = subprocess.run(
                _powershell(
                    f"Install-Module -Scope CurrentUser {self._package_name}",
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if install.returncode != 0:
                raise Exception(f"installation failed", install.stdout.splitlines())
            self.register_change(Installed(install.stdout.splitlines()))
        else:
            self.register_change(Installed([DiffLine.add(self._package_name)]))

        self._display(log)

    @staticmethod
    def _load_installed() -> Set[str]:
        if IsInstalled._cache is not None:
            return IsInstalled._cache

        query_packages = subprocess.run(
            _powershell("(Get-InstalledModule).Name"),
            capture_output=True,
            text=True,
            check=True,
        )
        packages = set(query_packages.stdout.splitlines())

        IsInstalled._cache = packages
        return packages


class Installed(Change):
    def __init__(self, details: Sequence[str | Tuple[DiffType, str]]):
        super().__init__("installed", details)


def _powershell(command: str):
    return [
        "powershell",
        "-NoProfile",
        "-Command",
        command,
    ]
