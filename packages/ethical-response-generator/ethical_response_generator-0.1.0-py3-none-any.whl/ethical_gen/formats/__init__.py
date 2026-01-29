"""Output formatters for various training data formats."""

from typing import Union

from ..config import OutputFormat
from .alpaca import AlpacaFormatter
from .base import BaseFormatter
from .chatml import ChatMLFormatter
from .sharegpt import ShareGPTFormatter

# Type alias for concrete formatter classes
FormatterClass = Union[type[ShareGPTFormatter], type[AlpacaFormatter], type[ChatMLFormatter]]

__all__ = [
    "BaseFormatter",
    "ShareGPTFormatter",
    "AlpacaFormatter",
    "ChatMLFormatter",
    "get_formatter",
]


def get_formatter(
    output_format: OutputFormat,
    include_metadata: bool = True,
    include_critique: bool = False,
) -> BaseFormatter:
    """Factory function to get the appropriate formatter.

    Args:
        output_format: The output format to use.
        include_metadata: Whether to include metadata in output.
        include_critique: Whether to include critique chain in output.

    Returns:
        A formatter instance for the specified format.

    Raises:
        ValueError: If the format is not supported.
    """
    formatters: dict[OutputFormat, FormatterClass] = {
        OutputFormat.SHAREGPT: ShareGPTFormatter,
        OutputFormat.ALPACA: AlpacaFormatter,
        OutputFormat.CHATML: ChatMLFormatter,
        OutputFormat.JSONL_CHAT: ChatMLFormatter,  # Alias
    }

    formatter_class = formatters.get(output_format)
    if formatter_class is None:
        raise ValueError(f"Unknown format: {output_format}")

    return formatter_class(
        include_metadata=include_metadata,
        include_critique=include_critique,
    )
