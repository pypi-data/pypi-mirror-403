from typing import Sequence, TYPE_CHECKING
from dataclasses import dataclass, field

from riskit.convergence.analyze import ConvergenceAnalysis

from numtypes import Array, Dim1

import numpy as np

if TYPE_CHECKING:
    from anyio import Path as AsyncPath
    from rich.table import Table
    from rich.panel import Panel


@dataclass(frozen=True)
class ConvergenceFit:
    """Power-law fit: error ∝ N^(-rate)."""

    intercept: float
    rate: float
    r_squared: float

    @staticmethod
    def from_data(
        *, sample_counts: Sequence[int], errors: Array[Dim1]
    ) -> "ConvergenceFit":
        """Fits a power-law model to the provided (N, error) data."""
        log_n = np.log(sample_counts)
        log_err = np.log(errors)

        slope, intercept = np.polyfit(log_n, log_err, 1)
        predicted = slope * log_n + intercept

        ss_res = float(np.sum((log_err - predicted) ** 2))
        ss_tot = float(np.sum((log_err - np.mean(log_err)) ** 2))
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

        return ConvergenceFit(
            intercept=float(intercept),
            rate=float(-slope),
            r_squared=r_squared,
        )

    def samples_for_error(self, target: float) -> int | None:
        """Estimates the number of samples needed to achieve the target error."""
        if self.rate <= 0:
            return None

        log_n = (self.intercept - np.log(target)) / self.rate
        return max(1, int(np.exp(log_n)))


@dataclass(frozen=True)
class MetricFit:
    """Convergence fit for one (test, metric) pair."""

    test_name: str
    metric_name: str
    fit: ConvergenceFit
    final_error: float

    def samples_for_error(self, target: float) -> int | None:
        """Estimates the number of samples needed to achieve the target error."""
        return self.fit.samples_for_error(target)


@dataclass(frozen=True)
class ConvergenceSummary:
    fits: Sequence[MetricFit]
    target_error: float

    async def save(self, *, to: "AsyncPath") -> None:
        await to.parent.mkdir(parents=True, exist_ok=True)
        await to.write_text(self._html(), encoding="utf-8")

    def _html(self) -> str:
        from rich.console import Console

        console = Console(record=True, width=120, force_terminal=True)
        console.print(self._build_table())
        console.print(self._statistics_panel())

        return console.export_html(inline_styles=True)

    def _build_table(self) -> "Table":
        from rich.table import Table

        table = Table(
            title=f"Convergence Summary (target: {self.target_error:.1%} error)"
        )

        table.add_column("Test", style="cyan")
        table.add_column("Metric", style="magenta")
        table.add_column("Rate", justify="right")
        table.add_column("R²", justify="right")
        table.add_column("Final Err", justify="right")
        table.add_column("Est. N", justify="right")

        for f in self.fits:
            rate_str = (
                f"N^(-{f.fit.rate:.2f})" if f.fit.rate > 0 else "[red]divergent[/red]"
            )
            r_squared_style = (
                "green"
                if f.fit.r_squared > 0.7
                else "yellow"
                if f.fit.r_squared > 0.5
                else "red"
            )
            est_n = f.samples_for_error(self.target_error)
            est_str = f"{est_n:,}" if est_n else "[red]N/A[/red]"

            table.add_row(
                f.test_name,
                f.metric_name,
                rate_str,
                f"[{r_squared_style}]{f.fit.r_squared:.3f}[/{r_squared_style}]",
                f"{f.final_error:.2e}",
                est_str,
            )

        return table

    def _statistics_panel(self) -> "Panel":
        from rich.panel import Panel
        from rich.text import Text

        if not self.fits:
            return Panel("No data")

        rates = [f.fit.rate for f in self.fits]
        r_squareds = [f.fit.r_squared for f in self.fits]

        lines = Text()
        lines.append(f"Metrics analyzed: {len(self.fits)}\n")
        lines.append(f"Rate: mean=N^(-{np.mean(rates):.2f}), std={np.std(rates):.2f}\n")
        lines.append(f"R²: mean={np.mean(r_squareds):.3f}\n")

        good_estimates = [
            est
            for f in self.fits
            if f.fit.r_squared > 0.5 and f.fit.rate > 0.2
            if (est := f.samples_for_error(self.target_error)) and est < 10_000_000
        ]

        if good_estimates:
            lines.append(f"\nSamples for {self.target_error:.1%} error ")
            lines.append("(R² > 0.5, rate > 0.2)", style="dim")
            lines.append(f"\n  n={len(good_estimates)}, ")
            lines.append(f"mean={int(np.mean(good_estimates)):,}, ")
            lines.append(f"median={int(np.median(good_estimates)):,}, ")
            lines.append(f"p95={int(np.percentile(good_estimates, 95)):,}")

        return Panel(lines, title="Statistics")


@dataclass(frozen=True)
class ConvergenceCollector:
    """Collects convergence analyses and fits power-law models."""

    _analyses: list[tuple[str, ConvergenceAnalysis]] = field(default_factory=list)

    def add(self, name: str, analysis: ConvergenceAnalysis) -> None:
        self._analyses.append((name, analysis))

    def summary(self, *, target_error: float) -> ConvergenceSummary:
        """Generates a summary of convergence fits across all collected analyses."""
        return ConvergenceSummary(fits=self._fit_all(), target_error=target_error)

    def _fit_all(self) -> list[MetricFit]:
        results: list[MetricFit] = []

        for test_name, analysis in self._analyses:
            for metric_name, result in analysis.results_by_metric.items():
                if result.error_is_absolute:
                    continue

                if (errors := result.relative_errors()) is None:
                    continue

                results.append(
                    MetricFit(
                        test_name=test_name,
                        metric_name=metric_name,
                        fit=ConvergenceFit.from_data(
                            sample_counts=result.sample_counts, errors=errors
                        ),
                        final_error=errors[-1],
                    )
                )

        return results
