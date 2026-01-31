from dataclasses import dataclass
from math import ceil
from warnings import warn

from riskit.risk.common import (
    Costs,
    Risk,
    ArrayLike,
    BatchCostFunction,
    TrajectoriesProvider,
    Uncertainties,
    Backend,
    Sampler,
    Compute,
    InsufficientSampleWarning,
    RiskMetric,
    EvaluationCallback,
)


def compute_cutoff_index(alpha: float, sample_count: int) -> tuple[int, bool]:
    ideal_cutoff = ceil(alpha * sample_count)

    if ideal_cutoff >= sample_count:
        return sample_count - 1, True

    return ideal_cutoff, False


def core[ArrayT: ArrayLike](
    compute: Compute[ArrayT], costs: ArrayT, cutoff: int, n: int
) -> ArrayT:
    trajectory_costs = compute.sum(costs, axis=0)
    sorted_costs = compute.sort(trajectory_costs, axis=1)
    tail_indices = compute.arange(cutoff, n)
    tail = compute.take(sorted_costs, indices=tail_indices, axis=1)
    return compute.mean(tail, axis=1)


@dataclass(frozen=True)
class ConditionalValueAtRisk[
    TrajectoriesT,
    UncertaintySamplesT,
    CostsT: Costs,
    RiskT: Risk,
    ArrayT: ArrayLike,
](RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]):
    cost: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT]
    backend: Backend[CostsT, RiskT, ArrayT]
    sampler: Sampler[UncertaintySamplesT]
    alpha: float
    callback: EvaluationCallback[CostsT, RiskT]

    def __post_init__(self) -> None:
        assert 0.0 < self.alpha < 1.0, "Alpha must be in the interval (0, 1)."

    def compute(
        self,
        *,
        trajectories: TrajectoriesProvider[TrajectoriesT],
        uncertainties: Uncertainties[UncertaintySamplesT],
    ) -> RiskT:
        T, M = trajectories.time_steps, trajectories.trajectory_count

        samples, N = self.sampler.sample_from(uncertainties)
        costs = self.cost(trajectories=trajectories.get(), uncertainties=samples)

        assert costs.shape == (T, M, N), (
            f"Costs shape {costs.shape} does not match expected shape {(T, M, N)}."
        )

        cutoff_index, was_adjusted = compute_cutoff_index(self.alpha, N)

        if was_adjusted:
            required_tail_size = ceil((1 - self.alpha) * N)
            warn(
                f"CVaR with alpha={self.alpha} requires at least {required_tail_size + 1} "
                f"samples for accurate tail estimation, but only {N} samples were provided. "
                f"Using only the highest sample for tail mean.",
                InsufficientSampleWarning,
                stacklevel=2,
            )

        result = self.backend.execute(
            core, costs, cutoff_index, N, static_argument_indices=(1, 2)
        )
        risk = self.backend.to_risk(result, time_steps=T)
        self.callback(costs, risk)

        return risk

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "ConditionalValueAtRisk[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ConditionalValueAtRisk(
            cost=self.cost,
            backend=self.backend,
            sampler=sampler,
            alpha=self.alpha,
            callback=self.callback,
        )

    def on_evaluation(
        self, callback: EvaluationCallback[CostsT, RiskT]
    ) -> "ConditionalValueAtRisk[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ConditionalValueAtRisk(
            cost=self.cost,
            backend=self.backend,
            sampler=self.sampler,
            alpha=self.alpha,
            callback=callback,
        )
