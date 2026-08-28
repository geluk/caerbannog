import pytest
from jinja2 import Environment, UndefinedError

from caerbannog import template

VARS = {"vars": {"git": {"global_hooks_path": "~/.githooks"}}}


def _render(source: str) -> str:
    env = Environment()
    env.undefined = template.StrictChainableUndefined
    return env.from_string(source).render(VARS)


def test_optional_guard_is_falsy_when_undefined():
    assert _render("{% if vars.git.ssh_command %}y{% else %}n{% endif %}") == "n"


def test_optional_guard_is_truthy_when_defined():
    assert _render("{% if vars.git.global_hooks_path %}y{% else %}n{% endif %}") == "y"


def test_not_guard_on_undefined():
    assert _render("{% if not vars.git.missing %}ok{% endif %}") == "ok"


def test_typo_raises_on_emission():
    with pytest.raises(UndefinedError):
        _render("{{ vars.git.global_hook_path }}")


def test_undefined_through_filter_raises():
    with pytest.raises(UndefinedError):
        _render("{{ vars.git.nope | lower }}")


def test_default_returns_fallback_for_undefined():
    assert _render("{{ vars.git.nope | default('fallback') }}") == "fallback"


def test_default_passthrough_for_defined():
    assert _render("{{ vars.git.global_hooks_path | default('fallback') }}") == (
        "~/.githooks"
    )


def test_environment_uses_strict_chainable_undefined(monkeypatch, tmp_path):
    class _Settings:
        def jinja_globals(self):
            return {}

    monkeypatch.setattr(template.context, "settings", lambda: _Settings())
    monkeypatch.setattr(template.context, "current_role_dir", lambda: str(tmp_path))

    env = template._create_environment()

    assert env.undefined is template.StrictChainableUndefined
