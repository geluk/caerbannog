from caerbannog import var_loader
from tests.fixtures import *


def test_get_targets_depth_first_diamond_dependency(target):
    a0 = target.target("a0").depends_on("b0", "b1")
    b0 = target.target("b0").depends_on("c0", "c1")
    b1 = target.target("b1").depends_on("c0", "c2")
    c0 = target.target("c0")
    c1 = target.target("c1")
    c2 = target.target("c2")

    targets = var_loader._get_targets_depth_first(a0)

    assert targets == [c0, c1, c2, b0, b1, a0]


def test_get_targets_depth_first_uses_minimum_depth_found(target):
    a0 = target.target("a0").depends_on("b0", "c0")
    b0 = target.target("b0").depends_on("c0")
    c0 = target.target("c0")

    targets = var_loader._get_targets_depth_first(a0)

    assert targets == [b0, c0, a0]
