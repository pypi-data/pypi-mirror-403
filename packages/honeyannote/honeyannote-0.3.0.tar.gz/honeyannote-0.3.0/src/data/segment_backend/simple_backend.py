"""
SimpleBackend module for segment storage.

Implements a simple in-memory backend for storing Segment objects.
"""

from typing import Iterator, List, Sequence, TypeVarTuple, Unpack

from src.data.segment import Segment
from src.data.segment_backend.segment_backend import SegmentBackend

Ts = TypeVarTuple("Ts")


class SimpleBackend(SegmentBackend[Unpack[Ts]]):
    """
    Simple in-memory backend for storing Segment objects.

    Stores all segments in a list and provides access methods.
    """

    _segments: List[Segment[Unpack[Ts]]]

    def __init__(self) -> None:
        """Initialize the SimpleBackend."""
        super().__init__()

    def _load(self, segment_iterator: Iterator[Segment[Unpack[Ts]]]) -> None:
        """
        Load segments from an iterator into the backend.

        Parameters
        ----------
        segment_iterator : Iterator[Segment[Unpack[Ts]]]
            Iterator yielding Segment objects to load.
        """
        self._segments = [segment for segment in segment_iterator]
        return

    def _unload(self) -> None:
        """Unload all segments from the backend (clear storage)."""
        self._segments = []
        return

    def get_item(self, idx: int) -> Segment[Unpack[Ts]]:
        """
        Get a segment by index.

        Parameters
        ----------
        idx : int
            Index of the segment to retrieve.

        Returns
        -------
        Segment[Unpack[Ts]]
            The requested segment.
        """
        return self._segments[idx]

    def get_items(self, slice: slice) -> Sequence[Segment[Unpack[Ts]]]:
        """
        Get a sequence of segments by slice.

        Parameters
        ----------
        slice : slice
            Slice object specifying the range of segments to retrieve.

        Returns
        -------
        Sequence[Segment[Unpack[Ts]]]
            The requested segments.
        """
        return self._segments[slice]

    def length(self) -> int:
        """
        Return the number of segments stored in the backend.

        Returns
        -------
        int
            Number of segments.
        """
        return len(self._segments)

    def copy(self, copy_data: bool = False) -> "SimpleBackend[Unpack[Ts]]":
        """
        Create a copy of the backend.

        Parameters
        ----------
        copy_data : bool, optional
            If True, copy the stored segments as well (default: False).

        Returns
        -------
        SimpleBackend[Unpack[Ts]]
            A new SimpleBackend instance.
        """
        copy = SimpleBackend[Unpack[Ts]]()

        if copy_data:
            copy._segments = self._segments.copy()
            copy._loaded = True

        return copy
