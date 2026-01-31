from dataclasses import dataclass

from riskit.risk.common import (
    Costs,
    Risk,
    ArrayLike,
    BatchCostFunction,
    TrajectoriesProvider,
    Uncertainties,
    Sampler,
    Backend,
    Compute,
    RiskMetric,
    EvaluationCallback,
)


def core[ArrayT: ArrayLike](
    compute: Compute[ArrayT], costs: ArrayT, gamma: float
) -> ArrayT:
    costs_sum = compute.sum(costs, axis=0)
    mean = compute.mean(costs_sum, axis=1)
    variance = compute.var(costs_sum, axis=1)
    return compute.axpby(x=mean, b=gamma, y=variance)


@dataclass(frozen=True)
class MeanVariance[
    TrajectoriesT,
    UncertaintySamplesT,
    CostsT: Costs,
    RiskT: Risk,
    ArrayT: ArrayLike,
](RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]):
    cost: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT]
    backend: Backend[CostsT, RiskT, ArrayT]
    sampler: Sampler[UncertaintySamplesT]
    gamma: float
    callback: EvaluationCallback[CostsT, RiskT]

    def __post_init__(self) -> None:
        assert self.gamma >= 0.0, "Gamma must be non-negative."

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

        result = self.backend.execute(core, costs, self.gamma)
        risk = self.backend.to_risk(result, time_steps=T)
        self.callback(costs, risk)

        return risk

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "MeanVariance[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return MeanVariance(
            cost=self.cost,
            backend=self.backend,
            sampler=sampler,
            gamma=self.gamma,
            callback=self.callback,
        )

    def on_evaluation(
        self, callback: EvaluationCallback[CostsT, RiskT]
    ) -> "MeanVariance[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return MeanVariance(
            cost=self.cost,
            backend=self.backend,
            sampler=self.sampler,
            gamma=self.gamma,
            callback=callback,
        )
