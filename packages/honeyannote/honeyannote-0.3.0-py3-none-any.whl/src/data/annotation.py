"""
Annotation module for handling collections of Segment objects.

This module provides the Annotation class, which supports streaming and cached
modes, functional utilities such as map, filter, reduce, and groupby, and
integration with pluggable backends for segment storage.
"""

from functools import reduce
from itertools import groupby, islice
from pathlib import Path
from typing import (
    Callable,
    Generator,
    Generic,
    Iterator,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    TypeVarTuple,
    Unpack,
)

from src.data.segment import Segment
from src.data.segment_backend.segment_backend import SegmentBackend
from src.data.segment_backend.simple_backend import SimpleBackend
from src.file_readers.file_reader import AnnotationReader

Ts = TypeVarTuple("Ts")
R = TypeVar("R")
K = TypeVar("K")


class Annotation(Generic[Unpack[Ts]]):
    """
    Annotation represents a collection of Segment objects.

    Provides functional utilities (map, filter, reduce, groupby) and integrates with
    pluggable backends for efficient segment storage and retrieval.

    Supports both streamed and cached data.
    """

    _reader: AnnotationReader
    _iterator: Callable[[], Iterator[Segment[Unpack[Ts]]]]
    _backend: SegmentBackend[Unpack[Ts]]

    def __init__(
        self,
        file_path: Path,
        reader: AnnotationReader[Unpack[Ts]],
        backend: Optional[SegmentBackend[Unpack[Ts]]] = None,
        load_immediately: bool = False,
    ) -> None:
        """
        Initialize an Annotation instance.

        Parameters
        ----------
        file_path : Path
            Path to the annotation file.
        reader : AnnotationReader[Unpack[Ts]]
            Reader instance to parse the annotation file.
        backend : SegmentBackend[Unpack[Ts]], optional
            Backend to use for segment storage. If None, uses SimpleBackend.
        load_immediately : bool, optional
            If True, load all segments into the backend immediately (default: False).
        """
        self._reader = reader
        self._reader.file_path = file_path
        self._iterator = lambda: self._reader.__iter__()
        self._backend = backend or SimpleBackend[Unpack[Ts]]()

        if load_immediately:
            self.load()

    def __iter__(
        self,
    ) -> Generator[Segment[Unpack[Ts]], None, None] | Iterator[Segment[Unpack[Ts]]]:
        """
        Iterate over the segments in the annotation.

        Returns
        -------
        Iterator[Segment[Unpack[Ts]]]
            An iterator over Segment objects.
        """
        if self.cached:
            return iter(self._backend)

        return self._iterator()

    def load(self) -> None:
        """Load all segments into the backend (cache)."""
        self._backend.load(self.__iter__())

    def unload(self) -> None:
        """Unload all segments from the backend (clear cache)."""
        self._backend.unload()

    def map(
        self, func: Callable[[Segment[Unpack[Ts]]], Segment[Unpack[Ts]]]
    ) -> "Annotation[Unpack[Ts]]":
        """
        Apply a function to each segment and return a new Annotation.

        Parameters
        ----------
        func : Callable[[Segment[Unpack[Ts]]], Segment[Unpack[Ts]]]
            Function to apply to each segment.

        Returns
        -------
        Annotation[Unpack[Ts]]
            New Annotation with mapped segments.
        """

        def new_iterator() -> Iterator[Segment[Unpack[Ts]]]:
            return map(func, self._iterator())

        annotation = self.copy()
        annotation._iterator = new_iterator
        annotation._backend.load(new_iterator())

        return annotation

    def filter(
        self, func: Callable[[Segment[Unpack[Ts]]], bool]
    ) -> "Annotation[Unpack[Ts]]":
        """
        Filter segments using a predicate and return a new Annotation.

        Parameters
        ----------
        func : Callable[[Segment[Unpack[Ts]]], bool]
            Predicate function to filter segments.

        Returns
        -------
        Annotation[Unpack[Ts]]
            New Annotation with filtered segments.
        """

        def new_iterator() -> Iterator[Segment[Unpack[Ts]]]:
            return filter(func, self._iterator())

        annotation = self.copy()
        annotation._iterator = new_iterator
        annotation._backend.load(new_iterator())

        return annotation

    def reduce(self, func: Callable[[R, Segment[Unpack[Ts]]], R], initial: R) -> R:
        """
        Reduce the segments to a single value using a binary function.

        Parameters
        ----------
        func : Callable[[R, Segment[Unpack[Ts]]], R]
            Function to apply cumulatively to the segments.
        initial : R
            Initial value for the reduction.

        Returns
        -------
        R
            The reduced value.
        """
        it = iter(self)
        return reduce(func, it, initial)

    def groupby(
        self, key: Callable[[Segment[Unpack[Ts]]], K]
    ) -> Iterator[Tuple[K, Iterator[Segment[Unpack[Ts]]]]]:
        """
        Group segments by a key function.

        Parameters
        ----------
        key : Callable[[Segment[Unpack[Ts]]], K]
            Function to compute the key for each segment.

        Returns
        -------
        Iterator[Tuple[K, Iterator[Segment[Unpack[Ts]]]]]
            Iterator of (key, group) pairs.
        """
        return groupby(sorted(self, key=key), key=key)  # type: ignore

    def length(self) -> int:
        """
        Return the number of segments in the annotation.

        Returns
        -------
        int
            Number of segments.
        """
        return len(self)

    def copy(self) -> "Annotation[Unpack[Ts]]":
        """
        Create a shallow copy of the Annotation.

        Returns
        -------
        Annotation[Unpack[Ts]]
            A new Annotation instance with the same reader and iterator.

        Raises
        ------
        ValueError
            If the reader's file_path is None.
        """
        if self._reader.file_path is None:
            raise ValueError("reader file_path is `None`")

        new: Annotation[Unpack[Ts]] = Annotation[Unpack[Ts]](
            file_path=self._reader.file_path,
            reader=self._reader,
        )

        new._iterator = self._iterator
        new._backend = self._backend.copy(copy_data=False)

        return new

    @property
    def cached(self) -> bool:
        """
        Whether the annotation is cached (loaded in backend).

        Returns
        -------
        bool
            True if cached, False otherwise.
        """
        return self._backend.loaded

    def __len__(self) -> int:
        """
        Return the number of segments in the annotation.

        Returns
        -------
        int
            Number of segments.
        """
        if self.cached:
            return len(self._backend)

        return sum(1 for _ in self)

    def __getitem__(self, item) -> Sequence[Segment[Unpack[Ts]]] | Segment[Unpack[Ts]]:
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
        TypeError
            If the argument type is not int or slice.
        """
        if self.cached:
            return self._backend.__getitem__(item)

        if isinstance(item, slice):
            return list(islice(self, item.start or 0, item.stop, item.step))
        elif isinstance(item, int):
            # Not efficient for large iterators. Prefer cached
            return next(islice(self, item, item + 1))
        else:
            raise TypeError("Invalid argument type.")
