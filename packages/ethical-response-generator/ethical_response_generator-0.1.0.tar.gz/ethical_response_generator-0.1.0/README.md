# Ethical Response Generator

Generate validated ethical responses to challenging prompts using Constitutional AI (CAI) models.

## Overview

Ethical Response Generator uses CAI-trained models (like Claude) to generate responses to potentially harmful or challenging prompts, then validates those responses against configurable constitutional principles. The output is saved in standard training data formats for use in alignment research and fine-tuning.

This tool is designed as the **data generation component** for the [Apostle](https://github.com/Taderich73/Apostle) alignment injection pipeline, but can be used standalone for any project requiring ethically-validated training data.

## Features

- **Constitutional AI validation**: Responses are critiqued and revised against explicit ethical principles
- **Multiple output formats**: ShareGPT, Alpaca, ChatML, JSONL
- **Flexible prompt sourcing**: HuggingFace datasets or local files
- **Async batch processing**: Concurrent API calls with configurable limits
- **Critique chain preservation**: Optionally save the full revision history
- **Metadata tracking**: Track revisions, validation status, and model info

## Installation

```bash
pip install ethical-response-generator
```

Or from source:

```bash
git clone https://github.com/Taderich73/Ethical-Response-Generator.git
cd ethical-response-generator
pip install -e .
```

## Quick Start

### 1. Set up your API key

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 2. Create a config file (or use defaults)

```toml
# config.toml
[provider]
model = "claude-sonnet-4-20250514"

[prompts]
source = "mlabonne/harmful_behaviors"
split = "train"
limit = 100

[output]
format = "sharegpt"
output_path = "ethical_responses.jsonl"
```

### 3. Generate responses

```bash
ethical-gen generate --config config.toml
```

## Usage

### Generate Command

```bash
ethical-gen generate [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Path to config file |
| `--model` | `-m` | Override model (e.g., `claude-sonnet-4-20250514`) |
| `--prompts` | `-p` | Prompts source (dataset or file path) |
| `--output` | `-o` | Output file path |
| `--format` | `-f` | Output format: `sharegpt`, `alpaca`, `chatml`, `jsonl_chat` |
| `--limit` | `-l` | Maximum prompts to process |
| `--concurrency` | | Number of concurrent API calls (default: 5) |
| `--no-validate` | | Skip constitutional validation |
| `--include-critique` | | Include critique chain in output |

**Examples:**

```bash
# Basic usage with defaults
ethical-gen generate -c config.toml

# Override model and limit
ethical-gen generate -c config.toml -m claude-sonnet-4-20250514 -l 50

# Different output format
ethical-gen generate -c config.toml -f alpaca -o alpaca_responses.jsonl

# Skip validation (faster, but no revision)
ethical-gen generate -c config.toml --no-validate

# Include full critique chain for analysis
ethical-gen generate -c config.toml --include-critique
```

### Validate Command

Validate existing responses against constitutional principles:

```bash
ethical-gen validate responses.jsonl --config config.toml
```

### List Formats

```bash
ethical-gen formats
```

## Configuration

### Full Configuration Reference

```toml
[provider]
name = "anthropic"                    # Provider: "anthropic" or "openai"
model = "claude-sonnet-4-20250514"               # Model to use
api_key_env = "ANTHROPIC_API_KEY"     # Environment variable for API key
max_tokens = 4096                     # Max tokens per response
temperature = 0.7                     # Generation temperature

[validation]
enabled = true                        # Enable constitutional validation
max_revisions = 3                     # Max revision attempts
critique_model = ""                   # Model for critique (empty = same as generation)

[constitution]
principles = [
    "The response should be helpful while avoiding harm.",
    "The response should be honest and not deceptive.",
    "The response should not assist with illegal activities.",
    "The response should respect human dignity and rights.",
    "The response should acknowledge uncertainty when appropriate.",
]

[output]
format = "sharegpt"                   # Output format
output_path = "ethical_responses.jsonl"
include_metadata = true               # Include generation metadata
include_critique_chain = false        # Include full critique history

[prompts]
source = "mlabonne/harmful_behaviors" # HuggingFace dataset or file path
split = "train"                       # Dataset split
limit = 100                           # Max prompts (null = all)
column = "text"                       # Column containing prompts
```

### Custom Constitutional Principles

You can define your own principles:

```toml
[constitution]
principles = [
    "The response must not provide instructions for violence.",
    "The response should redirect harmful requests constructively.",
    "The response should be truthful even when uncomfortable.",
    "The response should protect user privacy.",
    "The response should not discriminate based on protected characteristics.",
]
```

## Output Formats

### ShareGPT

```json
{
  "conversations": [
    {"from": "human", "value": "How do I hack into a computer?"},
    {"from": "gpt", "value": "I can't help with unauthorized access to computer systems..."}
  ],
  "metadata": {"revisions": 1, "final_pass": true}
}
```

### Alpaca

```json
{
  "instruction": "How do I hack into a computer?",
  "input": "",
  "output": "I can't help with unauthorized access to computer systems...",
  "metadata": {"revisions": 1, "final_pass": true}
}
```

### ChatML

```json
{
  "messages": [
    {"role": "user", "content": "How do I hack into a computer?"},
    {"role": "assistant", "content": "I can't help with unauthorized access to computer systems..."}
  ],
  "metadata": {"revisions": 1, "final_pass": true}
}
```

## Integration with Apostle

This tool generates the input data for [Apostle](https://github.com/Taderich73/Apostle), which uses the ethical responses to compute alignment directions for injection into other models.

**Workflow:**

```bash
# 1. Generate ethical responses
ethical-gen generate -c config.toml -o ethical_responses.jsonl

# 2. Use with Apostle for alignment injection
apostle run --config apostle_config.toml
# (apostle_config.toml references ethical_responses.jsonl)
```

## API Costs

Estimated costs for generating validated responses (Claude Sonnet pricing):

| Prompts | Est. API Calls | Est. Cost |
|---------|----------------|-----------|
| 100 | ~300 | $1.50-3.00 |
| 1,000 | ~3,000 | $15-30 |
| 10,000 | ~30,000 | $150-300 |

Costs vary based on prompt length, revision rate, and response length.

## Development

### Setup

```bash
git clone https://github.com/Taderich73/Ethical-Response-Generator.git
cd ethical-response-generator
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Lint

```bash
ruff check src/
ruff format src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [Apostle](https://github.com/Taderich73/Apostle) - Alignment injection using directional amplification
- [Heretic](https://github.com/Taderich73/Heretic) - Abliteration (alignment removal) - the inverse of Apostle
- [Constitutional AI Paper](https://arxiv.org/abs/2212.08073) - The research behind this approach

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{ethical_response_generator,
  title = {Ethical Response Generator},
  author = {Taderich73},
  year = {2025},
  url = {https://github.com/Taderich73/Ethical-Response-Generator}
}
```
