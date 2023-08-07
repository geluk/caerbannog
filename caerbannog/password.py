import getpass
import subprocess
from typing import Callable, List

from caerbannog import command, context


def input_loader() -> str:
    return getpass.getpass("Secrets password: ")


def command_loader(cmd: List[str]) -> Callable[[], str]:
    def _command_loader():
        result = subprocess.run(
            command.create_user_command(*cmd),
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.rstrip("\r\n")

    return _command_loader


_cached_password = None


def get_password():
    global _cached_password

    if _cached_password is None:
        loader = context.settings().password_loader()
        _cached_password = loader()

    return _cached_password
