from typing import Mapping, Sequence, TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict

from riskit.convergence.fit import MetricFit

import numpy as np

if TYPE_CHECKING:
    from anyio import Path as AsyncPath
    from rich.text import Text
    from rich.table import Table
    from rich.panel import Panel


class MetricFitSorter:
    @staticmethod
    def sort(fits: Sequence[MetricFit]) -> Sequence[MetricFit]:
        def sorter(it: MetricFit) -> tuple:
            return (
                it.test_name,
                MetricFitSorter.name_order_of(it.metric_name),
                it.metric_name,
            )

        return sorted(fits, key=sorter)

    @staticmethod
    def sort_by_metric[T](estimates: Mapping[str, T]) -> Sequence[tuple[str, T]]:
        def sorter(item: tuple[str, T]) -> tuple:
            name, _ = item
            return (MetricFitSorter.name_order_of(name), name)

        return sorted(estimates.items(), key=sorter)

    @staticmethod
    def name_order_of(name: str) -> int:
        if name.startswith("E"):
            return 0
        if name.startswith("MV"):
            return 1
        if name.startswith("VaR"):
            return 2
        if name.startswith("CVaR"):
            return 3
        return 4


@dataclass(frozen=True)
class ConvergenceSummary:
    fits: Sequence[MetricFit]
    target_error: float
    min_error: float
    highlight: Sequence[str]
    r_squared_good: float
    r_squared_min: float
    rate_range: tuple[float, float]

    @staticmethod
    def of(
        fits: Sequence[MetricFit],
        *,
        target_error: float,
        min_error: float,
        highlight: Sequence[str],
        r_squared_good: float,
        r_squared_min: float,
        rate_range: tuple[float, float],
    ) -> "ConvergenceSummary":
        return ConvergenceSummary(
            fits=MetricFitSorter.sort(fits),
            target_error=target_error,
            min_error=min_error,
            highlight=highlight,
            r_squared_good=r_squared_good,
            r_squared_min=r_squared_min,
            rate_range=rate_range,
        )

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
            title=f"Convergence Summary (target: {self.target_error:.1%} error, min fit error: {self.min_error:.1%})"
        )

        table.add_column("Test", style="cyan")
        table.add_column("Metric", style="magenta")
        table.add_column("Rate", justify="right")
        table.add_column("R²", justify="right")
        table.add_column("Sample Range", justify="right")
        table.add_column("Error Range", justify="right")
        table.add_column("Est. N for Target", justify="right")

        for it in self.fits:
            fit = it.get_for(min_error=self.min_error)

            rate_str = (
                f"N^(-{fit.rate:.2f})" if fit.rate > 0 else "[red]divergent[/red]"
            )
            r_squared_style = (
                "green"
                if fit.r_squared > self.r_squared_good
                else "yellow"
                if fit.r_squared > self.r_squared_min
                else "red"
            )
            est_n = fit.samples_for_error(self.target_error)
            est_str = f"{est_n:,}" if est_n else "[red]N/A[/red]"

            table.add_row(
                it.test_name,
                it.metric_name,
                rate_str,
                f"[{r_squared_style}]{fit.r_squared:.3f}[/{r_squared_style}]",
                f"{it.min_sample_count:,} - {it.max_sample_count:,}",
                f"{it.min_error:.2e} - {it.max_error:.2e}",
                est_str,
                style="bold on grey82" if it.test_name in self.highlight else "",
            )

        return table

    def _statistics_panel(self) -> "Panel":
        from rich.panel import Panel
        from rich.text import Text

        if not self.fits:
            return Panel("No data")

        lines = Text()
        lines.append(self._overall_statistics())
        lines.append(self._overall_estimates())
        lines.append(self._estimates_by_metric())
        lines.append(self._estimates_for_highlighted())

        return Panel(lines, title="Statistics")

    def _overall_statistics(self) -> "Text":
        from rich.text import Text

        lines = Text()
        fits = [it.get_for(min_error=self.min_error) for it in self.fits]
        rates = [fit.rate for fit in fits]
        r_squareds = [fit.r_squared for fit in fits]

        lines = Text()
        lines.append(f"Metrics analyzed: {len(fits)}\n")
        lines.append(f"Rate: mean=N^(-{np.mean(rates):.2f}), std={np.std(rates):.2f}\n")
        lines.append(f"R²: mean={np.mean(r_squareds):.3f}\n")

        return lines

    def _overall_estimates(self) -> "Text":
        from rich.text import Text

        lines = Text()
        fits = [it.get_for(min_error=self.min_error) for it in self.fits]
        r_squared_min = self.r_squared_min
        rate_min, rate_max = self.rate_range

        good_estimates = [
            estimate
            for fit in fits
            if fit.r_squared > r_squared_min and rate_min < fit.rate < rate_max
            if (estimate := fit.samples_for_error(self.target_error)) is not None
        ]

        if good_estimates:
            lines.append(f"\nSamples for {self.target_error:.1%} error ", style="bold")
            lines.append(
                f"(R² > {r_squared_min}, {rate_min} < rate < {rate_max}, Rel. Error > {self.min_error:.1%})",
                style="dim",
            )
            lines.append(f"\n  n={len(good_estimates)}, ")
            lines.append(f"mean={int(np.mean(good_estimates)):,}, ")
            lines.append(f"median={int(np.median(good_estimates)):,}, ")
            lines.append(f"p95={int(np.percentile(good_estimates, 95)):,}\n")

        return lines

    def _estimates_by_metric(self) -> "Text":
        from rich.text import Text

        lines = Text()
        estimates_by_metric: dict[str, list[int]] = defaultdict(list)
        r_squared_min = self.r_squared_min
        rate_min, rate_max = self.rate_range

        for it in self.fits:
            fit = it.get_for(min_error=self.min_error)

            if (
                fit.r_squared > r_squared_min
                and rate_min < fit.rate < rate_max
                and (estimate := fit.samples_for_error(self.target_error)) is not None
            ):
                estimates_by_metric[it.metric_name].append(estimate)

        for metric_name, estimates in MetricFitSorter.sort_by_metric(
            estimates_by_metric
        ):
            lines.append(f"\nSamples for {metric_name}\n")
            lines.append(f"  n={len(estimates)}, ")
            lines.append(f"mean={int(np.mean(estimates)):,}, ")
            lines.append(f"median={int(np.median(estimates)):,}, ")
            lines.append(f"p95={int(np.percentile(estimates, 95)):,}\n")

        return lines

    def _estimates_for_highlighted(self) -> "Text":
        from rich.text import Text

        lines = Text()
        fits_by_highlight = {
            highlight: [it for it in self.fits if it.test_name == highlight]
            for highlight in self.highlight
        }

        for highlight, fits in fits_by_highlight.items():
            lines.append(f"\nSamples for {highlight}\n")

            for it in fits:
                fit = it.get_for(min_error=self.min_error)
                est_n = fit.samples_for_error(self.target_error)
                est_str = f"{est_n:,}" if est_n else "[red]N/A[/red]"
                lines.append(f"  {it.metric_name}: {est_str}\n")

        return lines
