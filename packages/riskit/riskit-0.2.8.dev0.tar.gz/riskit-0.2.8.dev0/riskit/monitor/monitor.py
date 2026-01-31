from typing import NamedTuple
from dataclasses import dataclass, field
from datetime import datetime

from riskit.risk import Costs, Risk, RiskMetric


class EvaluationData[CostsT: Costs, RiskT: Risk](NamedTuple):
    """Data captured from a single risk metric evaluation.

    Attributes:
        costs: The (T, M, N) cost array from the batch cost function.
        risk: The (T, M) risk array from the metric.
        timestamp: When the evaluation occurred.
    """

    costs: CostsT
    risk: RiskT
    timestamp: datetime


@dataclass(frozen=True)
class RiskMetricEvaluationMonitor[CostsT: Costs, RiskT: Risk]:
    """A monitor that captures data from risk metric evaluations.

    The monitor wraps risk metrics by registering an evaluation callback
    that stores computed values for later visualization and debugging.

    Example usage:
        >>> monitor = RiskMetricEvaluationMonitor()
        >>>
        >>> # Wrap the metric to capture evaluation data
        >>> monitored_metric = monitor.monitor(risk.expected_value_of(my_cost))
        >>>
        >>> # Compute as usual
        >>> result = monitored_metric.compute(trajectories=..., uncertainties=...)
        >>>
        >>> # Access captured data
        >>> monitor.last_evaluation  # or monitor.evaluations[-1]
    """

    _evaluations: list[EvaluationData[CostsT, RiskT]] = field(
        default_factory=list, init=False
    )

    @staticmethod
    def monitoring[T, U, C: Costs, R: Risk](
        metric: RiskMetric[T, U, C, R],
    ) -> tuple[RiskMetric[T, U, C, R], "RiskMetricEvaluationMonitor[C, R]"]:
        """Wraps a risk metric to capture complete evaluation data.

        The wrapped metric will invoke a callback after each compute() call
        that captures the costs and risk values.

        Args:
            metric: The risk metric to wrap.

        Returns:
            A new risk metric that captures evaluation data, along with the monitor itself.
        """
        monitor: RiskMetricEvaluationMonitor[C, R] = RiskMetricEvaluationMonitor()

        def record(costs: C, risk: R) -> None:
            monitor._evaluations.append(
                EvaluationData(
                    costs=costs,
                    risk=risk,
                    timestamp=datetime.now(),
                )
            )

        return metric.on_evaluation(record), monitor

    def clear(self) -> None:
        """Clears all captured evaluation data."""
        self._evaluations.clear()

    @property
    def evaluations(self) -> list[EvaluationData[CostsT, RiskT]]:
        """Returns all captured evaluation data in order of occurrence."""
        return list(self._evaluations)

    @property
    def last_evaluation(self) -> EvaluationData[CostsT, RiskT] | None:
        """Returns the most recent captured evaluation data, or None if none exist."""
        return self._evaluations[-1] if self._evaluations else None
