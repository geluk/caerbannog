import subprocess

from caerbannog import command, context
from caerbannog.logging import *
from caerbannog.operations import *

if host.is_linux():
    import grp


class Group(Subject):
    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    def is_present(self):
        if not host.is_linux():
            raise NotImplementedError()

        self.add_assertion(IsPresent(self._name))
        return self

    def describe(self):
        return f"group {fmt.subject(self._name)}"

    def clone(self) -> Self:
        return Group(self._name)


class IsPresent(Assertion):
    def __init__(self, name: str) -> None:
        super().__init__("is present")
        self._name = name

    def apply(self, log: LogContext):
        groups = grp.getgrall()
        group = next((g for g in groups if g.gr_name == self._name), None)
        if group is not None:
            self._display(log)
            return

        if context.should_modify():
            groupadd = subprocess.run(
                command.create_elevated_command("groupadd", self._name),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if groupadd.returncode != 0:
                raise Exception("adding group failed", groupadd.stdout)

        self.register_change(Created(self._name))
        self._display(log)


class Created(Change):
    def __init__(self, name: str) -> None:
        super().__init__("created", [DiffLine.add(name)])
