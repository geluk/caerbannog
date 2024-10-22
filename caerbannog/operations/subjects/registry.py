import winreg
from caerbannog.logging import LogContext

from caerbannog.operations import *
from caerbannog.operations.windows import RegistryHive


class RegistryKey(Subject):
    def __init__(self, hive: RegistryHive, path: str) -> None:
        self._hive = hive
        self._path = path
        self._full_key = f"{str(self._hive.name)}\\{self._path}"
        super().__init__()

    def clone(self) -> Self:
        return RegistryKey(self._hive, self._path)

    def describe(self) -> str:
        formatted_key = fmt.code(self._full_key)
        return f"Registry key {formatted_key}"

    def has_string_value(self, key: str, value: str) -> Self:
        self.add_assertion(
            HasValue(self._hive, self._path, key, value, "string"), allow_multiple=True
        )
        return self


class HasValue(Assertion):
    def __init__(
        self, hive: RegistryHive, path: str, key: str, value: Any, type: str
    ) -> None:
        self._hive = hive
        self._path = path
        self._key = key
        self._value = value
        self._type = type

        super().__init__(f"has {type} value")

    def apply(self, log: LogContext):
        conn = winreg.OpenKey(
            self._hive.key_type,
            f"{self._path}\\{self._key}",
            access=winreg.KEY_READ,
        )

        if context.should_modify():
            pass

        print(
            f"apply me {self._hive.name}\\{self._path}.{self._key} ({self._type}) = {self._value}"
        )
