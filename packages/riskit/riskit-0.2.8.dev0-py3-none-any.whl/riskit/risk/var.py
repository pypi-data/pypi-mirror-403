from dataclasses import dataclass

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
    EvaluationCallback,
    RiskMetric,
)


def core[ArrayT: ArrayLike](
    compute: Compute[ArrayT], costs: ArrayT, q: float
) -> ArrayT:
    trajectory_costs = compute.sum(costs, axis=0)
    return compute.quantile(trajectory_costs, q=q, axis=1)


@dataclass(frozen=True)
class ValueAtRisk[
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

        result = self.backend.execute(core, costs, self.alpha)
        risk = self.backend.to_risk(result, time_steps=T)
        self.callback(costs, risk)

        return risk

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "ValueAtRisk[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ValueAtRisk(
            cost=self.cost,
            backend=self.backend,
            sampler=sampler,
            alpha=self.alpha,
            callback=self.callback,
        )

    def on_evaluation(
        self, callback: EvaluationCallback[CostsT, RiskT]
    ) -> "ValueAtRisk[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ValueAtRisk(
            cost=self.cost,
            backend=self.backend,
            sampler=self.sampler,
            alpha=self.alpha,
            callback=callback,
        )
