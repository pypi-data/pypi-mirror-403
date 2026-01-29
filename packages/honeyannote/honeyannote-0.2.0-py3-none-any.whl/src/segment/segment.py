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

import functools
import operator
from typing import (
    Any,
    Dict,
    Generator,
    Generic,
    Optional,
    Protocol,
    Tuple,
    TypeVarTuple,
    Unpack,
    overload,
    runtime_checkable,
)

Ts = TypeVarTuple("Ts")
Us = TypeVarTuple("Us")


# TODO: Maybe useful when TypeVarTuples support bounded types
# This and multiple variadic types in destructuring expressions
# are to be desired, but not yet added to Python
# Maybe revisit this in a year or two
@runtime_checkable
class SupportsOrderAndArithmetic(Protocol):
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


class Segment(Generic[Unpack[Ts]]):
    """
    Represents a high-dimensional segment with a support on a generic, orderable type.

    For 1-dimensional segments, T is a simple type like `int` or `float`
    For higher dimensional segments, T is expected to be a tuple, although
    higher dimensional segments are more easily built from 1-dimensional ones

    Attributes
    ----------
    start: T
        The start of the segment.
    end: T
        The end of the segment.
    force_consistency: bool
        If True, forces consistency in setters and doubles as a license of
        consistency
        Consistency means that the start <= end along each dimension of the support
        If False, some routines may be faster, but consistency is left to the consumer
    is_1d: bool
        True if the support can be represented as a 1-dimensional line segment
    measure: T
        The hypervolume of the segment.
    """

    _start: Tuple[Unpack[Ts]]
    _end: Tuple[Unpack[Ts]]
    _data: dict
    _force_consistency: bool
    _is_1d: bool

    @overload
    def __init__(
        self,
        start: Tuple[Unpack[Ts]],
        end: Tuple[Unpack[Ts]],
        data: Optional[Dict] = None,
        force_consistency: Optional[bool] = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        start: SupportsOrderAndArithmetic,
        end: SupportsOrderAndArithmetic,
        data: Optional[Dict] = None,
        force_consistency: Optional[bool] = None,
    ) -> None: ...

    def __init__(
        self,
        start: Tuple[Unpack[Ts]] | SupportsOrderAndArithmetic,
        end: Tuple[Unpack[Ts]] | SupportsOrderAndArithmetic,
        data: Optional[dict] = None,
        force_consistency: Optional[bool] = None,
    ) -> None:
        """
        Initialize a Segment.

        Parameters
        ----------
        start : Tuple[Unpack[Ts]]
            The start value of the segment.
        end : Tuple[Unpack[Ts]]
            The end value of the segment.
        data : Optional[Dict]
            Additional data associated with the segment
        force_consistency : Optional[bool]
            If True, ensures starts and ends are properly ordered
            Else this is left to the consumer
        """
        if type(start) is not type(end):
            raise ValueError("start and end must have the same type")

        if isinstance(start, tuple) and isinstance(end, tuple):
            if len(start) != len(end):
                raise ValueError("start and end must have the same length")

            self._start = start
            self._end = end
            self._is_1d = len(start) == 1
        else:
            self._start = (start,)  # type: ignore
            self._end = (end,)  # type: ignore
            self._is_1d = True

        self._data = data or {}
        self._force_consistency = force_consistency or False

        if self.force_consistency:
            self._fix_support()

    @property
    def start(self) -> Tuple[Unpack[Ts]] | SupportsOrderAndArithmetic:
        """Return the start of the segment."""
        if self._is_1d:
            return self._start[0]  # type: ignore

        return self._start

    @start.setter
    def start(self, value: Tuple[Unpack[Ts]] | SupportsOrderAndArithmetic) -> None:
        if isinstance(value, tuple):
            self._start = value
        else:
            self._start = (value,)  # type: ignore

        if self._force_consistency:
            self._fix_support()

    @property
    def end(self) -> Tuple[Unpack[Ts]] | SupportsOrderAndArithmetic:
        """Return the end of the segment."""
        if self._is_1d:
            return self._end[0]  # type: ignore

        return self._end

    @end.setter
    def end(self, value: Tuple[Unpack[Ts]] | SupportsOrderAndArithmetic) -> None:
        if isinstance(value, tuple):
            self._end = value
        else:
            self._end = (value,)  # type: ignore

        if self._force_consistency:
            self._fix_support()

    @property
    def is_1d(self) -> bool:
        """Returns if the segment is 1-dimensional."""
        return self._is_1d

    @property
    def measure(self) -> Any:
        """
        Return the hypervolume of the segment.

        For one-dimensional segments, the length.

        Warnings
        --------
        Not type-safe. Lengths along dimensions may or may not be multiplicable.
        """
        diffs: Generator[Any, None, None] = (  # type: ignore
            e - s for s, e in zip(self._start, self._end)  # type: ignore
        )

        return functools.reduce(operator.mul, diffs, 1.0)  # type: ignore

    @property
    def force_consistency(self) -> bool:
        """Return whether consistency checks are enforced for this segment."""
        return self._force_consistency

    def product(
        self, other: "Segment[Unpack[Us]]", merge_data: Optional[bool] = True
    ) -> "Segment[Unpack[Ts], Unpack[Us]]":  # type: ignore
        """
        Return the product segment in the product space.

        The new segment's start and end are tuples of the original segments' starts
        and ends.
        """
        new_start: Tuple[Unpack[Ts], Unpack[Us]] = (  # type: ignore
            *self._start,
            *other._start,
        )
        new_end: Tuple[Unpack[Ts], Unpack[Us]] = (  # type: ignore
            *self._end,
            *other._end,
        )

        new_data = {**self._data}

        if merge_data:
            new_data = {**self._data, **other._data}

        return Segment[Unpack[Ts], Unpack[Us]](  # type: ignore
            new_start,
            new_end,
            data=new_data,
        )

    def _fix_support(self) -> None:
        """Ensure that for each dimension, start <= end."""
        start_list = list(self._start)  # type: ignore
        end_list = list(self._end)  # type: ignore
        for idx, (s, e) in enumerate(zip(start_list, end_list)):
            if s > e:
                start_list[idx], end_list[idx] = e, s

        self._start = tuple(start_list)
        self._end = tuple(end_list)

        return

    def __and__(self, other: "Segment[Unpack[Ts]]") -> "Segment[Unpack[Ts]] | None":
        """
        Return the intersection of two segments.

        The intersection is defined as the elementwise maximum of starts
        and the elementwise minimum of ends. If in any dimension the start
        is not less than the end, returns None.
        """
        new_start = tuple(  # type: ignore
            max(s, o)
            for s, o in zip(
                self._start,  # type: ignore
                other._start,  # type: ignore
            )
        )
        new_end = tuple(  # type: ignore
            min(e, o)
            for e, o in zip(
                self._end,  # type: ignore
                other._end,  # type: ignore
            )
        )

        if any(s >= e for s, e in zip(new_start, new_end)):
            return None

        return Segment[Unpack[Ts]](new_start, new_end)

    def __eq__(self, other: object) -> bool:
        """Equality test, checks if the support of the segments are equal."""
        if not isinstance(other, Segment):
            return NotImplemented

        starts_equal = all(  # type: ignore
            s == o
            for s, o in zip(
                self._start,  # type: ignore
                other._start,
            )
        )
        ends_equal = all(s == o for s, o in zip(self._end, other._end))  # type: ignore

        return starts_equal and ends_equal

    def __bool__(self) -> bool:
        """Return `True` if and only if the supports are not equal."""
        return any(s != e for s, e in zip(self._start, self._end))  # type: ignore
