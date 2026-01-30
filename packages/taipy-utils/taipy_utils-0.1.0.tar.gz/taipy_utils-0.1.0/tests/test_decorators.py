"""Tests for taipy_utils decorators."""

from unittest.mock import patch

import pytest
from taipy_utils.decorators import hold_control_during_execution, taipy_callback


class MockState:
    """Mock Taipy State for testing."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_taipy_callback_success():
    """Test taipy_callback with successful execution."""

    @taipy_callback
    def callback(state):
        return "success"

    state = MockState()
    result = callback(state)
    assert result == "success"


def test_taipy_callback_value_error():
    """Test taipy_callback catches ValueError and notifies."""

    @taipy_callback
    def callback(state):
        raise ValueError("Test error")

    state = MockState()

    with patch("taipy_utils.decorators.notify") as mock_notify:
        callback(state)
        mock_notify.assert_called_once_with(state, "w", "Test error")


def test_taipy_callback_generic_exception():
    """Test taipy_callback re-raises non-ValueError exceptions."""

    @taipy_callback
    def callback(state):
        raise RuntimeError("Test error")

    state = MockState()

    with patch("taipy_utils.decorators.notify") as mock_notify:
        with pytest.raises(RuntimeError):
            callback(state)
        mock_notify.assert_called_once()


def test_hold_control_during_execution():
    """Test hold_control_during_execution holds and resumes control."""

    @hold_control_during_execution("Testing...")
    def callback(state):
        return "done"

    state = MockState()

    with patch("taipy_utils.decorators.hold_control") as mock_hold:
        with patch("taipy_utils.decorators.resume_control") as mock_resume:
            result = callback(state)

            assert result == "done"
            mock_hold.assert_called_once_with(state, message="Testing...")
            mock_resume.assert_called_once_with(state)


def test_hold_control_resumes_on_exception():
    """Test hold_control_during_execution resumes even on exception."""

    @hold_control_during_execution()
    def callback(state):
        raise ValueError("Error")

    state = MockState()

    with patch("taipy_utils.decorators.hold_control"):
        with patch("taipy_utils.decorators.resume_control") as mock_resume:
            with pytest.raises(ValueError):
                callback(state)

            mock_resume.assert_called_once()
