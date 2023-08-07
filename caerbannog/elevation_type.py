import enum
from enum import StrEnum


class ElevationType(StrEnum):
    NONE = enum.auto()
    JUST_IN_TIME = enum.auto()
    ELEVATED = enum.auto()
