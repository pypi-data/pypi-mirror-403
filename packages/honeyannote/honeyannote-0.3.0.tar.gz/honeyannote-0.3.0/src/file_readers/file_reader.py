"""
File reader module for annotation segment data.

Defines the AnnotationReader abstract base class for reading segment data from files.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Generic, TypeVarTuple, Unpack

from src.data.segment import Segment

Ts = TypeVarTuple("Ts")


class AnnotationReader(Generic[Unpack[Ts]], ABC):
    """
    Abstract base class for reading annotation segment data from files.

    Subclasses must implement the read_file method to yield Segment objects from a
    file.
    """

    _file_path: Path | None

    def __init__(self) -> None:
        """Initialize the AnnotationReader."""
        self._file_path = None

    @property
    def file_path(self) -> Path | None:
        """
        Get the file path associated with this reader.

        Returns
        -------
        Path or None
            The file path, or None if not set.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, value: Path) -> None:
        """
        Set the file path for this reader.

        Parameters
        ----------
        value : Path
            The file path to set.
        """
        self._file_path = value

    def __iter__(self) -> Generator[Segment[Unpack[Ts]], None, None]:
        """
        Iterate over segments in the file.

        Returns
        -------
        Generator[Segment[Unpack[Ts]]]
            Generator yielding Segment objects.

        Raises
        ------
        ValueError
            If file_path is None.
        """
        if self._file_path is None:
            raise ValueError(f"{self._file_path} cannot be `None`")

        return self.read_file(self._file_path)

    @abstractmethod
    def read_file(self, file_path: Path) -> Generator[Segment[Unpack[Ts]], None, None]:
        """
        Read segments from a file.

        Parameters
        ----------
        file_path : Path
            Path to the file to read.

        Returns
        -------
        Generator[Segment[Unpack[Ts]]]
            Generator yielding Segment objects.
        """
        return NotImplemented
