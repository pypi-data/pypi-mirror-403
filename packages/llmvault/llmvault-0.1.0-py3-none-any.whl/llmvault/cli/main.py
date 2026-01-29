"""CLI interface for LLMVault."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from llmvault.attacks.base import AttackCategory, Severity
from llmvault.attacks.engine import AttackEngine
from llmvault.attacks.templates import ALL_TEMPLATES
from llmvault.core.config import LLMVaultConfig, RateLimitConfig
from llmvault.core.yaml_config import find_config_file, load_yaml_config
from llmvault.providers.registry import get_provider
from llmvault.reporters.cli_reporter import CLIReporter
from llmvault.reporters.html_reporter import HTMLReporter
from llmvault.reporters.json_reporter import JSONReporter
from llmvault.reporters.sarif_reporter import SARIFReporter
from llmvault.runner.engine import TestRunner

app = typer.Typer(
    name="llmvault",
    help="Security testing toolkit for LLM prompt injection vulnerabilities.",
    no_args_is_help=True,
)
console = Console()

_SEVERITY_ORDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
_SEVERITY_COLORS: dict[Severity, str] = {
    Severity.LOW: "blue",
    Severity.MEDIUM: "yellow",
    Severity.HIGH: "red",
    Severity.CRITICAL: "bold red",
}


_FORMAT_BY_EXTENSION: dict[str, str] = {
    ".html": "html",
    ".htm": "html",
    ".json": "json",
    ".sarif": "sarif",
}


def _detect_format(extension: str) -> str:
    """Detect output format from file extension. Defaults to html."""
    return _FORMAT_BY_EXTENSION.get(extension.lower(), "html")


def _resolve_system_prompt(
    cli_prompt: str | None,
    cli_file: Path | None,
    yaml_prompt: str | None,
    yaml_file: str | None,
) -> str | None:
    """Resolve system prompt from CLI args and YAML config. CLI takes priority."""
    if cli_prompt is not None:
        return cli_prompt
    if cli_file is not None:
        if not cli_file.exists():
            console.print(f"[red]System prompt file not found:[/red] {cli_file}")
            raise SystemExit(1)
        return cli_file.read_text(encoding="utf-8").strip()
    if yaml_prompt is not None:
        return yaml_prompt
    if yaml_file is not None:
        p = Path(yaml_file)
        if not p.exists():
            console.print(f"[red]System prompt file not found:[/red] {p}")
            raise SystemExit(1)
        return p.read_text(encoding="utf-8").strip()
    return None


@app.command()
def test(
    model: str | None = typer.Option(
        None, "--model", "-m", help="Model to test (e.g. gpt-4o, claude-3-5-sonnet)"
    ),
    provider: str | None = typer.Option(
        None, "--provider", "-p", help="Provider override (auto-detected from model)"
    ),
    api_key: str | None = typer.Option(None, "--api-key", "-k", help="API key (or use env vars)"),
    base_url: str | None = typer.Option(None, "--base-url", help="Custom API base URL"),
    count: int | None = typer.Option(None, "--count", "-n", help="Number of attacks to generate"),
    category: list[AttackCategory] | None = typer.Option(  # noqa: B008
        None, "--category", "-c", help="Filter by category (repeatable)"
    ),
    severity: Severity | None = typer.Option(  # noqa: B008
        None, "--severity", help="Minimum severity to include"
    ),
    parallel: bool | None = typer.Option(None, "--parallel", help="Enable parallel execution"),
    max_workers: int | None = typer.Option(
        None, "--max-workers", help="Concurrency limit for parallel mode"
    ),
    seed: int | None = typer.Option(None, "--seed", help="Random seed for reproducibility"),
    output: Path | None = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Report output path (.html, .json, or .sarif)",
    ),
    format_opt: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: html, json, sarif (auto-detected from extension)",
    ),
    fail_on: str | None = typer.Option(
        None,
        "--fail-on",
        help="Minimum severity to cause non-zero exit (low, medium, high, critical)",
    ),
    evaluator: str | None = typer.Option(
        None,
        "--evaluator",
        help="Custom evaluator: 'module.path:ClassName' or 'module.path:func'",
    ),
    rpm: int | None = typer.Option(None, "--rpm", help="Requests per minute override"),
    config: Path | None = typer.Option(  # noqa: B008
        None, "--config", help="Path to YAML config file"
    ),
    patterns: Path | None = typer.Option(  # noqa: B008
        None, "--patterns", "-P", help="Path to custom patterns YAML file or directory"
    ),
    no_builtins: bool | None = typer.Option(
        None, "--no-builtins", help="Exclude built-in attack templates"
    ),
    system_prompt: str | None = typer.Option(
        None, "--system-prompt", help="System prompt to use for all attacks"
    ),
    system_prompt_file: Path | None = typer.Option(  # noqa: B008
        None, "--system-prompt-file", help="File containing system prompt"
    ),
) -> None:
    """Run prompt injection security tests against a model."""
    # Load YAML config
    yaml_cfg = None
    if config is not None:
        if not config.exists():
            console.print(f"[red]Config file not found:[/red] {config}")
            raise SystemExit(1)
        try:
            yaml_cfg = load_yaml_config(config)
        except ValueError as e:
            console.print(f"[red]Config error:[/red] {e}")
            raise SystemExit(1) from None
    else:
        found = find_config_file()
        if found is not None:
            try:
                yaml_cfg = load_yaml_config(found)
            except ValueError as e:
                console.print(f"[red]Config error in {found}:[/red] {e}")
                raise SystemExit(1) from None

    # Merge: CLI overrides YAML overrides defaults
    resolved_model = model or (yaml_cfg.model if yaml_cfg else None)
    if resolved_model is None:
        console.print("[red]Error:[/red] --model is required (or set in config file)")
        raise SystemExit(1)

    resolved_provider = provider or (yaml_cfg.provider if yaml_cfg else None)
    resolved_api_key = api_key or (yaml_cfg.api_key if yaml_cfg else None)
    resolved_base_url = base_url or (yaml_cfg.base_url if yaml_cfg else None)
    resolved_count = (
        count
        if count is not None
        else (yaml_cfg.count if yaml_cfg and yaml_cfg.count is not None else 50)
    )
    resolved_parallel = (
        parallel
        if parallel is not None
        else (yaml_cfg.parallel if yaml_cfg and yaml_cfg.parallel is not None else False)
    )
    resolved_max_workers = (
        max_workers
        if max_workers is not None
        else (yaml_cfg.max_workers if yaml_cfg and yaml_cfg.max_workers is not None else 4)
    )
    resolved_seed = (
        seed
        if seed is not None
        else (yaml_cfg.seed if yaml_cfg and yaml_cfg.seed is not None else None)
    )
    resolved_output = (
        output
        if output is not None
        else (Path(yaml_cfg.output) if yaml_cfg and yaml_cfg.output is not None else None)
    )
    resolved_rpm = (
        rpm
        if rpm is not None
        else (yaml_cfg.rpm if yaml_cfg and yaml_cfg.rpm is not None else None)
    )
    resolved_severity = (
        severity
        if severity is not None
        else (Severity(yaml_cfg.severity) if yaml_cfg and yaml_cfg.severity is not None else None)
    )
    resolved_no_builtins = (
        no_builtins
        if no_builtins is not None
        else (yaml_cfg.no_builtins if yaml_cfg and yaml_cfg.no_builtins is not None else False)
    )
    resolved_patterns = (
        patterns
        if patterns is not None
        else (Path(yaml_cfg.patterns) if yaml_cfg and yaml_cfg.patterns is not None else None)
    )

    # Merge categories (CLI overrides YAML)
    resolved_categories: list[AttackCategory] | None = None
    if category:
        resolved_categories = category
    elif yaml_cfg and yaml_cfg.categories:
        resolved_categories = [AttackCategory(c) for c in yaml_cfg.categories]

    # Resolve system prompt
    resolved_system_prompt = _resolve_system_prompt(
        system_prompt,
        system_prompt_file,
        yaml_cfg.system_prompt if yaml_cfg else None,
        yaml_cfg.system_prompt_file if yaml_cfg else None,
    )

    # Resolve format, fail_on, evaluator
    resolved_format = format_opt or (yaml_cfg.format if yaml_cfg else None)
    resolved_fail_on_str = fail_on or (yaml_cfg.fail_on if yaml_cfg else None)
    resolved_fail_on = Severity.CRITICAL
    if resolved_fail_on_str is not None:
        try:
            resolved_fail_on = Severity(resolved_fail_on_str.lower())
        except ValueError:
            console.print(
                f"[red]Invalid --fail-on value:[/red] '{resolved_fail_on_str}'. "
                f"Must be one of: low, medium, high, critical"
            )
            raise SystemExit(1) from None

    resolved_evaluator_spec = evaluator or (yaml_cfg.evaluator if yaml_cfg else None)
    custom_evaluator = None
    if resolved_evaluator_spec:
        from llmvault.runner.evaluator_loader import load_evaluator

        try:
            custom_evaluator = load_evaluator(resolved_evaluator_spec)
        except (ValueError, ImportError, AttributeError) as e:
            console.print(f"[red]Evaluator error:[/red] {e}")
            raise SystemExit(1) from None

    console.print(f"[bold]LLMVault[/bold] - Testing model: [cyan]{resolved_model}[/cyan]")

    # Build config
    rate_limit = RateLimitConfig()
    if resolved_rpm is not None:
        rate_limit = RateLimitConfig(requests_per_minute=resolved_rpm)

    try:
        llmvault_config = LLMVaultConfig(
            model=resolved_model,
            provider=resolved_provider,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            rate_limit=rate_limit,
            parallel=resolved_parallel,
            max_workers=resolved_max_workers,
        )
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise SystemExit(1) from None

    # Create provider
    try:
        llm_provider = get_provider(llmvault_config)
    except ValueError as e:
        console.print(f"[red]Provider error:[/red] {e}")
        raise SystemExit(1) from None

    console.print(f"  Provider: {llmvault_config.provider}")

    # Build template list
    templates = [] if resolved_no_builtins else list(ALL_TEMPLATES)
    if resolved_patterns is not None:
        from llmvault.attacks.loader import load_patterns

        try:
            custom_templates = load_patterns(resolved_patterns)
            templates.extend(custom_templates)
        except (ValueError, FileNotFoundError) as e:
            console.print(f"[red]Pattern loading error:[/red] {e}")
            raise SystemExit(1) from None

    if not templates:
        console.print("[yellow]No attack templates available.[/yellow]")
        raise SystemExit(0)

    # Generate attacks
    engine = AttackEngine(templates=templates, seed=resolved_seed)
    attack_list = engine.generate_attacks(categories=resolved_categories, count=resolved_count)

    # Filter by minimum severity
    if resolved_severity is not None:
        min_index = _SEVERITY_ORDER.index(resolved_severity)
        attack_list = [a for a in attack_list if _SEVERITY_ORDER.index(a.severity) >= min_index]

    if not attack_list:
        console.print("[yellow]No attacks match the specified filters.[/yellow]")
        raise SystemExit(0)

    # Apply system prompt to all attacks
    if resolved_system_prompt:
        for attack in attack_list:
            attack.system_prompt = resolved_system_prompt

    console.print(f"  Attacks:  {len(attack_list)}")
    console.print()

    # Run attacks
    reporter = CLIReporter(console=console)
    runner = TestRunner(
        provider=llm_provider,
        config=llmvault_config,
        evaluator=custom_evaluator,
        on_progress=reporter.on_progress,
    )

    result = asyncio.run(runner.run(attack_list))

    # Display summary
    reporter.print_summary(result)

    # Generate report if requested
    if resolved_output is not None:
        fmt = resolved_format or _detect_format(resolved_output.suffix)
        if fmt == "json":
            JSONReporter().generate(result, resolved_output)
        elif fmt == "sarif":
            SARIFReporter().generate(result, resolved_output)
        else:
            HTMLReporter().generate(result, resolved_output)
        console.print(f"\n[green]Report saved to:[/green] {resolved_output}")

    # Exit with appropriate code
    sys.exit(result.compute_exit_code(resolved_fail_on))


@app.command()
def attacks(
    category: AttackCategory | None = typer.Option(  # noqa: B008
        None, "--category", "-c", help="Filter by category"
    ),
) -> None:
    """List available attack patterns."""
    templates = ALL_TEMPLATES
    if category is not None:
        templates = [t for t in templates if t.category == category]

    if not templates:
        console.print("[yellow]No templates match the specified filter.[/yellow]")
        return

    table = Table(title="Attack Templates", show_lines=False)
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Severity")
    table.add_column("Description", max_width=50)

    for t in templates:
        sev_color = _SEVERITY_COLORS.get(t.severity, "white")
        table.add_row(
            t.name,
            t.category.value,
            f"[{sev_color}]{t.severity.value}[/{sev_color}]",
            t.description,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(templates)} templates[/dim]")


if __name__ == "__main__":
    app()
