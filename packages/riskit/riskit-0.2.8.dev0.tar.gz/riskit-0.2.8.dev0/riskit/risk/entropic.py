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


def core[ArrayT: ArrayLike](
    compute: Compute[ArrayT], costs: ArrayT, theta: float
) -> ArrayT:
    trajectory_costs = compute.sum(costs, axis=0)

    # NOTE: log-sum-exp trick for numerical stability:
    # (1/theta) * log(mean(exp(theta * x)))
    # = (1/theta) * (max_val + log(mean(exp(theta * x - max_val))))
    scaled = compute.scale(theta, trajectory_costs)
    max_val = compute.max(scaled, axis=1, keepdims=True)
    shifted = compute.subtract(scaled, max_val)
    shifted_exp = compute.exp(shifted)
    mean_exp = compute.mean(shifted_exp, axis=1)
    log_mean_exp = compute.log(mean_exp)
    max_squeezed = compute.max(scaled, axis=1, keepdims=False)
    sum_log = compute.axpby(a=1.0, x=max_squeezed, b=1.0, y=log_mean_exp)
    return compute.scale(1.0 / theta, sum_log)


@dataclass(frozen=True)
class EntropicRisk[
    TrajectoriesT,
    UncertaintySamplesT,
    CostsT: Costs,
    RiskT: Risk,
    ArrayT: ArrayLike,
](RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]):
    cost: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT]
    backend: Backend[CostsT, RiskT, ArrayT]
    sampler: Sampler[UncertaintySamplesT]
    theta: float
    callback: EvaluationCallback[CostsT, RiskT]

    def __post_init__(self) -> None:
        assert self.theta > 0.0, "Theta must be positive."

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

        result = self.backend.execute(core, costs, self.theta)
        risk = self.backend.to_risk(result, time_steps=T)
        self.callback(costs, risk)

        return risk

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "EntropicRisk[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return EntropicRisk(
            cost=self.cost,
            backend=self.backend,
            sampler=sampler,
            theta=self.theta,
            callback=self.callback,
        )

    def on_evaluation(
        self, callback: EvaluationCallback[CostsT, RiskT]
    ) -> "EntropicRisk[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return EntropicRisk(
            cost=self.cost,
            backend=self.backend,
            sampler=self.sampler,
            theta=self.theta,
            callback=callback,
        )
