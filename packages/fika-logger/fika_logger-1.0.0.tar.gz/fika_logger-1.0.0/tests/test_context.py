import pytest
from fika_logger.core.context import (
    context,
    get_current_context,
    add_context,
    update_context,
    is_inside_trace,
    set_inside_trace,
    reset_inside_trace,
)


def test_context_manager_sets_and_resets():
    assert get_current_context() == {}
    with context(client="x", user_id="123"):
        ctx = get_current_context()
        assert ctx["client"] == "x"
        assert ctx["user_id"] == "123"
    assert get_current_context() == {}


def test_nested_context():
    with context(client="x"):
        with context(user_id="123"):
            ctx = get_current_context()
            assert ctx["client"] == "x"
            assert ctx["user_id"] == "123"
        ctx = get_current_context()
        assert ctx["client"] == "x"
        assert "user_id" not in ctx


def test_add_context():
    with context(client="x"):
        add_context(user_id="123")
        ctx = get_current_context()
        assert ctx["client"] == "x"
        assert ctx["user_id"] == "123"


def test_update_context():
    with context(client="x"):
        update_context(client="y")
        ctx = get_current_context()
        assert ctx["client"] == "y"


def test_trace_flag():
    assert is_inside_trace() is False
    token = set_inside_trace(True)
    assert is_inside_trace() is True
    reset_inside_trace(token)
    assert is_inside_trace() is False
