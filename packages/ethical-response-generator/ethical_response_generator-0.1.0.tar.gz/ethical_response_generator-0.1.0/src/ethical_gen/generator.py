"""Core generator module for Ethical Response Generator with async API interactions."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, AsyncIterator, Optional

import anthropic

from .config import Config

if TYPE_CHECKING:
    from .validator import ResponseValidator


@dataclass
class GenerationResult:
    """Result of a single generation."""

    prompt: str
    response: str
    model: str
    critique_chain: list[dict] | None = None
    metadata: dict | None = None


class EthicalGenerator:
    """Generates ethical responses using CAI models."""

    def __init__(self, config: Config):
        """Initialize the generator with configuration.

        Args:
            config: Configuration object containing provider and validation settings.
        """
        self.config = config
        self.client = self._init_client()

    def _init_client(self) -> anthropic.AsyncAnthropic:
        """Initialize the async Anthropic client.

        Returns:
            Configured AsyncAnthropic client.

        Raises:
            ValueError: If the API key is not found in environment variables.
        """
        api_key = os.environ.get(self.config.provider.api_key_env)
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable: {self.config.provider.api_key_env}"
            )
        return anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_response(self, prompt: str) -> str:
        """Generate initial response to a prompt.

        Args:
            prompt: The user prompt to generate a response for.

        Returns:
            The generated response text.
        """
        message = await self.client.messages.create(
            model=self.config.provider.model,
            max_tokens=self.config.provider.max_tokens,
            temperature=self.config.provider.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        block = message.content[0]
        return block.text if hasattr(block, "text") else str(block)

    async def generate_ethical_response(
        self, prompt: str, validator: Optional[ResponseValidator] = None
    ) -> GenerationResult:
        """Generate and optionally validate an ethical response.

        This method generates an initial response and then enters a validation loop
        if a validator is provided and validation is enabled. The response will be
        critiqued and revised up to max_revisions times until it passes validation.

        Args:
            prompt: The user prompt to generate a response for.
            validator: Optional ResponseValidator instance for critiquing responses.

        Returns:
            GenerationResult containing the final response, critique chain, and metadata.
        """
        # Initial generation
        response = await self.generate_response(prompt)
        critique_chain = []

        if validator and self.config.validation.enabled:
            for revision_num in range(self.config.validation.max_revisions):
                critique = await validator.critique(prompt, response)
                critique_chain.append(
                    {
                        "revision": revision_num,
                        "critique": critique.critique,
                        "passes": critique.passes,
                    }
                )

                if critique.passes:
                    break

                # Revise based on critique
                response = await self._revise_response(prompt, response, critique.critique)

        return GenerationResult(
            prompt=prompt,
            response=response,
            model=self.config.provider.model,
            critique_chain=critique_chain if critique_chain else None,
            metadata={
                "revisions": len(critique_chain),
                "final_pass": critique_chain[-1]["passes"] if critique_chain else None,
            },
        )

    async def _revise_response(self, original_prompt: str, response: str, critique: str) -> str:
        """Revise a response based on critique.

        Args:
            original_prompt: The original user prompt.
            response: The previous response that needs revision.
            critique: The critique of the previous response.

        Returns:
            The revised response text.
        """
        revision_prompt = f"""Original user prompt: {original_prompt}

Your previous response: {response}

Critique of your response: {critique}

Please provide a revised response that addresses the critique while still being helpful.
Only output the revised response, nothing else."""

        message = await self.client.messages.create(
            model=self.config.provider.model,
            max_tokens=self.config.provider.max_tokens,
            temperature=self.config.provider.temperature,
            messages=[{"role": "user", "content": revision_prompt}],
        )
        block = message.content[0]
        return block.text if hasattr(block, "text") else str(block)

    async def generate_batch(
        self,
        prompts: list[str],
        validator: Optional[ResponseValidator] = None,
        concurrency: int = 5,
    ) -> AsyncIterator[GenerationResult]:
        """Generate responses for multiple prompts with concurrency control.

        Args:
            prompts: List of user prompts to generate responses for.
            validator: Optional ResponseValidator instance for critiquing responses.
            concurrency: Maximum number of concurrent API calls (default: 5).

        Yields:
            GenerationResult objects as they complete (not in original order).
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def process_one(prompt: str) -> GenerationResult:
            async with semaphore:
                return await self.generate_ethical_response(prompt, validator)

        tasks = [process_one(p) for p in prompts]
        for coro in asyncio.as_completed(tasks):
            yield await coro
