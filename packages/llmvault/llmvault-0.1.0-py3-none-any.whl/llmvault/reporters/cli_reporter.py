"""Rich-based CLI reporter for test results."""

from rich.console import Console
from rich.table import Table

from llmvault.attacks.base import AttackResult, Severity
from llmvault.runner.models import TestSuiteResult

_SEVERITY_COLORS: dict[Severity, str] = {
    Severity.LOW: "blue",
    Severity.MEDIUM: "yellow",
    Severity.HIGH: "red",
    Severity.CRITICAL: "bold red",
}


def _pass_rate_color(rate: float) -> str:
    """Return a color string based on pass rate."""
    if rate >= 0.9:
        return "green"
    if rate >= 0.7:
        return "yellow"
    return "red"


class CLIReporter:
    """Rich terminal reporter for attack test progress and results."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def on_progress(self, completed: int, total: int, result: AttackResult | None) -> None:
        """Progress callback for TestRunner.

        Prints a status line for each completed attack.
        """
        if result is None:
            self._console.print(f"  [{completed}/{total}] ...")
            return

        status = "[red]VULNERABLE[/red]" if result.is_vulnerable else "[green]PASS[/green]"
        self._console.print(f"  [{completed}/{total}] {result.attack.name}: {status}")

    def print_summary(self, result: TestSuiteResult) -> None:
        """Print a full summary of the test suite results."""
        self._console.print()
        self._console.rule("[bold]LLMVault Test Results[/bold]")
        self._console.print()

        # Header info
        self._console.print(f"  Model:    [bold]{result.model}[/bold]")
        self._console.print(f"  Provider: {result.provider}")
        self._console.print(f"  Duration: {result.duration_seconds:.1f}s")
        self._console.print(f"  Attacks:  {result.total_attacks}")
        self._console.print()

        # Overall pass rate
        rate_color = _pass_rate_color(result.pass_rate)
        self._console.print(
            f"  Pass rate: [{rate_color}]{result.pass_rate:.0%}[/{rate_color}]"
            f"  ({result.vulnerable_count} vulnerable / {result.total_attacks} total)"
        )
        self._console.print()

        # Category breakdown
        categories = result.by_category()
        if categories:
            cat_table = Table(title="Category Breakdown", show_lines=False)
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Total", justify="right")
            cat_table.add_column("Vulnerable", justify="right")
            cat_table.add_column("Pass Rate", justify="right")
            for cat in categories:
                color = _pass_rate_color(cat.pass_rate)
                cat_table.add_row(
                    cat.category.value,
                    str(cat.total),
                    str(cat.vulnerable),
                    f"[{color}]{cat.pass_rate:.0%}[/{color}]",
                )
            self._console.print(cat_table)
            self._console.print()

        # Severity breakdown
        severities = result.by_severity()
        if severities:
            sev_table = Table(title="Severity Breakdown", show_lines=False)
            sev_table.add_column("Severity", style="cyan")
            sev_table.add_column("Total", justify="right")
            sev_table.add_column("Vulnerable", justify="right")
            sev_table.add_column("Pass Rate", justify="right")
            for sev in severities:
                sev_color = _SEVERITY_COLORS.get(sev.severity, "white")
                rate_color = _pass_rate_color(sev.pass_rate)
                sev_table.add_row(
                    f"[{sev_color}]{sev.severity.value}[/{sev_color}]",
                    str(sev.total),
                    str(sev.vulnerable),
                    f"[{rate_color}]{sev.pass_rate:.0%}[/{rate_color}]",
                )
            self._console.print(sev_table)
            self._console.print()

        # Vulnerable attacks detail
        vulnerable_results = [r for r in result.results if r.is_vulnerable]
        if vulnerable_results:
            self._console.print("[bold red]Vulnerable Attacks:[/bold red]")
            for vr in vulnerable_results:
                sev_color = _SEVERITY_COLORS.get(vr.attack.severity, "white")
                response_excerpt = vr.response[:120].replace("\n", " ")
                if len(vr.response) > 120:
                    response_excerpt += "..."
                self._console.print(
                    f"  [{sev_color}]{vr.attack.severity.value:8s}[/{sev_color}] "
                    f"{vr.attack.name} "
                    f"(confidence: {vr.confidence:.0%})"
                )
                self._console.print(f"           [dim]{response_excerpt}[/dim]")

        # Errors
        if result.errors:
            self._console.print()
            self._console.print(f"[yellow]Errors: {len(result.errors)}[/yellow]")
            for err in result.errors[:5]:
                self._console.print(f"  [dim]{err}[/dim]")
            if len(result.errors) > 5:
                self._console.print(f"  [dim]... and {len(result.errors) - 5} more[/dim]")
