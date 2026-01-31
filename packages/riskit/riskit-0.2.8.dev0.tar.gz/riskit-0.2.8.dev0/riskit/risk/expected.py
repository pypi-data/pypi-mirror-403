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
    RiskMetric,
    EvaluationCallback,
)


def core[ArrayT: ArrayLike](compute: Compute[ArrayT], costs: ArrayT) -> ArrayT:
    return compute.mean(costs, axis=2)


@dataclass(frozen=True)
class ExpectedValue[
    TrajectoriesT,
    UncertaintySamplesT,
    CostsT: Costs,
    RiskT: Risk,
    ArrayT: ArrayLike,
](RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]):
    cost: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT]
    backend: Backend[CostsT, RiskT, ArrayT]
    sampler: Sampler[UncertaintySamplesT]
    callback: EvaluationCallback[CostsT, RiskT]

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

        result = self.backend.execute(core, costs)
        risk = self.backend.to_risk(result)
        self.callback(costs, risk)

        return risk

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "ExpectedValue[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ExpectedValue(
            cost=self.cost,
            backend=self.backend,
            sampler=sampler,
            callback=self.callback,
        )

    def on_evaluation(
        self, callback: EvaluationCallback[CostsT, RiskT]
    ) -> "ExpectedValue[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ExpectedValue(
            cost=self.cost,
            backend=self.backend,
            sampler=self.sampler,
            callback=callback,
        )
