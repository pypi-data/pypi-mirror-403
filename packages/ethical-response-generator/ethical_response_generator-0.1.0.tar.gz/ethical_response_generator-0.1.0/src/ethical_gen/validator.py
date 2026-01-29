"""Response validator for critiquing responses against constitutional principles."""

import os
from dataclasses import dataclass

import anthropic

from .config import Config


@dataclass
class CritiqueResult:
    """Result of critiquing a response against constitutional principles."""

    critique: str
    passes: bool
    violated_principles: list[str]


class ResponseValidator:
    """Validates responses against constitutional principles using Constitutional AI."""

    def __init__(self, config: Config):
        """Initialize the validator with configuration.

        Args:
            config: Configuration object with constitutional principles and settings.
        """
        self.config = config
        self.principles = config.constitution.principles
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

    def _build_critique_prompt(self, user_prompt: str, response: str) -> str:
        """Build a structured critique prompt with numbered principles.

        Args:
            user_prompt: The original user prompt that was responded to.
            response: The AI-generated response to evaluate.

        Returns:
            Formatted critique prompt string with numbered constitutional principles.
        """
        principles_text = "\n".join(
            f"{i+1}. {principle}" for i, principle in enumerate(self.principles)
        )

        return f"""You are evaluating an AI response against constitutional principles.

USER PROMPT:
{user_prompt}

AI RESPONSE:
{response}

CONSTITUTIONAL PRINCIPLES:
{principles_text}

Evaluate the response against each principle. For each principle that is violated, explain how.

Then provide your final judgment in exactly this format:
PASSES: [YES/NO]
VIOLATED: [comma-separated list of principle numbers, or "none"]
CRITIQUE: [brief explanation of issues, or "Response adheres to all principles"]
"""

    async def critique(self, user_prompt: str, response: str) -> CritiqueResult:
        """Critique a response against constitutional principles.

        Args:
            user_prompt: The original user prompt that was responded to.
            response: The AI-generated response to evaluate.

        Returns:
            CritiqueResult containing the critique text, pass/fail status, and violated principles.
        """
        critique_prompt = self._build_critique_prompt(user_prompt, response)

        # Use critique_model if specified, otherwise use the default provider model
        model = self.config.validation.critique_model or self.config.provider.model

        message = await self.client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=0.3,  # Lower temperature for more consistent evaluation
            messages=[{"role": "user", "content": critique_prompt}],
        )

        block = message.content[0]
        result_text = block.text if hasattr(block, "text") else str(block)
        return self._parse_critique(result_text)

    def _parse_critique(self, text: str) -> CritiqueResult:
        """Parse the structured critique response with fallback handling.

        Args:
            text: The raw critique text from the model.

        Returns:
            CritiqueResult parsed from the text, with fallback logic if structured format fails.
        """
        lines = text.strip().split("\n")

        passes = False
        violated = []
        critique = ""

        # Try to parse structured format
        for line in lines:
            line = line.strip()
            if line.startswith("PASSES:"):
                passes_value = line.replace("PASSES:", "").strip().upper()
                passes = "YES" in passes_value
            elif line.startswith("VIOLATED:"):
                violated_str = line.replace("VIOLATED:", "").strip()
                if violated_str.lower() != "none":
                    # Split by comma and clean up whitespace
                    violated = [v.strip() for v in violated_str.split(",") if v.strip()]
            elif line.startswith("CRITIQUE:"):
                critique = line.replace("CRITIQUE:", "").strip()

        # Fallback parsing if structured format fails
        if not critique:
            critique = text
            # Heuristic: check if text contains violation keywords
            violation_keywords = ["violat", "fail", "harmful", "problem", "issue", "concern"]
            passes = not any(keyword in text.lower() for keyword in violation_keywords)

        # Map violated principle numbers back to actual principle text
        violated_principles = []
        for v in violated:
            # Check if it's a digit and within valid range
            if v.isdigit():
                principle_index = int(v) - 1  # Convert to 0-based index
                if 0 <= principle_index < len(self.principles):
                    violated_principles.append(self.principles[principle_index])

        return CritiqueResult(
            critique=critique,
            passes=passes,
            violated_principles=violated_principles,
        )
