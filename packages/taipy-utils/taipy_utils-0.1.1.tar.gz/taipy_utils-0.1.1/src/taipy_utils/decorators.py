"""Decorators for Taipy GUI callback functions.

This module provides decorators to handle common patterns in Taipy callbacks:
- Automatic error handling and user notifications
- Control flow management (hold/resume)
"""

import inspect
from functools import wraps
from typing import Any, Callable, Optional

from taipy.gui import State, hold_control, notify, resume_control


def taipy_callback(func: Callable) -> Callable:
    """Decorator that translates Python exceptions to Taipy notifications.

    Catches ValueError and shows warning notifications, catches other exceptions
    and shows error notifications while re-raising them.

    Args:
        func: Taipy callback function to wrap

    Returns:
        Wrapped function with automatic error handling

    Example:
        >>> @taipy_callback
        ... def on_button_click(state):
        ...     if state.value < 0:
        ...         raise ValueError("Value must be positive")
        ...     # process normally
    """

    @wraps(func)
    def wrapper(
        state: State, var_name: Optional[str] = None, payload: Optional[dict] = None
    ) -> Any:
        with state as s:
            try:
                return _call_with_appropriate_args(func, s, var_name, payload)
            except ValueError as e:
                notify(s, "w", str(e))
            except Exception as e:
                notify(s, "e", f"Unexpected error: {str(e)}")
                raise

    return wrapper


def hold_control_during_execution(message: str = "Processing...") -> Callable:
    """Decorator to hold control during callback execution.

    Holds the Taipy GUI control before executing the callback and resumes
    it afterwards, even if an exception occurs.

    Args:
        message: Message to display while control is held

    Returns:
        Decorator function

    Example:
        >>> @hold_control_during_execution("Loading data...")
        ... def on_load_data(state):
        ...     # long running operation
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(
            state: State, var_name: Optional[str] = None, payload: Optional[dict] = None
        ) -> Any:
            hold_control(state, message=message)
            try:
                return _call_with_appropriate_args(func, state, var_name, payload)
            finally:
                resume_control(state)

        return wrapper

    return decorator


def _call_with_appropriate_args(
    func: Callable,
    state: State,
    var_name: Optional[str] = None,
    payload: Optional[dict] = None,
) -> Any:
    """Call a function with the appropriate number of arguments based on its signature.

    Args:
        func: Function to call
        state: Taipy state object
        var_name: Optional variable name
        payload: Optional payload dictionary

    Returns:
        Result of the function call
    """
    sig = inspect.signature(func)
    num_params = len(sig.parameters)

    if num_params == 1:
        return func(state)
    elif num_params == 2:
        return func(state, var_name)
    else:
        return func(state, var_name, payload)
