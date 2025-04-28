from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Self,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from caerbannog import context
from caerbannog.logging import *


class Do:
    """
    Make all assertions on the given subjects true, or pretend to make them true
    if `should_modify` is `False` (i.e. `--dry-run` is set).
    """

    def __init__(self, *subjects: "Subject") -> None:
        context.role_context().do(list(subjects))


class Ensure:
    """
    Require that all assertions on the given subjects are true without making
    any changes. If an assertion is false, raise an error.
    """

    def __init__(self, *subjects: "Subject") -> None:
        context.role_context().ensure((list(subjects)))


class Handler:
    def __init__(self, *subjects: "Subject") -> None:
        self._listen: List[Subject] = []
        self._call = list(subjects)
        self._generated = False
        context.role_context().add_handler(self)

    @staticmethod
    def _create_internal(subject: "Subject"):
        handler = Handler(subject)
        handler._generated = True
        return handler

    def register(self, subject: "Subject"):
        self._listen.append(subject)

    def remove(self):
        context.role_context().remove_handler(self)

    def apply(self, log: LogContext):
        any_changed = any(map(lambda a: a.changed(), self._listen))
        if any_changed:
            log.change("executing handler for:")
            with log.level():
                self._display_summary(log)
            for tgt in self._call:
                tgt.apply(log)
        elif not self._generated:
            log.no_change("skipped handler for:")
            self._display_summary(log)

    def _display_summary(self, log):
        with log.level():
            for listen in self._listen:
                if listen.changed():
                    log.change(listen.get_description())
                else:
                    log.no_change(listen.get_description())


class Subject(ABC):
    def __init__(self) -> None:
        super().__init__()
        self._assertions: List[Assertion] = []
        self._subjects_before: List[Subject] = []
        self._description = None

    def apply(self, log: LogContext):
        with log.level():
            log.no_change(self.get_description())

            for assertion in self._assertions:
                assertion.prepare()

            for subject in self._subjects_before:
                subject.apply(log)

            for assertion in self._assertions:
                assertion.apply(log)

    def changed(self) -> bool:
        return any(map(lambda a: a.changed(), self.assertions())) or any(
            map(lambda c: c.changed(), self._subjects_before)
        )

    def add_assertion(self, assertion: "Assertion"):
        """
        Add an assertion to this subject. If an assertion of the same type
        already exists, it will be overwritten.
        """
        self.remove_assertions(type(assertion))
        self._assertions.append(assertion)

    def has_assertion(self, t: Type):
        return any(filter(lambda a: type(a) == t, self._assertions))

    T = TypeVar("T")

    def get_assertion(self, t: Type[T]) -> Optional[T]:
        matching_assertions = list(filter(lambda a: type(a) == t, self._assertions))
        if len(matching_assertions) == 0:
            return None
        return cast(t, matching_assertions[0])

    def get_last_assertion(self, t: Type[T]) -> Optional[T]:
        matching_assertions = list(filter(lambda a: type(a) == t, self._assertions))
        if len(matching_assertions) == 0:
            return None
        return cast(t, matching_assertions[-1])

    def remove_assertions(self, t: Type):
        self._assertions = list(filter(lambda a: type(a) != t, self._assertions))

    def add_subject_before(self, subject: "Subject"):
        self._subjects_before.append(subject)

    def assertions(self) -> Iterable["Assertion"]:
        assertions = [
            assertion
            for subject in self._subjects_before
            for assertion in subject.assertions()
        ]
        assertions.extend(self._assertions)

        return assertions

    def on_change(self, handler: "Handler"):
        handler.register(self)
        return self

    def on_change_self(self, f: Callable[[Self], Any]):
        clone = self.clone()
        f(clone)
        return self.on_change(Handler(clone))

    def annotate(self, description) -> Self:
        """
        Override the default description of this subject.
        """
        self._description = description
        return self

    def get_description(self) -> str:
        if self._description is not None:
            return self._description

        return self.describe()

    @abstractmethod
    def clone(self) -> Self:
        pass

    @abstractmethod
    def describe(self) -> str:
        pass


class Assertion(ABC):
    def __init__(self, name: str) -> None:
        self._changes: List["Change"] = []
        self._assertion_name = name

    def register_change(self, change: "Change"):
        self._changes.append(change)
        if context.should_modify():
            change.execute()

    def changed(self) -> bool:
        return len(self._changes) > 0

    @abstractmethod
    def apply(self, log: LogContext):
        raise NotImplementedError("Assertion.apply()")

    def prepare(self):
        return

    def _display(self, log: LogContext):
        with log.level():
            if self.changed():
                log.assertion_change(self._assertion_name)
                for change in self._changes:
                    change.display(log)
            else:
                log.assertion_pass(self._assertion_name)

    def _display_failed(self, log: LogContext):
        with log.level():
            log.assertion_fail(self._assertion_name)
            for change in self._changes:
                change.display(log)

    def _display_changed(self, log: LogContext):
        with log.level():
            log.assertion_change(self._assertion_name)
            for change in self._changes:
                change.display(log)

    def _display_passed(self, log: LogContext):
        with log.level():
            log.assertion_pass(self._assertion_name)


class Change:
    def __init__(
        self, name: str, details: Sequence[Union[str, Tuple["DiffType", str]]] = []
    ) -> None:
        self._name = name
        self._details: Any = [
            (DiffType.NEUTRAL, detail) if type(detail) is str else detail
            for detail in details
        ]

    def execute(self):
        pass

    def display(self, log: LogContext):
        with log.level():
            log.detail(self._name)
            for diff_type, detail in self._details:
                if diff_type == DiffType.NEUTRAL:
                    log.detail(detail)
                elif diff_type == DiffType.ADD:
                    log.detail_green(detail)
                elif diff_type == DiffType.REMOVE:
                    log.detail_red(detail)
                elif diff_type == DiffType.HEADER:
                    log.detail_cyan(detail)


class DiffType(Enum):
    NEUTRAL = 0
    ADD = 1
    REMOVE = 2
    HEADER = 3


class DiffLine:
    @staticmethod
    def neutral(content: str) -> Tuple[DiffType, str]:
        return (DiffType.NEUTRAL, f"  {content}")

    @staticmethod
    def add(content: str) -> Tuple[DiffType, str]:
        return (DiffType.ADD, f"+ {content}")

    @staticmethod
    def remove(content: str) -> Tuple[DiffType, str]:
        return (DiffType.REMOVE, f"- {content}")

    @staticmethod
    def header(content: str) -> Tuple[DiffType, str]:
        return (DiffType.HEADER, content)

    @staticmethod
    def detail(content: str) -> Tuple[DiffType, str]:
        return (DiffType.NEUTRAL, content)
