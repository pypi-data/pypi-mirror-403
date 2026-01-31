from typing import Sequence
from dataclasses import dataclass, field
from collections import defaultdict

from riskit.convergence.analyze import ConvergenceAnalysis
from riskit.convergence.fit import MetricFit
from riskit.convergence.summary import ConvergenceSummary


@dataclass(frozen=True)
class ConvergenceCollector:
    """Collects convergence analyses and fits power-law models."""

    _analyses: dict[str, ConvergenceAnalysis] = field(
        default_factory=lambda: defaultdict(ConvergenceAnalysis.empty)
    )

    def add(self, name: str, analysis: ConvergenceAnalysis) -> None:
        self._analyses[name] = self._analyses[name].merge(analysis)

    def summary(
        self,
        *,
        target_error: float,
        min_error: float,
        highlight: Sequence[str],
        r_squared_good: float,
        r_squared_min: float,
        rate_range: tuple[float, float],
    ) -> ConvergenceSummary:
        """Generates a summary of convergence fits across all collected analyses."""
        return ConvergenceSummary.of(
            self._fit_all(),
            target_error=target_error,
            min_error=min_error,
            highlight=highlight,
            r_squared_good=r_squared_good,
            r_squared_min=r_squared_min,
            rate_range=rate_range,
        )

    def _fit_all(self) -> Sequence[MetricFit]:
        results: list[MetricFit] = []

        for test_name, analysis in self._analyses.items():
            for metric_name, result in analysis.results_by_metric.items():
                if result.error_is_absolute:
                    continue

                if (errors := result.relative_errors()) is None:
                    continue

                results.append(
                    MetricFit(
                        test_name=test_name,
                        metric_name=metric_name,
                        sample_counts=result.sample_counts,
                        errors=errors,
                        standard_errors=result.standard_errors,
                    )
                )

        return results
