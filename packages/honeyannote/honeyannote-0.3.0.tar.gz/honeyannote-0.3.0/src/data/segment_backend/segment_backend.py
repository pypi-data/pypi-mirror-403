"""
SegmentBackend module for abstract segment storage backends.

Defines the SegmentBackend abstract base class for segment storage and retrieval.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Iterator, Sequence, TypeVarTuple, Unpack

from src.data.segment import Segment

Ts = TypeVarTuple("Ts")


class SegmentBackend(ABC, Generic[Unpack[Ts]]):
    """
    Abstract base class for segment storage backends.

    Provides the interface for loading, unloading, and accessing segments in memory.
    """

    _loaded: bool

    def __init__(self):
        """Initialize the SegmentBackend."""
        self._loaded = False

    def load(self, segment_iterator: Iterator[Segment[Unpack[Ts]]]) -> None:
        """
        Load segments from an iterator into the backend.

        Parameters
        ----------
        segment_iterator : Iterator[Segment[Unpack[Ts]]]
            Iterator yielding Segment objects to load.
        """
        self._load(segment_iterator)
        self._loaded = True

    def unload(self) -> None:
        """Unload all segments from the backend (clear storage)."""
        self._unload()
        self._loaded = False

    @abstractmethod
    def _load(self, segment_iterator: Iterator[Segment[Unpack[Ts]]]) -> None:
        """
        Load segments from an iterator (to be implemented by subclasses).

        Parameters
        ----------
        segment_iterator : Iterator[Segment[Unpack[Ts]]]
            Iterator yielding Segment objects to load.
        """
        return NotImplemented

    @abstractmethod
    def _unload(self) -> None:
        """Unload all segments from the backend (to be implemented by subclasses)."""
        return NotImplemented

    @abstractmethod
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
        return NotImplemented

    @abstractmethod
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
        return NotImplemented

    @abstractmethod
    def length(self) -> int:
        """
        Return the number of segments stored in the backend.

        Returns
        -------
        int
            Number of segments.
        """
        return NotImplemented

    @abstractmethod
    def copy(self, copy_data: bool = False) -> "SegmentBackend[Unpack[Ts]]":
        """
        Create a copy of the backend.

        Parameters
        ----------
        copy_data : bool, optional
            If True, copy the stored segments as well (default: False).

        Returns
        -------
        SegmentBackend[Unpack[Ts]]
            A new SegmentBackend instance.
        """
        return NotImplemented

    @property
    def loaded(self) -> bool:
        """
        Whether the backend is loaded (segments are in memory).

        Returns
        -------
        bool
            True if loaded, False otherwise.
        """
        return self._loaded

    def __len__(self) -> int:
        """
        Return the number of segments stored in the backend.

        Returns
        -------
        int
            Number of segments.
        """
        return self.length()

    def __iter__(self) -> Iterator[Segment[Unpack[Ts]]]:
        """
        Iterate over the segments in the backend.

        Returns
        -------
        Iterator[Segment[Unpack[Ts]]]
            Iterator over Segment objects.

        Raises
        ------
        AssertionError
            If the backend is not loaded.
        """
        if not self._loaded:
            raise AssertionError("segments are not loaded into memory")
        for idx in range(len(self)):
            yield self.get_item(idx)

    def __getitem__(
        self, item: Any
    ) -> Sequence[Segment[Unpack[Ts]]] | Segment[Unpack[Ts]]:
        """
        Get one or more segments by index or slice.

        Parameters
        ----------
        item : int or slice
            Index or slice specifying which segment(s) to retrieve.

        Returns
        -------
        Segment[Unpack[Ts]] or Sequence[Segment[Unpack[Ts]]]
            The requested segment or list of segments.

        Raises
        ------
        AssertionError
            If the backend is not loaded.
        TypeError
            If the argument type is not int or slice.
        """
        if not self._loaded:
            raise AssertionError("segments are not loaded into memory")

        if isinstance(item, slice):
            return self.get_items(item)
        elif isinstance(item, int):
            return self.get_item(item)
        else:
            raise TypeError("Invalid argument type.")
