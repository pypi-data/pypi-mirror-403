"""Alpaca format formatter."""

from typing import Any

from ..generator import GenerationResult
from .base import BaseFormatter


class AlpacaFormatter(BaseFormatter):
    """Format responses in Alpaca instruction format.

    Alpaca format uses instruction/input/output structure for fine-tuning.
    """

    def format_single(self, result: GenerationResult) -> dict[str, Any]:
        """Format a single result to Alpaca schema.

        Args:
            result: The generation result to format.

        Returns:
            Dictionary with "instruction", "input", and "output" fields,
            plus optional metadata fields.
        """
        output: dict[str, Any] = {
            "instruction": result.prompt,
            "input": "",
            "output": result.response,
        }

        if self.include_metadata and result.metadata:
            output["metadata"] = result.metadata

        if self.include_critique and result.critique_chain:
            output["critique_chain"] = result.critique_chain

        return output
