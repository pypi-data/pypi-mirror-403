"""Defines a no-operation function that does nothing."""

from typing import Any


def nop(*args: Any, **kwargs: Any) -> None:
    """Accepts any arguments and intentionally does nothing."""
    pass
