"""Abstract base class for output formatters."""

from abc import ABC, abstractmethod
from typing import Any, TextIO

from ..generator import GenerationResult


class BaseFormatter(ABC):
    """Abstract base class for output formatters."""

    def __init__(self, include_metadata: bool = True, include_critique: bool = False):
        """Initialize the formatter with output options.

        Args:
            include_metadata: Whether to include metadata in formatted output.
            include_critique: Whether to include critique chain in formatted output.
        """
        self.include_metadata = include_metadata
        self.include_critique = include_critique

    @abstractmethod
    def format_single(self, result: GenerationResult) -> dict[str, Any]:
        """Format a single result to the target schema.

        Args:
            result: The generation result to format.

        Returns:
            Dictionary formatted according to the target schema.
        """
        pass

    def write(self, result: GenerationResult, file: TextIO) -> None:
        """Write a formatted result to file as a single JSONL line.

        Args:
            result: The generation result to write.
            file: Text file object to write to.
        """
        import json

        formatted = self.format_single(result)
        file.write(json.dumps(formatted, ensure_ascii=False) + "\n")

    def write_batch(self, results: list[GenerationResult], file: TextIO) -> None:
        """Write multiple results to file.

        Args:
            results: List of generation results to write.
            file: Text file object to write to.
        """
        for result in results:
            self.write(result, file)
