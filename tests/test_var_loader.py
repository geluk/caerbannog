from caerbannog import var_loader
from caerbannog.var_loader import MergeStrategy
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


def test_unify_with_merge_no_conflicts_merges_values():
    base = {"a": 1}
    overlay = {"b": 2}

    joined = var_loader.unify(base, overlay, MergeStrategy.MERGE)

    assert joined == {"a": 1, "b": 2}


def test_unify_with_merge_conflict_prefers_overlay():
    base = {"a": 1}
    overlay = {"a": 2}

    joined = var_loader.unify(base, overlay, MergeStrategy.MERGE)

    assert joined == {"a": 2}


def test_unify_with_merge_conflict_on_dict_type_cascades_merge():
    base = {"a": {"a_a": 1}}
    overlay = {"a": {"a_b": 2}}

    joined = var_loader.unify(base, overlay, MergeStrategy.MERGE)

    assert joined == {"a": {"a_a": 1, "a_b": 2}}


def test_unify_with_replace_no_conflicts_prefers_overlay():
    base = {"a": 1}
    overlay = {"b": 2}

    joined = var_loader.unify(base, overlay, MergeStrategy.REPLACE)

    assert joined == {"b": 2}


def test_unify_with_replace_conflict_prefers_overlay():
    base = {"a": 1}
    overlay = {"a": 2}

    joined = var_loader.unify(base, overlay, MergeStrategy.REPLACE)

    assert joined == {"a": 2}


def test_unify_with_replace_conflict_on_dict_type_prefers_overlay():
    base = {"a": {"a_a": 1}}
    overlay = {"a": {"a_b": 2}}

    joined = var_loader.unify(base, overlay, MergeStrategy.REPLACE)

    assert joined == {"a": {"a_b": 2}}


def test_unify_with_strategy_from_marker():
    base = {"a": 1, "$conflict": "replace"}
    overlay = {"b": 2}

    joined = var_loader.unify(base, overlay, MergeStrategy.MERGE)

    assert joined == {"b": 2, "$conflict": "replace"}


def test_unify_with_merge_and_replace_merges_parent_and_replaces_child():
    base = {"a": {"a_a": 1, "$conflict": "replace"}, "b": 3}
    overlay = {"a": {"a_b": 2, "a_c": 3}}

    joined = var_loader.unify(base, overlay, MergeStrategy.MERGE)

    assert joined == {"a": {"a_b": 2, "a_c": 3, "$conflict": "replace"}, "b": 3}
