from typing import Any, Mapping, Sequence, TYPE_CHECKING
from dataclasses import dataclass
from functools import cached_property

from riskit.sampler import sampler
from riskit.risk import RiskMetric, TrajectoriesProvider, Uncertainties, Risk
from riskit.convergence.common import ComputedRisks
from riskit.convergence.visualize import AnalysisVisualizer

from numtypes import Array, Dim1

import numpy as np


if TYPE_CHECKING:
    from anyio import Path as AsyncPath


@dataclass(frozen=True)
class ConvergenceAnalysis:
    sample_counts: Sequence[int]
    results_by_metric: Mapping[str, "ComputedRisks"]

    @staticmethod
    def empty() -> "ConvergenceAnalysis":
        return ConvergenceAnalysis(sample_counts=(), results_by_metric={})

    async def save(self, *, to: "AsyncPath") -> None:
        """Saves visualizations of the convergence analysis to the specified path."""
        await AnalysisVisualizer().save(analysis=self, to=to)

    def result_for(self, metric_name: str) -> ComputedRisks:
        """Retrieves the computed risks for the specified metric name."""
        return self.results_by_metric[metric_name]

    def merge(self, other: "ConvergenceAnalysis") -> "ConvergenceAnalysis":
        """Merges this analysis with another, combining their results."""
        return ConvergenceAnalysis(
            sample_counts=self.sample_counts,
            results_by_metric={
                name: risks
                for name in set(self.results_by_metric) | set(other.results_by_metric)
                if (
                    risks := ComputedRisks.merge(
                        self.results_by_metric.get(name),
                        other.results_by_metric.get(name),
                    )
                )
                is not None
            },
        )

    @cached_property
    def results(self) -> Sequence[tuple[str, ComputedRisks]]:
        """Returns the mapping of metric names to computed risks."""
        return list(self.results_by_metric.items())


@dataclass(frozen=True)
class ConvergenceAnalyzer:
    """Computes risk metrics with increasing sample counts to analyze convergence.

    Attributes:
        sample_counts: List of sample counts (N values) to test.
        repetitions: Number of times to repeat each evaluation for averaging.
    """

    sample_counts: Sequence[int]
    repetitions: int = 1

    def __post_init__(self) -> None:
        assert len(self.sample_counts) > 0, "At least one sample count is required."
        assert self.repetitions > 1, (
            "At least two repetitions are required for averaging."
        )

    def analyze[TrajectoriesT, UncertaintySamplesT](
        self,
        *,
        risk_metrics: Mapping[
            str, RiskMetric[TrajectoriesT, UncertaintySamplesT, Any, Risk]
        ],
        trajectories: TrajectoriesProvider[TrajectoriesT],
        uncertainties: Uncertainties[UncertaintySamplesT],
        ground_truths: Mapping[str, float] | None = None,
    ) -> ConvergenceAnalysis:
        """Analyzes convergence of risk metrics across sample counts.

        Args:
            risk_metrics: Mapping from metric names to risk metrics to analyze.
            trajectories: The trajectories provider for computation.
            uncertainties: The uncertainties to sample from.
            ground_truths: Optional mapping from metric names to analytical ground truth values.
        """
        ground_truths = ground_truths or {}

        return ConvergenceAnalysis(
            sample_counts=self.sample_counts,
            results_by_metric={
                name: self._analyze_single_metric(
                    name=name,
                    metric=metric,
                    trajectories=trajectories,
                    uncertainties=uncertainties,
                    ground_truth=ground_truths.get(name),
                )
                for name, metric in risk_metrics.items()
            },
        )

    def _analyze_single_metric[TrajectoriesT, UncertaintySamplesT](
        self,
        *,
        name: str,
        metric: RiskMetric[TrajectoriesT, UncertaintySamplesT, Any, Risk],
        trajectories: TrajectoriesProvider[TrajectoriesT],
        uncertainties: Uncertainties[UncertaintySamplesT],
        ground_truth: float | None,
    ) -> ComputedRisks:
        risks_by_sample_count: dict[int, Array[Dim1]] = {}

        for sample_count in self.sample_counts:
            configured_metric = metric.sampled_with(sampler.monte_carlo(sample_count))

            risks_by_sample_count[sample_count] = np.asarray(
                [
                    np.asarray(
                        configured_metric.compute(
                            trajectories=trajectories,
                            uncertainties=uncertainties,
                        )
                    )[0, 0]
                    for _ in range(self.repetitions)
                ]
            )

        return ComputedRisks(
            name=name,
            risks_by_sample_count=risks_by_sample_count,
            ground_truth=ground_truth,
        )
