import platform
import subprocess
from typing import Dict, Set

from caerbannog import context
from caerbannog.operations import *
from caerbannog.logging import *


class Package(Subject):
    def __init__(self, *names: str) -> None:
        super().__init__()
        self._names = list(names)

    def is_installed(self):
        if platform.freedesktop_os_release()["NAME"] != "Arch Linux":
            raise NotImplementedError()

        self.add_assertion(IsInstalled(self._names))
        return self

    def describe(self):
        joined = ", ".join(map(fmt.subject, self._names))
        if len(self._names) > 1:
            return f"packages {joined}"
        return f"package {joined}"

    def clone(self) -> Self:
        return Package(*self._names)


class IsInstalled(Assertion):
    _cache: Union[Tuple[Set[str], Dict[str, Set[str]]], None] = None

    def __init__(self, names: List[str]) -> None:
        if len(names) > 1:
            descr = "are installed"
        else:
            descr = "is installed"
        super().__init__(descr)
        self._package_names = set(names)

    def apply(self, log: LogContext):
        packages, groups = IsInstalled._load_installed()

        present = packages | groups.keys()
        missing = self._package_names - present

        if len(missing) == 0:
            self._display(log)
            return

        if context.should_modify():
            install = subprocess.run(
                ["sudo", "pacman", "--sync", "--noconfirm", *missing],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if install != 0:
                raise Exception(f"installation failed", install.stdout)
            self.register_change(Installed(install.stdout.splitlines()))
        else:
            self.register_change(Installed([DiffLine.add(name) for name in missing]))

        self._display(log)

    @staticmethod
    def _load_installed() -> Tuple[Set[str], Dict[str, Set[str]]]:
        if IsInstalled._cache is not None:
            return IsInstalled._cache

        query_packages = subprocess.run(
            ["pacman", "--query", "--quiet"],
            capture_output=True,
            text=True,
            check=True,
        )
        query_groups = subprocess.run(
            ["pacman", "--query", "--groups"],
            capture_output=True,
            text=True,
            check=True,
        )
        packages = set(query_packages.stdout.splitlines())
        groups: Dict[str, Set[str]] = {}
        for line in query_groups.stdout.splitlines():
            [group, package] = line.split(" ")
            entry = groups.setdefault(group, set())
            entry.add(package)

        IsInstalled._cache = packages, groups
        return packages, groups


class Installed(Change):
    def __init__(self, details: Sequence[str | Tuple[DiffType, str]]):
        super().__init__("installed", details)
