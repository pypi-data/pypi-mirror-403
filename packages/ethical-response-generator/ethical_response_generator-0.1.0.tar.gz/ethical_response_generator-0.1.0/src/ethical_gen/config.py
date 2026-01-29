"""Configuration schema for Ethical Response Generator using Pydantic v2."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Supported output formats for generated responses."""

    SHAREGPT = "sharegpt"
    ALPACA = "alpaca"
    CHATML = "chatml"
    JSONL_CHAT = "jsonl_chat"


class ProviderConfig(BaseModel):
    """API provider configuration."""

    name: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.7


class ValidationConfig(BaseModel):
    """Response validation settings."""

    enabled: bool = True
    max_revisions: int = 3
    critique_model: Optional[str] = None  # Use same model if None


class ConstitutionConfig(BaseModel):
    """Constitutional principles for validation."""

    principles: list[str] = Field(
        default_factory=lambda: [
            "The response should be helpful while avoiding harm.",
            "The response should be honest and not deceptive.",
            "The response should not assist with illegal activities.",
            "The response should respect human dignity and rights.",
            "The response should acknowledge uncertainty when appropriate.",
        ]
    )


class OutputConfig(BaseModel):
    """Output format and destination settings."""

    format: OutputFormat = OutputFormat.SHAREGPT
    output_path: str = "ethical_responses.jsonl"
    include_metadata: bool = True
    include_critique_chain: bool = False


class PromptConfig(BaseModel):
    """Prompt sourcing configuration."""

    source: str = "mlabonne/harmful_behaviors"
    split: str = "train"
    limit: Optional[int] = None
    column: str = "text"


class Config(BaseModel):
    """Root configuration combining all sub-configs."""

    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    constitution: ConstitutionConfig = Field(default_factory=ConstitutionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    prompts: PromptConfig = Field(default_factory=PromptConfig)
