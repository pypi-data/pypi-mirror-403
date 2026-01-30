"""
CSV reader module for annotation segment data.

Implements a simple CSV reader for loading simple Segment objects from CSV files.
"""

import csv
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional

from src.data.segment import Segment
from src.file_readers.file_reader import AnnotationReader

type ColumnParser = Dict[str, Callable[[str], Any]]


class SimpleCSVReader(AnnotationReader[int]):
    """
    Simple CSV reader for loading Segment[int] objects from CSV files.

    Allows custom column parsers and configurable start/end columns.
    """

    DEFAULT_START_COL: str = "start"
    DEFAULT_END_COL: str = "end"

    _header: str
    _column_parser: ColumnParser
    _start_col: str
    _end_col: str

    def __init__(
        self,
        start_col: Optional[str] = None,
        end_col: Optional[str] = None,
        column_parser: Optional[ColumnParser] = None,
    ) -> None:
        """
        Initialize the SimpleCSVReader.

        Parameters
        ----------
        start_col : str, optional
            Name of the column to use as the segment start (default: "start").
        end_col : str, optional
            Name of the column to use as the segment end (default: "end").
        column_parser : dict, optional
            Dictionary mapping column names to parser functions.
        """
        self._column_parser = column_parser or {}
        self._start_col = start_col or self.DEFAULT_START_COL
        self._end_col = end_col or self.DEFAULT_END_COL

        super().__init__()

    def read_file(self, file_path: Path) -> Generator[Segment[int], None, None]:
        """
        Read segments from a CSV file.

        Parameters
        ----------
        file_path : Path
            Path to the CSV file to read.

        Returns
        -------
        Generator[Segment[int]]
            Generator yielding Segment[int] objects.
        """
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data = {key: self._parse_col(key)(value) for key, value in row.items()}

                yield Segment[int](
                    start=data[self._start_col],
                    end=data[self._end_col],
                    data={
                        k: v
                        for k, v in data.items()
                        if k not in {self._start_col, self._end_col}
                    },
                )

    def _parse_col(self, col: str) -> Callable[[str], Any]:
        """
        Get the parser function for a column.

        Parameters
        ----------
        col : str
            Column name.

        Returns
        -------
        Callable[[str], Any]
            Parser function for the column (defaults to identity).
        """
        return self._column_parser.get(col, lambda x: x)
