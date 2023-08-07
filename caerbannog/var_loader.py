import os
from os import DirEntry
from typing import Any, Dict, List, Tuple

import yaml

from caerbannog import password, secrets, target


def load_all():
    all_vars = load_vars("vars", "all")

    targets = _get_targets_depth_first(target.current())

    for tgt in targets:
        all_vars |= load_vars("vars/targets", tgt.name())

    return all_vars


def load_vars(directory, key) -> Dict[str, Any]:
    dir_name = os.path.join(directory, key)
    yaml_name = f"{dir_name}.yaml"
    yml_name = f"{dir_name}.yml"

    vars = {}

    if os.path.isdir(dir_name):
        vars_files = [file for file in os.scandir(dir_name) if _is_vars_file(file)]
        vars_files.sort(key=lambda f: f.name)
        for entry in vars_files:
            entry_vars = _load_vars(entry.path)
            vars |= entry_vars
    elif os.path.isfile(yaml_name):
        vars |= _load_vars(yaml_name)
    elif os.path.isfile(yml_name):
        vars |= _load_vars(yml_name)

    return vars


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


def _load_vars(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
        if content.startswith(secrets.SECRET_MARKER):
            content = secrets.decrypt(content, password.get_password()).decode("utf-8")

    return yaml.load(content, yaml.Loader)
