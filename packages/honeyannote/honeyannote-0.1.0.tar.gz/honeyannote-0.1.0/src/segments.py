"""
Segment data structures and protocols.

This module provides the `Segment` class for representing intervals with
generic, orderable, and arithmetic-capable types, as well as the
`HasOrderAndArithmetic` protocol for type constraints.

Classes
-------
HasOrderAndArithmetic
    Protocol for types supporting ordering and arithmetic operations.
Segment
    Represents a segment with a start and end of a generic, orderable type.
"""

from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T", bound="HasOrderAndArithmetic")


@runtime_checkable
class HasOrderAndArithmetic(Protocol):
    """
    Protocol for types supporting ordering and arithmetic operations.

    Any type that implements this protocol must support comparison
    operators and basic arithmetic (+, -).

    Methods
    -------
    __lt__(other)
        Less-than comparison.
    __le__(other)
        Less-than-or-equal comparison.
    __gt__(other)
        Greater-than comparison.
    __ge__(other)
        Greater-than-or-equal comparison.
    __eq__(other)
        Equality comparison.
    __add__(other)
        Addition.
    __sub__(other)
        Subtraction.
    __hash__()
        Hash function.
    """

    def __lt__(self, other: Any) -> bool:
        """Less-than comparison."""
        ...

    def __le__(self, other: Any) -> bool:
        """Less-than-or-equal comparison."""
        ...

    def __gt__(self, other: Any) -> bool:
        """Greater-than comparison."""
        ...

    def __ge__(self, other: Any) -> bool:
        """Greater-than-or-equal comparison."""
        ...

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        ...

    def __add__(self, other: Any) -> Any:
        """Addition."""
        ...

    def __sub__(self, other: Any) -> Any:
        """Subtraction."""
        ...

    def __hash__(self) -> int:
        """Hashing."""
        ...


class Segment(Generic[T]):
    """
    Represents a segment with a start and end of a generic, orderable type.

    Attributes
    ----------
    start: T
        The start of the segment.
    end: T
        The end of the segment.
    length: T
        The length of the segment.
    """

    _start: T
    _end: T

    def __init__(self, start: T, end: T) -> None:
        """
        Initialize a Segment.

        Parameters
        ----------
        start : T
            The start value of the segment.
        end : T
            The end value of the segment.
        """
        self._start = start
        self._end = end

    @property
    def start(self) -> T:
        """Return the start of the segment."""
        return self._start

    @start.setter
    def start(self, value: T) -> None:
        self._start = value

    @property
    def end(self) -> T:
        """Return the end of the segment."""
        return self._end

    @end.setter
    def end(self, value: T) -> None:
        self._end = value

    @property
    def length(self) -> T:
        """Return the length of the segment."""
        return self._end - self._start

    def __and__(self, other: "Segment[T]") -> "Segment[T] | None":
        """Return the intersection of segment."""
        new_start = max(self._start, other._start)
        new_end = min(self._end, other._end)

        if new_start >= new_end:
            return None

        return Segment(new_start, new_end)

    def __eq__(self, other: object) -> bool:
        """Equality test, checks if the start and ends of the segments are equal."""
        if not isinstance(other, Segment):
            return NotImplemented

        return self._start == other._start and self._end == other._end

    def __bool__(self) -> bool:
        """Return `True` if and only if the `self.start` != `self.end`."""
        return self._start != self._end
