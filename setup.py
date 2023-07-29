import subprocess
from typing import List, Optional
from caerbannog import plugin, password, command
from caerbannog.commandline import args


def commit():
    target = _load_target()
    args.parse(target)


def _load_target() -> Optional[str]:
    try:
        with open(".target", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return None


class Setup:
    def use_password_plugin(self, name: str) -> "Setup":
        password_plugin = plugin.load_plugin(name)
        password.set_loader(password_plugin.get_password)

        return self

    def use_password_command(self, cmd: List[str]):
        def load_from_command() -> str:
            result = subprocess.run(
                command.create_user_command(*cmd),
                text=True,
                capture_output=True,
                check=True,
            )
            return result.stdout.rstrip("\r\n")

        password.set_loader(load_from_command)
        return self

    def load_plugin(self, name: str):
        plugin.load_plugin(name)


_setup = Setup()


def setup() -> Setup:
    return _setup
