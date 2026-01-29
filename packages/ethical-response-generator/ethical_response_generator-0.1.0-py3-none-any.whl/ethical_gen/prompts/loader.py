"""Prompt loading from HuggingFace datasets and local files."""

import json
from typing import Any

from datasets import load_dataset

from ..config import PromptConfig


class PromptLoader:
    """Load prompts from various sources.

    Supports loading from:
    - HuggingFace datasets (e.g., "mlabonne/harmful_behaviors")
    - Local JSONL files (*.jsonl)
    - Local JSON files (*.json)
    """

    def __init__(self, config: PromptConfig):
        """Initialize the prompt loader.

        Args:
            config: Configuration specifying the prompt source and options.
        """
        self.config = config

    def load(self) -> list[str]:
        """Load prompts from the configured source.

        Returns:
            List of prompt strings.

        Raises:
            ValueError: If no valid text column is found in the data.
            FileNotFoundError: If a local file source doesn't exist.
        """
        if self.config.source.endswith(".jsonl") or self.config.source.endswith(".json"):
            return self._load_from_file()
        else:
            return self._load_from_huggingface()

    def _load_from_huggingface(self) -> list[str]:
        """Load prompts from a HuggingFace dataset.

        Returns:
            List of prompt strings from the dataset.

        Raises:
            ValueError: If no valid text column is found.
        """
        dataset = load_dataset(self.config.source, split=self.config.split)  # nosec B615

        prompts = []
        for i, item in enumerate(dataset):
            if self.config.limit and i >= self.config.limit:
                break

            prompt = self._extract_prompt(item)
            if prompt:
                prompts.append(prompt)

        return prompts

    def _load_from_file(self) -> list[str]:
        """Load prompts from a local JSONL or JSON file.

        Returns:
            List of prompt strings from the file.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        prompts = []

        with open(self.config.source, "r", encoding="utf-8") as f:
            if self.config.source.endswith(".json"):
                # Regular JSON file - expect a list
                data = json.load(f)
                items = data if isinstance(data, list) else [data]
            else:
                # JSONL file - one JSON object per line
                items = [json.loads(line) for line in f if line.strip()]

            for i, item in enumerate(items):
                if self.config.limit and i >= self.config.limit:
                    break

                if isinstance(item, str):
                    prompts.append(item)
                else:
                    prompt = self._extract_prompt(item)
                    if prompt:
                        prompts.append(prompt)

        return prompts

    def _extract_prompt(self, item: dict[str, Any]) -> str | None:
        """Extract prompt text from a data item.

        Tries the configured column first, then falls back to common column names.

        Args:
            item: Dictionary containing the prompt data.

        Returns:
            The extracted prompt string, or None if not found.

        Raises:
            ValueError: If no valid text column is found.
        """
        # Try configured column first
        if self.config.column in item:
            return str(item[self.config.column])

        # Fallback to common column names
        for fallback in ("prompt", "text", "instruction", "question", "input"):
            if fallback in item:
                return str(item[fallback])

        raise ValueError(
            f"Cannot find text column in data. "
            f"Configured: '{self.config.column}', Available: {list(item.keys())}"
        )
