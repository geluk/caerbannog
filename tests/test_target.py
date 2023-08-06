from tests.fixtures import *


def test_no_targets_declared(target):
    assert len(list(target.all())) == 0


def test_multiple_target_invocations(target):
    a = target.target("a")
    a = target.target("a")

    assert len(list(target.all())) == 1


def test_dependency_specified_before_declaration(target):
    a = target.target("a").depends_on("b")
    b = target.target("b")

    assert a.dependencies()[0] == b
