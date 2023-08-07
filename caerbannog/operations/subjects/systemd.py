import subprocess
from enum import StrEnum, auto
from typing import Callable

from caerbannog import command
from caerbannog.logging import *
from caerbannog.operations import *
from caerbannog.operations import filesystem

from . import File


class Scope(StrEnum):
    SYSTEM = auto()
    USER = auto()


class ServiceFile(File):
    def __init__(self, service: "SystemdService"):
        if service._scope == Scope.SYSTEM:
            path = f"/etc/systemd/system/{service._name}"
        else:
            path = filesystem.xdg_config_home("systemd", "user", service._name)

        super().__init__(path)

        self._service = service
        self.annotate(f"{str(service._scope)} service file")
        self._handler = None
        self._reload = False
        self._restart = False
        self.reloads_daemon()

    def reloads_daemon(self):
        """
        Reload the systemd daemon if the service file has changed.
        """
        self._reload = True
        self._update_handler()

    def does_not_reload_daemon(self):
        """
        Do not reload the systemd daemon if the service file has changed.
        """
        self._reload = False
        self._update_handler()

    def restarts_service(self):
        """
        Restart the systemd daemon if the service file has changed.
        """
        self._restart = True
        self._update_handler()

    def does_not_restart_service(self):
        """
        Do not restart the systemd daemon if the service file has changed.
        """
        self._restart = False
        self._update_handler()

    def _update_handler(self):
        if self._handler is not None:
            self._handler.remove()
            self._handler = None

        if not self._reload and not self._restart:
            return

        clone = self._service.clone()
        if self._reload:
            clone.is_reloaded()
        if self._restart:
            clone.is_restarted()

        self._handler = Handler._create_internal(clone)
        self._handler.register(self)


class SystemdService(Subject):
    def __init__(self, name, scope=Scope.SYSTEM) -> None:
        super().__init__()
        self._name = name
        self._scope = scope

    def file(self, f: Callable[[ServiceFile], Any]):
        self._file = ServiceFile(self)
        f(self._file)

        self.add_child(self._file)
        return self

    def is_started(self):
        self.add_assertion(IsStarted(self))
        return self

    def is_restarted(self):
        self.add_assertion(IsRestarted(self))
        return self

    def is_enabled(self):
        self.add_assertion(IsEnabled(self))
        return self

    def is_reloaded(self):
        self.add_assertion(IsReloaded(self._scope))
        return self

    def describe(self):
        return f"service {fmt.subject(self._name)}"

    def _get_property(self, property):
        exists = subprocess.run(
            self._create_scoped_command("status", self._name),
            env=context.env(),
            capture_output=True,
        )
        if exists.returncode == 4:
            raise Exception(
                f"Systemd unit '{self._name}' does not exist in {self._scope} scope"
            )

        output = subprocess.run(
            self._create_scoped_command(
                "show", "--value", "--property", property, self._name
            ),
            env=context.env(),
            capture_output=True,
            text=True,
            check=True,
        )
        return output.stdout.rstrip()

    def _create_scoped_command(self, *args):
        return _create_scoped_command(self._scope, *args)

    def clone(self) -> Self:
        return SystemdService(self._name, self._scope)


class IsStarted(Assertion):
    def __init__(self, service: SystemdService) -> None:
        self._service = service
        super().__init__("is started")

    def apply(self, log: LogContext):
        active_state = self._service._get_property("ActiveState")
        if active_state == "active":
            self._display_passed(log)
            return
        elif active_state == "inactive":
            if context.should_modify():
                subprocess.run(
                    self._service._create_scoped_command("start", self._service._name),
                    env=context.env(),
                    check=True,
                )
            self.register_change(Started())
        else:
            raise Exception(
                f"Unknown state for service '{self._service._name}': ActiveState={active_state}"
            )

        self._display(log)


class IsEnabled(Assertion):
    def __init__(self, service: SystemdService) -> None:
        self._service = service
        super().__init__("is enabled")

    def apply(self, log: LogContext):
        unit_file_state = self._service._get_property("UnitFileState")
        if unit_file_state == "enabled":
            self._display_passed(log)
            return
        elif unit_file_state == "disabled":
            if context.should_modify():
                subprocess.run(
                    self._service._create_scoped_command("enable", self._service._name),
                    env=context.env(),
                    check=True,
                )
            self.register_change(Enabled())
        else:
            raise Exception(
                f"Unknown state for service '{self._service._name}': UnitFileState={unit_file_state}"
            )

        self._display(log)


class IsRestarted(Assertion):
    def __init__(self, service: SystemdService) -> None:
        self._service = service
        super().__init__("is restarted")

    def apply(self, log: LogContext):
        if context.should_modify():
            subprocess.run(
                self._service._create_scoped_command("restart", self._service._name),
                env=context.env(),
                check=True,
            )
        self.register_change(Restarted())

        self._display(log)


class IsReloaded(Assertion):
    def __init__(self, scope: Scope) -> None:
        super().__init__(f"systemd {str(scope)} daemon is reloaded")
        self._scope = scope

    def apply(self, log: LogContext):
        if context.should_modify():
            subprocess.run(
                _create_scoped_command(self._scope, "daemon-reload"),
                env=context.env(),
                check=True,
            )
        self.register_change(Reloaded())

        self._display(log)


class Started(Change):
    def __init__(self):
        super().__init__("started")


class Enabled(Change):
    def __init__(self):
        super().__init__("enabled")


class Reloaded(Change):
    def __init__(self):
        super().__init__("reloaded")


class Restarted(Change):
    def __init__(self):
        super().__init__("restarted")


def _create_scoped_command(scope: Scope, *args: str):
    if scope == Scope.SYSTEM:
        return ["systemctl", *args]
    else:
        return command.create_user_command("systemctl", "--user", *args)
