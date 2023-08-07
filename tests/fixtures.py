import sys
from types import ModuleType
from typing import Any, Iterator

import pytest


@pytest.fixture(scope="function")
def target() -> Iterator[ModuleType]:
    import caerbannog.target

    yield caerbannog.target
    del sys.modules["caerbannog.target"]
