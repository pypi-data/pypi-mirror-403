"""Jinja2-based HTML report generator."""

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import llmvault
from llmvault.runner.models import TestSuiteResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _rate_class(rate: float) -> str:
    """Return CSS class for a pass rate value."""
    if rate >= 0.9:
        return "color-green"
    if rate >= 0.7:
        return "color-yellow"
    return "color-red"


def _rate_bg(rate: float) -> str:
    """Return CSS background class for a pass rate value."""
    if rate >= 0.9:
        return "bg-green"
    if rate >= 0.7:
        return "bg-yellow"
    return "bg-red"


class HTMLReporter:
    """Generates self-contained HTML reports from test suite results."""

    def generate(self, result: TestSuiteResult, output_path: Path) -> None:
        """Render the HTML report and write to output_path.

        Args:
            result: The test suite results to report.
            output_path: File path where the HTML report will be written.
        """
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
        )
        env.globals["rate_class"] = _rate_class
        env.globals["rate_bg"] = _rate_bg

        template = env.get_template("report.html")

        pass_rate_class = _rate_class(result.pass_rate)
        pass_rate_bg = _rate_bg(result.pass_rate)

        html = template.render(
            result=result,
            categories=result.by_category(),
            severities=result.by_severity(),
            pass_rate_class=pass_rate_class,
            pass_rate_bg=pass_rate_bg,
            generated_at=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            version=llmvault.__version__,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
