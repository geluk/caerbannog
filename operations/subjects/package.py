import subprocess
from typing import Dict, Set

from caerbannog import context
from caerbannog.operations import *
from caerbannog.logging import *


class Package(Subject):
    def __init__(self, *ids: str) -> None:
        super().__init__()
        self._names = list(ids)

    def is_installed(self):
        if host.is_arch_linux():
            self.add_assertion(PacmanPackageIsInstalled(set(self._names)))
        elif host.is_windows():
            for name in self._names:
                self.add_assertion(WinGetPackageIsInstalled(name))
        else:
            raise NotImplementedError()

        return self

    def describe(self):
        joined = ", ".join(map(fmt.subject, self._names))
        if len(self._names) > 1:
            return f"packages {joined}"
        return f"package {joined}"

    def clone(self) -> Self:
        return Package(*self._names)


class WinGetPackage(Subject):
    def __init__(self, *ids: str) -> None:
        super().__init__()
        self._ids = list(ids)

    def is_installed(self):
        if not host.is_arch_linux():
            raise NotImplementedError()

        for id in self._ids:
            self.add_assertion(WinGetPackageIsInstalled(id))
        return self

    def describe(self):
        joined = ", ".join(map(fmt.subject, self._ids))
        if len(self._ids) > 1:
            return f"WinGet packages {joined}"
        return f"WinGet package {joined}"

    def clone(self) -> Self:
        return WinGetPackage(*self._ids)


class PacmanPackage(Subject):
    def __init__(self, *names: str) -> None:
        super().__init__()
        self._names = list(names)

    def is_installed(self):
        if not host.is_arch_linux():
            raise NotImplementedError()

        self.add_assertion(PacmanPackageIsInstalled(set(self._names)))
        return self

    def describe(self):
        joined = ", ".join(map(fmt.subject, self._names))
        if len(self._names) > 1:
            return f"Pacman packages {joined}"
        return f"Pacman package {joined}"

    def clone(self) -> Self:
        return PacmanPackage(*self._names)


class WinGetPackageIsInstalled(Assertion):
    def __init__(self, id: str) -> None:
        descr = "is installed"
        super().__init__(descr)
        self._package_id = id

    def apply(self, log: LogContext):
        query = subprocess.run(
            ["winget", "list", "--id", self._package_id],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        if query.returncode == 0:
            self._display(log)
            return

        if context.should_modify():
            install = subprocess.run(
                ["winget", "install", "--id", self._package_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if install.returncode != 0:
                raise Exception(f"installation failed", install.stdout.splitlines())
            self.register_change(Installed(install.stdout.splitlines()))
        else:
            self.register_change(Installed([DiffLine.add(self._package_id)]))

        self._display(log)


class PacmanPackageIsInstalled(Assertion):
    _cache: Union[Tuple[Set[str], Dict[str, Set[str]]], None] = None

    def __init__(self, names: Set[str]) -> None:
        if len(names) > 1:
            descr = "are installed"
        else:
            descr = "is installed"
        super().__init__(descr)
        self._package_names = names

    def apply(self, log: LogContext):
        packages, groups = PacmanPackageIsInstalled._load_installed()

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
            if install.returncode != 0:
                raise Exception(f"installation failed", install.stdout)
            self.register_change(Installed(install.stdout.splitlines()))
        else:
            self.register_change(Installed([DiffLine.add(name) for name in missing]))

        self._display(log)

    @staticmethod
    def _load_installed() -> Tuple[Set[str], Dict[str, Set[str]]]:
        if PacmanPackageIsInstalled._cache is not None:
            return PacmanPackageIsInstalled._cache

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

        PacmanPackageIsInstalled._cache = packages, groups
        return packages, groups


class Installed(Change):
    def __init__(self, details: Sequence[str | Tuple[DiffType, str]]):
        super().__init__("installed", details)
