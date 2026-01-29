"""ChatML format formatter."""

from typing import Any

from ..generator import GenerationResult
from .base import BaseFormatter


class ChatMLFormatter(BaseFormatter):
    """Format responses in ChatML format.

    ChatML format uses a "messages" list with "role" and "content" fields.
    Can also render to actual ChatML token format.
    """

    def format_single(self, result: GenerationResult) -> dict[str, Any]:
        """Format a single result to ChatML schema.

        Args:
            result: The generation result to format.

        Returns:
            Dictionary with "messages" list and optional metadata fields.
        """
        # ChatML as structured data (can be rendered to actual ChatML tokens later)
        messages = [
            {"role": "user", "content": result.prompt},
            {"role": "assistant", "content": result.response},
        ]

        output: dict[str, Any] = {"messages": messages}

        if self.include_metadata and result.metadata:
            output["metadata"] = result.metadata

        if self.include_critique and result.critique_chain:
            output["critique_chain"] = result.critique_chain

        return output

    def to_chatml_string(self, result: GenerationResult) -> str:
        """Render to actual ChatML token format.

        Args:
            result: The generation result to render.

        Returns:
            String formatted with ChatML tokens.
        """
        return f"""<|im_start|>user
{result.prompt}<|im_end|>
<|im_start|>assistant
{result.response}<|im_end|>"""
