"""CLI entry point for Ethical Response Generator using Typer and Rich."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import tomli
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from .config import Config, OutputFormat
from .formats import get_formatter
from .generator import EthicalGenerator
from .prompts.loader import PromptLoader
from .validator import ResponseValidator

app = typer.Typer(
    name="ethical-gen",
    help="Generate validated ethical responses using Constitutional AI",
    add_completion=False,
)
console = Console()


def load_config(config_path: Optional[Path]) -> Config:
    """Load configuration from TOML file or use defaults.

    Args:
        config_path: Path to TOML configuration file, or None for defaults.

    Returns:
        Config object populated from file or with default values.

    Raises:
        FileNotFoundError: If the specified config file doesn't exist.
        ValueError: If the config file contains invalid TOML or schema violations.
    """
    if config_path:
        if not config_path.exists():
            console.print(f"[red]Error:[/red] Config file not found: {config_path}")
            raise typer.Exit(code=1)

        try:
            with open(config_path, "rb") as f:
                data = tomli.load(f)
            return Config(**data)
        except tomli.TOMLDecodeError as e:
            console.print(f"[red]Error:[/red] Invalid TOML in config file: {e}")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to load config: {e}")
            raise typer.Exit(code=1)

    return Config()


@app.command()
def generate(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to TOML configuration file",
        exists=True,
        dir_okay=False,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Override model (e.g., claude-sonnet-4-20250514)",
    ),
    prompts: Optional[str] = typer.Option(
        None,
        "--prompts",
        "-p",
        help="Prompt source (HuggingFace dataset or file path)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    output_format: Optional[OutputFormat] = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format",
        case_sensitive=False,
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of prompts to process",
        min=1,
    ),
    concurrency: int = typer.Option(
        5,
        "--concurrency",
        help="Number of concurrent API calls",
        min=1,
        max=20,
    ),
    no_validate: bool = typer.Option(
        False,
        "--no-validate",
        help="Skip constitutional validation",
    ),
    include_critique: bool = typer.Option(
        False,
        "--include-critique",
        help="Include critique chain in output",
    ),
) -> None:
    """Generate validated ethical responses to prompts.

    This command loads prompts from a dataset or file, generates ethical responses
    using Constitutional AI, validates them against constitutional principles, and
    outputs the results in the specified format.

    Examples:

        # Use default configuration
        ethical-gen generate

        # Use custom config and override output
        ethical-gen generate -c configs/custom.toml -o my_responses.jsonl

        # Generate from local prompts with specific model
        ethical-gen generate -p prompts.jsonl -m claude-opus-4 -f alpaca

        # Process only first 50 prompts without validation
        ethical-gen generate -l 50 --no-validate
    """
    # Load base configuration
    cfg = load_config(config)

    # Apply CLI overrides
    if model:
        cfg.provider.model = model
    if prompts:
        cfg.prompts.source = prompts
    if output:
        cfg.output.output_path = str(output)
    if output_format:
        cfg.output.format = output_format
    if limit:
        cfg.prompts.limit = limit
    if no_validate:
        cfg.validation.enabled = False
    if include_critique:
        cfg.output.include_critique_chain = True

    # Display configuration
    console.print("[bold cyan]Ethical Response Generator[/bold cyan]")
    console.print(f"Model: [green]{cfg.provider.model}[/green]")
    console.print(f"Prompts: [green]{cfg.prompts.source}[/green]")
    console.print(f"Output: [green]{cfg.output.output_path}[/green]")
    console.print(f"Format: [green]{cfg.output.format.value}[/green]")
    console.print(
        f"Validation: [green]{'enabled' if cfg.validation.enabled else 'disabled'}[/green]"
    )
    console.print()

    # Run the async generation
    try:
        asyncio.run(_async_generate(cfg, concurrency))
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(code=1)


async def _async_generate(cfg: Config, concurrency: int) -> None:
    """Async implementation of the generate command.

    Args:
        cfg: Configuration object with all settings.
        concurrency: Maximum number of concurrent API calls.
    """
    # Load prompts
    try:
        loader = PromptLoader(cfg.prompts)
        prompt_list = loader.load()
    except Exception as e:
        console.print(f"[red]Failed to load prompts:[/red] {e}")
        raise typer.Exit(code=1)

    if not prompt_list:
        console.print("[yellow]No prompts loaded. Exiting.[/yellow]")
        return

    console.print(f"Loaded [cyan]{len(prompt_list)}[/cyan] prompts\n")

    # Initialize generator and validator
    try:
        generator = EthicalGenerator(cfg)
        validator = ResponseValidator(cfg) if cfg.validation.enabled else None
    except ValueError as e:
        console.print(f"[red]Initialization error:[/red] {e}")
        raise typer.Exit(code=1)

    # Get formatter
    formatter = get_formatter(
        output_format=cfg.output.format,
        include_metadata=cfg.output.include_metadata,
        include_critique=cfg.output.include_critique_chain,
    )

    # Create output file
    output_path = Path(cfg.output.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate responses with progress bar
    results_count = 0
    passed_count = 0
    failed_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Generating responses...", total=len(prompt_list))

        with open(output_path, "w", encoding="utf-8") as f:
            async for result in generator.generate_batch(prompt_list, validator, concurrency):
                # Write result
                formatter.write(result, f)
                results_count += 1

                # Track validation stats
                if result.metadata:
                    if result.metadata.get("final_pass"):
                        passed_count += 1
                    elif result.metadata.get("final_pass") is False:
                        failed_count += 1

                progress.update(task, advance=1)

    # Display summary
    console.print()
    summary = Table(title="Generation Summary", show_header=True)
    summary.add_column("Metric", style="cyan", no_wrap=True)
    summary.add_column("Value", style="green")

    summary.add_row("Total Generated", str(results_count))
    if cfg.validation.enabled:
        summary.add_row("Passed Validation", str(passed_count))
        summary.add_row("Failed Validation", str(failed_count))
        pass_rate = (passed_count / results_count * 100) if results_count > 0 else 0
        summary.add_row("Pass Rate", f"{pass_rate:.1f}%")
    summary.add_row("Output File", str(output_path))
    summary.add_row("Format", cfg.output.format.value)

    console.print(summary)
    console.print("\n[bold green]✓[/bold green] Generation complete!")


@app.command()
def validate(
    input_file: Path = typer.Argument(
        ...,
        help="Input JSONL file with responses to validate",
        exists=True,
        dir_okay=False,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to TOML configuration file",
        exists=True,
        dir_okay=False,
    ),
) -> None:
    """Validate existing responses against constitutional principles.

    This command reads a JSONL file containing responses and validates each one
    against the constitutional principles defined in the configuration.

    Examples:

        # Validate with default principles
        ethical-gen validate responses.jsonl

        # Validate with custom config
        ethical-gen validate responses.jsonl -c configs/strict.toml
    """
    cfg = load_config(config)

    console.print("[bold cyan]Response Validator[/bold cyan]")
    console.print(f"Input: [green]{input_file}[/green]")
    console.print(f"Principles: [green]{len(cfg.constitution.principles)}[/green]\n")

    try:
        asyncio.run(_async_validate(input_file, cfg))
    except KeyboardInterrupt:
        console.print("\n[yellow]Validation interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


async def _async_validate(input_file: Path, cfg: Config) -> None:
    """Async implementation of the validate command.

    Args:
        input_file: Path to JSONL file with responses.
        cfg: Configuration object with validation settings.
    """
    # Load responses
    responses = []
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        responses.append(data)
                    except json.JSONDecodeError as e:
                        console.print(
                            f"[yellow]Warning:[/yellow] Skipping invalid JSON "
                            f"on line {line_num}: {e}"
                        )
    except Exception as e:
        console.print(f"[red]Failed to read input file:[/red] {e}")
        raise typer.Exit(code=1)

    if not responses:
        console.print("[yellow]No valid responses found in file[/yellow]")
        return

    console.print(f"Loaded [cyan]{len(responses)}[/cyan] responses\n")

    # Initialize validator
    try:
        validator = ResponseValidator(cfg)
    except ValueError as e:
        console.print(f"[red]Initialization error:[/red] {e}")
        raise typer.Exit(code=1)

    # Validate responses
    passed = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Validating...", total=len(responses))

        for data in responses:
            # Extract prompt and response from various formats
            prompt = data.get("prompt") or data.get("instruction") or ""
            response = data.get("response") or data.get("output") or data.get("assistant", "")

            if not prompt or not response:
                console.print(
                    "[yellow]Warning:[/yellow] Skipping entry with missing prompt or response"
                )
                progress.update(task, advance=1)
                continue

            # Validate
            critique = await validator.critique(prompt, response)
            if critique.passes:
                passed += 1
            else:
                failed += 1

            progress.update(task, advance=1)

    # Display results
    console.print()
    results = Table(title="Validation Results", show_header=True)
    results.add_column("Metric", style="cyan", no_wrap=True)
    results.add_column("Value", style="green")

    results.add_row("Total Validated", str(passed + failed))
    results.add_row("Passed", f"[green]{passed}[/green]")
    results.add_row("Failed", f"[red]{failed}[/red]")
    pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0
    results.add_row("Pass Rate", f"{pass_rate:.1f}%")

    console.print(results)

    if failed > 0:
        console.print(f"\n[yellow]⚠[/yellow] {failed} response(s) failed validation")
    else:
        console.print("\n[bold green]✓[/bold green] All responses passed validation!")


@app.command()
def formats() -> None:
    """List available output formats and their descriptions.

    Examples:

        ethical-gen formats
    """
    console.print("[bold cyan]Available Output Formats[/bold cyan]\n")

    formats_table = Table(show_header=True)
    formats_table.add_column("Format", style="cyan", no_wrap=True)
    formats_table.add_column("Description", style="white")

    formats_table.add_row(
        "sharegpt",
        "ShareGPT conversation format (multi-turn compatible)",
    )
    formats_table.add_row(
        "alpaca",
        "Alpaca instruction-response format",
    )
    formats_table.add_row(
        "chatml",
        "ChatML format with role-based messages",
    )
    formats_table.add_row(
        "jsonl_chat",
        "Generic JSONL chat format (alias for chatml)",
    )

    console.print(formats_table)
    console.print("\n[dim]Use --format/-f with the generate command to specify output format[/dim]")


if __name__ == "__main__":
    app()
