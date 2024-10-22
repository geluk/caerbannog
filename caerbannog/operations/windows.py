from enum import Enum

import winreg


class RegistryHive(Enum):
    CLASSES_ROOT = ("HKEY_CLASSES_ROOT", winreg.HKEY_CLASSES_ROOT)
    CURRENT_CONFIG = ("HKEY_CURRENT_CONFIG", winreg.HKEY_CURRENT_CONFIG)
    CURRENT_USER = ("HKEY_CURRENT_USER", winreg.HKEY_CURRENT_USER)
    LOCAL_MACHINE = ("HKEY_LOCAL_MACHINE", winreg.HKEY_LOCAL_MACHINE)
    PERFORMANCE_DATA = ("HKEY_PERFORMANCE_DATA", winreg.HKEY_PERFORMANCE_DATA)
    USERS = ("HKEY_USERS", winreg.HKEY_USERS)

    def __new__(cls, name: str, key_type: "winreg._KeyType"):
        obj = object.__new__(cls)
        obj.__init__(name, key_type)
        return obj

    def __init__(self, name: str, key_type: "winreg._KeyType") -> None:
        self._name = name
        self._key_type = key_type

    @property
    def name(self):
        return self._name

    @property
    def key_type(self):
        return self._key_type
