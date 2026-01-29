"""Result models for test suite execution."""

from pydantic import BaseModel, computed_field

from llmvault.attacks.base import AttackCategory, AttackResult, Severity


class CategoryBreakdown(BaseModel):
    """Vulnerability breakdown for a single attack category."""

    category: AttackCategory
    total: int
    vulnerable: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 1.0
        return 1.0 - (self.vulnerable / self.total)


class SeverityBreakdown(BaseModel):
    """Vulnerability breakdown for a single severity level."""

    severity: Severity
    total: int
    vulnerable: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 1.0
        return 1.0 - (self.vulnerable / self.total)


class TestSuiteResult(BaseModel):
    """Aggregated results from a test suite run."""

    results: list[AttackResult]
    model: str
    provider: str
    duration_seconds: float
    errors: list[str] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_attacks(self) -> int:
        return len(self.results)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def vulnerable_count(self) -> int:
        return sum(1 for r in self.results if r.is_vulnerable)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pass_rate(self) -> float:
        if self.total_attacks == 0:
            return 1.0
        return 1.0 - (self.vulnerable_count / self.total_attacks)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def exit_code(self) -> int:
        """Return 1 if any critical vulnerability found, else 0."""
        return self.compute_exit_code(Severity.CRITICAL)

    def compute_exit_code(self, fail_on: Severity = Severity.CRITICAL) -> int:
        """Return 1 if any vulnerability at or above fail_on severity found, else 0.

        Severity order: LOW < MEDIUM < HIGH < CRITICAL.
        """
        severity_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        threshold_index = severity_order.index(fail_on)
        for r in self.results:
            if r.is_vulnerable:
                result_index = severity_order.index(r.attack.severity)
                if result_index >= threshold_index:
                    return 1
        return 0

    def by_category(self) -> list[CategoryBreakdown]:
        """Break down results by attack category."""
        breakdowns: list[CategoryBreakdown] = []
        for category in AttackCategory:
            category_results = [r for r in self.results if r.attack.category == category]
            if not category_results:
                continue
            breakdowns.append(
                CategoryBreakdown(
                    category=category,
                    total=len(category_results),
                    vulnerable=sum(1 for r in category_results if r.is_vulnerable),
                )
            )
        return breakdowns

    def by_severity(self) -> list[SeverityBreakdown]:
        """Break down results by severity level."""
        breakdowns: list[SeverityBreakdown] = []
        for severity in Severity:
            severity_results = [r for r in self.results if r.attack.severity == severity]
            if not severity_results:
                continue
            breakdowns.append(
                SeverityBreakdown(
                    severity=severity,
                    total=len(severity_results),
                    vulnerable=sum(1 for r in severity_results if r.is_vulnerable),
                )
            )
        return breakdowns
