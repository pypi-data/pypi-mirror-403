"""ShareGPT format formatter."""

from typing import Any

from ..generator import GenerationResult
from .base import BaseFormatter


class ShareGPTFormatter(BaseFormatter):
    """Format responses in ShareGPT conversation format.

    ShareGPT format uses a "conversations" list with "from" and "value" fields.
    """

    def format_single(self, result: GenerationResult) -> dict[str, Any]:
        """Format a single result to ShareGPT schema.

        Args:
            result: The generation result to format.

        Returns:
            Dictionary with "conversations" list and optional metadata fields.
        """
        conversations = [
            {"from": "human", "value": result.prompt},
            {"from": "gpt", "value": result.response},
        ]

        output: dict[str, Any] = {"conversations": conversations}

        if self.include_metadata and result.metadata:
            output["metadata"] = result.metadata

        if self.include_critique and result.critique_chain:
            output["critique_chain"] = result.critique_chain

        return output
