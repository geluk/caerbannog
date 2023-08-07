from importlib import import_module

from caerbannog import context


def load_plugin(name: str):
    module = import_module(name)

    if hasattr(module, "init"):
        module.init(context)

    return module
