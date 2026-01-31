from typing import overload

from riskit.risk import (
    BatchCostFunction,
    Backend,
    RiskMetric,
    Risk,
    Costs,
    ArrayLike,
    ExpectedValue,
    MeanVariance,
    ValueAtRisk,
    ConditionalValueAtRisk,
    EntropicRisk,
    noop_callback,
)
from riskit.compute import (
    infer,
    NumPyBatchCostFunction,
    NumPyCosts,
    NumPyRisk,
    JaxBatchCostFunction,
    JaxCosts,
    JaxRisk,
)
from riskit.sampler import sampler


class risk:
    @overload
    @staticmethod
    def expected_value_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyCosts, NumPyRisk]:
        """Creates an Expected Value risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def expected_value_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxCosts, JaxRisk]:
        """Creates an Expected Value risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def expected_value_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        backend: Backend[CostsT, RiskT, ArrayT],
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        """Creates an Expected Value risk metric using the specified backend."""
        ...

    @staticmethod
    def expected_value_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        return ExpectedValue(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
            callback=noop_callback,
        )

    @overload
    @staticmethod
    def mean_variance_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyCosts, NumPyRisk]:
        """Creates a Mean-Variance risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def mean_variance_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxCosts, JaxRisk]:
        """Creates a Mean-Variance risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def mean_variance_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT],
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        """Creates a Mean-Variance risk metric using the specified backend."""
        ...

    @staticmethod
    def mean_variance_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        return MeanVariance(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
            gamma=gamma,
            callback=noop_callback,
        )

    @overload
    @staticmethod
    def var_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyCosts, NumPyRisk]:
        """Creates a Value at Risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def var_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxCosts, JaxRisk]:
        """Creates a Value at Risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def var_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT],
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        """Creates a Value at Risk metric using the specified backend."""
        ...

    @staticmethod
    def var_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        return ValueAtRisk(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
            alpha=alpha,
            callback=noop_callback,
        )

    @overload
    @staticmethod
    def cvar_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyCosts, NumPyRisk]:
        """Creates a Conditional Value at Risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def cvar_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxCosts, JaxRisk]:
        """Creates a Conditional Value at Risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def cvar_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT],
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        """Creates a Conditional Value at Risk metric using the specified backend."""
        ...

    @staticmethod
    def cvar_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
        alpha: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        return ConditionalValueAtRisk(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
            alpha=alpha,
            callback=noop_callback,
        )

    @overload
    @staticmethod
    def entropic_risk_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        theta: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyCosts, NumPyRisk]:
        """Creates an Entropic Risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def entropic_risk_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        theta: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxCosts, JaxRisk]:
        """Creates an Entropic Risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def entropic_risk_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT],
        theta: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        """Creates an Entropic Risk metric using the specified backend."""
        ...

    @staticmethod
    def entropic_risk_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
        theta: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]:
        return EntropicRisk(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
            theta=theta,
            callback=noop_callback,
        )
