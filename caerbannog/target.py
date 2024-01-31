from importlib import import_module
from typing import Dict, Iterator, List, Optional

from caerbannog import context
from caerbannog.logging import *
from caerbannog.operations import Do


def apply_role(role: str):
    log_ctx = LogContext()
    with log_ctx.level():
        log_ctx.no_change(f"Role {fmt.target(role)}")

        module_name = f"roles.{role}.role"

        try:
            module = import_module(module_name)
        except Exception as e:
            logger.error(f"Failed to import role '{role}'", e)
            return

        with context.role(role, log_ctx) as role_ctx:
            try:
                module.configure()
                role_ctx.run_handlers()

            except Exception as e:
                logger.error(f"Failed to apply role", e)
                return


_targets: Dict[str, "TargetDescriptor"] = {}
_current = None


class TargetDescriptor:
    def __init__(self, name) -> None:
        self._name = name
        self._requires: List[str] = []
        self._roles: List[str] = []

    def depends_on(self, *names: str) -> "TargetDescriptor":
        self._requires.extend(names)
        return self

    def has_roles(self, *roles: str) -> "TargetDescriptor":
        self._roles.extend(roles)
        return self

    def roles(self) -> List[str]:
        return self._roles

    def name(self) -> str:
        return self._name

    def dependencies(self) -> List["TargetDescriptor"]:
        return [target(name) for name in self._requires]

    def includes(self, name: str) -> bool:
        return self._name == name or any(
            [_targets[t].includes(name) for t in self._requires]
        )

    def execute(self, role_limit: Optional[List[str]] = [], skip_roles: List[str] = []):
        for req in self._requires:
            logger.info(f"Target {fmt.target(self._name)} requires {fmt.target(req)}")
            _targets[req].execute(role_limit=role_limit, skip_roles=skip_roles)

        logger.info(f"Applying target {fmt.target(self._name)}")
        for role in self._roles:
            if (role_limit is not None and role not in role_limit) or role in skip_roles:
                continue
            apply_role(role)


def target(name: str):
    if name not in _targets:
        _targets[name] = TargetDescriptor(name)

    return _targets[name]


def all() -> Iterator[TargetDescriptor]:
    for target in _targets.values():
        yield target


def current() -> TargetDescriptor:
    if _current is None:
        raise Exception("No target active yet")

    return _current


def is_targeted(tgt: str) -> bool:
    if not tgt in _targets:
        raise Exception(f"target '{tgt}' does not exist")

    return current().includes(tgt)


def select_target(target: str):
    global _current
    _current = _targets[target]


class TargetNotSupportedError(Exception):
    def __init__(self) -> None:
        super().__init__(
            f"the role '{context.current_role()}' does not support the target '{current().name()}'"
        )
