from typing import Callable
import getpass


def _input_loader():
    return getpass.getpass("Secrets password: ")


_password = None
_loader: Callable[[], str] = _input_loader


def set_loader(loader: Callable[[], str]):
    global _loader
    _loader = loader


def get_password():
    global _password
    global _loader

    if _password is None:
        _password = _loader()

    return _password
