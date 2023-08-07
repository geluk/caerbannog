from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, cast

from caerbannog import context, password, plugin
from caerbannog.commandline import args


def commit():
    target = _load_target()

    settings = _settings_builder._build()
    context._settings = settings

    args.parse(target)


def _load_target() -> Optional[str]:
    try:
        with open(".target", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None


class Settings:
    def __init__(
        self,
        password_loader: Callable[[], str],
        jinja_globals: Dict[str, Any],
        plugins: Dict[str, ModuleType],
    ) -> None:
        self._password_loader = password_loader
        self._jinja_globals = jinja_globals
        self._plugins = plugins

    def jinja_globals(self):
        return self._jinja_globals

    def password_loader(self):
        return self._password_loader


class SettingsBuilder:
    def __init__(self) -> None:
        self._jinja_globals = dict()
        self._password_loader = None
        self._jinja_globals = dict()
        self._plugins = set()

    def use_password_plugin(self, name: str) -> "SettingsBuilder":
        self._password_loader = name
        return self

    def use_password_command(self, cmd: List[str]) -> "SettingsBuilder":
        self._password_loader = cmd
        return self

    def add_jinja_global(self, name: str, value: Any) -> "SettingsBuilder":
        self._jinja_globals[name] = value
        return self

    def load_plugin(self, name: str) -> "SettingsBuilder":
        self._plugins.add(name)
        return self

    def _build(self) -> Settings:
        password_loader = password.input_loader
        if type(self._password_loader) == str:
            password_plugin = plugin.load_plugin(cast(str, self._password_loader))
            password_loader = password_plugin.get_password
        else:
            password_loader = password.command_loader(
                cast(List[str], self._password_loader)
            )

        plugins = {n: plugin.load_plugin(n) for n in self._plugins}

        return Settings(
            password_loader,
            self._jinja_globals,
            plugins,
        )


_settings_builder = SettingsBuilder()


def setup() -> SettingsBuilder:
    return _settings_builder
