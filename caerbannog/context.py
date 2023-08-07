import argparse
import json
import os
import platform
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    # The context and settings modules form a circular dependency. The settings module
    # is only used for a type annotation in this module, so we let the type checkers
    # deal with the circular dependency, while during normal runtime it will not exist.
    from caerbannog.settings import Settings

if platform.system() == "Linux":
    import grp

from caerbannog import var_loader
from caerbannog.command import ElevationType
from caerbannog.roles.role_context import RoleContext

_context: Dict[str, Any] = {
    "root": os.getcwd(),
    "current_role": None,
    "role_vars": {},
    "elevation": str(ElevationType.NONE),
}
_role_context = None
_settings = None

_should_modify = True


def _load_vars():
    _context["vars"] = var_loader.load_all()


def _load_host():
    user: Dict[str, Any] = {}
    if platform.system() == "Linux":
        user["username"] = os.getlogin()
        user["groupname"] = grp.getgrgid(os.getgid()).gr_name
        user["uid"] = os.getuid()
        user["gid"] = os.getgid()
        user["home_dir"] = os.path.expanduser(f"~{user['username']}")
    else:
        user["username"] = os.getlogin()
        user["home_dir"] = os.path.expanduser("~")

    _context["env"] = {k: v for (k, v) in os.environ.items()}

    _context["host"] = {"os": os.name, "system": platform.system(), "user": user}


def init(args: argparse.Namespace):
    def try_read(key):
        if hasattr(args, key):
            return getattr(args, key)
        return None

    global _should_modify
    global _context

    _should_modify = not try_read("dry_run")

    serialized_context = try_read("context")
    if serialized_context is not None:
        _context = json.loads(serialized_context)

    else:
        _context["target"] = try_read("target")

        if platform.system() == "Windows":
            if try_read("elevate"):
                raise Exception("Elevation is not supported on Windows")
            else:
                _context["elevation"] = str(ElevationType.NONE)
        else:
            if try_read("elevate"):
                _context["elevation"] = str(ElevationType.ELEVATED)
            else:
                _context["elevation"] = str(ElevationType.JUST_IN_TIME)

        _load_host()
        _load_vars()


def serialize() -> str:
    return json.dumps(_context)


def context():
    return _context


def elevation() -> ElevationType:
    return ElevationType(_context["elevation"])


def root() -> str:
    return _context["root"]


def user_home_dir() -> str:
    return _context["host"]["user"]["home_dir"]


def username() -> str:
    return _context["host"]["user"]["username"]


def groupname() -> str:
    return _context["host"]["user"]["groupname"]


def vars():
    return _context["vars"]


def env(variable=None):
    if variable is not None:
        return _context["env"][variable]

    return _context["env"]


def current_role() -> str:
    return _context["current_role"]


def current_role_dir() -> str:
    return role_dir(current_role())


def role_dir(role: str) -> str:
    return os.path.join(root(), "roles", role)


def resolve_path(*paths_to_resolve: str) -> str:
    return os.path.join(current_role_dir(), *paths_to_resolve)


def should_modify():
    """
    Returns `False` if `--dry-run` is specified, `True` otherwise.
    """
    return _should_modify


def role_vars():
    return _context["role_vars"]


def system():
    return _context["host"]["system"]


def settings() -> "Settings":
    if _settings is None:
        raise Exception("Settings are not available yet")
    return _settings


def role_context() -> "RoleContext":
    if _role_context is None:
        raise Exception("No role is currently executing")

    return _role_context


@contextmanager
def role(name, log):
    global _role_context
    try:
        _role_context = RoleContext(log)
        _context["role_vars"] = {}
        _context["current_role"] = name
        yield _role_context
    finally:
        _role_context = None
        _context["role_vars"] = {}
        _context["current_role"] = None


@contextmanager
def dry_run():
    global _should_modify
    backup = _should_modify
    _should_modify = False
    try:
        yield
    finally:
        _should_modify = backup
