import subprocess
from typing import List
from caerbannog import plugin, password, command
from caerbannog.commandline import args


def commit():
    args.parse()


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
