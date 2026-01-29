from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def loop_last[T](values: Iterable[T]) -> Iterable[tuple[bool, T]]:
    """Iterate and generate a tuple with a flag for last value.

    Args:
        values: An iterable of values to iterate over.

    Yields:
        A tuple of (is_last, value) for each value in the iterable.

    Example:
        >>> list(loop_last([1, 2, 3]))
        [(False, 1), (False, 2), (True, 3)]
    """
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    for value in iter_values:
        yield False, previous_value
        previous_value = value
    yield True, previous_value
