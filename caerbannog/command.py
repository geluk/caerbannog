from typing import List

from caerbannog import context
from caerbannog.elevation_type import ElevationType


def create_elevated_command(*args: str) -> List[str]:
    """
    Create a command with elevated privileges. If the current privilege level is
    sufficient, the command is executed immediately. If not, an elevated command
    will be created.
    """

    elevation = context.elevation()

    if elevation == ElevationType.NONE:
        raise Exception(
            "Cannot create an elevated command, because elevation is not allowed."
        )
    if elevation == ElevationType.ELEVATED:
        return list(args)
    if elevation == ElevationType.JUST_IN_TIME:
        command = ["sudo", *args]
        return command

    raise Exception(f"Unknown elevation type: {elevation}")


def create_user_command(*args: str) -> List[str]:
    """
    Create a command with reduced privileges. If the current privilege level is
    not elevated, command is executed immediately. Otherwise, the privilege
    level is dropped before executing the command.
    """

    elevation = context.elevation()

    if elevation == ElevationType.NONE or elevation == ElevationType.JUST_IN_TIME:
        return list(args)
    if elevation == ElevationType.ELEVATED:
        command = ["sudo", "--preserve-env", "--user", context.username(), *args]
        return command

    raise Exception(f"Unknown elevation type: {elevation}")
