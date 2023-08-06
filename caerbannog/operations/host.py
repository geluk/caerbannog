import platform
from typing import Optional


def is_arch_linux():
    return is_linux("Arch Linux")


def is_linux(distribution: Optional[str] = None):
    if platform.system() != "Linux":
        return False

    dist_matches = True
    if distribution is not None:
        dist_matches = platform.freedesktop_os_release()["NAME"] == distribution

    return dist_matches


def is_windows():
    return platform.system() == "Windows"
