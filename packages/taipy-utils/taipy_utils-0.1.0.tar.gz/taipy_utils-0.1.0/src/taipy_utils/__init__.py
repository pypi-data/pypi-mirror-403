"""Utility decorators and helpers for Taipy GUI applications"""

__version__ = "0.1.0"

from taipy_utils.decorators import (
    hold_control_during_execution,
    taipy_callback,
)

__all__ = [
    "taipy_callback",
    "hold_control_during_execution",
]
