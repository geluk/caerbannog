import enum
import os
from os import DirEntry
from typing import Any, Dict, List, Tuple, cast

import yaml

from caerbannog import password, secrets, target


def load_all():
    all_vars = load_vars("vars", "all")

    targets = _get_targets_depth_first(target.current())

    for tgt in targets:
        all_vars = unify(all_vars, load_vars("vars/targets", tgt.name()))

    return all_vars


def load_vars(directory, key) -> Dict[str, Any]:
    dir_name = os.path.join(directory, key)
    yaml_name = f"{dir_name}.yaml"
    yml_name = f"{dir_name}.yml"

    vars: Dict[str, Any] = {}

    if os.path.isdir(dir_name):
        vars_files = [file for file in os.scandir(dir_name) if _is_vars_file(file)]
        vars_files.sort(key=lambda f: f.name)
        for entry in vars_files:
            entry_vars = _load_var_file(entry.path)
            vars = unify(vars, entry_vars)
    elif os.path.isfile(yaml_name):
        vars = unify(vars, _load_var_file(yaml_name))
    elif os.path.isfile(yml_name):
        vars = unify(vars, _load_var_file(yml_name))

    return vars


class MergeStrategy(enum.StrEnum):
    MERGE = enum.auto()
    REPLACE = enum.auto()
    ERROR = enum.auto()


CONFLICT_HINT = "$conflict"


def unify(
    base: Dict[str, Any],
    overlay: Dict[str, Any],
    strategy: MergeStrategy = MergeStrategy.MERGE,
) -> Dict[str, Any]:
    """
    Unify the variables in `base` and `overlay`, recursively merging them
    according to the given `MergeStrategy`. If either variable set contains
    conflict resolution hints, they will be applied at the level where they are
    defined.
    """
    given_strategy = overlay.get(CONFLICT_HINT, base.get(CONFLICT_HINT, None))

    unified: Dict[str, Any] = {}
    if given_strategy is not None:
        unified[CONFLICT_HINT] = str(given_strategy)

    strategy = given_strategy or strategy
    if strategy == MergeStrategy.ERROR:
        raise Exception("Refusing to merge conflicting dictionaries.")
    elif strategy == MergeStrategy.REPLACE:
        for k, v in overlay.items():
            if k == CONFLICT_HINT:
                continue
            unified[k] = v
        return unified

    for key in base.keys() | overlay.keys():
        in_base = key in base
        in_overlay = key in overlay
        base_v = base.get(key, None)
        overlay_v = overlay.get(key, None)

        if in_base and not in_overlay:
            unified[key] = base_v
        elif in_overlay and not in_base:
            unified[key] = overlay_v
        elif type(base_v) == dict and type(overlay_v) == dict:
            unified[key] = unify(cast(Any, base_v), cast(Any, overlay_v), strategy)
        else:
            unified[key] = overlay_v

    return unified


def _get_targets_depth_first(
    target: "target.TargetDescriptor",
) -> List["target.TargetDescriptor"]:
    known_targets: Dict["target.TargetDescriptor", int] = dict()

    def add(target: "target.TargetDescriptor", depth):
        existing_depth = known_targets.get(target)
        if existing_depth is None:
            known_targets[target] = depth
        else:
            known_targets[target] = min(existing_depth, depth)

    def recurse(target: "target.TargetDescriptor", depth):
        add(target, depth)
        for dependency in target.dependencies():
            recurse(dependency, depth + 1)

    recurse(target, 0)

    def sort_depth_first_then_name(pair: Tuple["target.TargetDescriptor", int]):
        target, depth = pair
        return (-depth, target.name())

    sorted_targets = sorted(known_targets.items(), key=sort_depth_first_then_name)
    return [tgt for tgt, _ in sorted_targets]


def _is_vars_file(entry: DirEntry[str]) -> bool:
    return entry.is_file() and (
        entry.name.endswith(".yaml") or entry.name.endswith(".yml")
    )


def _load_var_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
        if content.startswith(secrets.SECRET_MARKER):
            content = secrets.decrypt(content, password.get_password()).decode("utf-8")

    return yaml.load(content, yaml.Loader)
