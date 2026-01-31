from typing import Any, Protocol, NamedTuple, overload

from numtypes import Shape, Dims, Array


class InsufficientSampleWarning(UserWarning):
    """Warning raised when there are insufficient samples for accurate risk computation."""


class ArrayLike[ShapeT: Shape](Protocol):
    def __array__(self) -> Array[ShapeT]:
        """Converts the object to a NumPy array with the given shape."""
        ...

    @property
    def shape(self) -> ShapeT | tuple[int, ...]:
        """Shape of the array like object."""
        ...


type Costs[T: int = Any, M: int = Any, N: int = Any] = ArrayLike[Dims[T, M, N]]
"""A costs array of shape (time steps, trajectories, uncertainty samples)."""

type Risk[T: int = Any, M: int = Any] = ArrayLike[Dims[T, M]]
"""A risk array of shape (time steps, trajectories)."""


class BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT: Costs](Protocol):
    def __call__(
        self, *, trajectories: TrajectoriesT, uncertainties: UncertaintySamplesT
    ) -> CostsT:
        """Describes the cost function that should be used for evaluating risk.

        Returns:
            An array like object of shape (M, N) where M is the number of trajectories
            and N is the number of uncertainty samples.
        """
        ...


class TrajectoriesProvider[TrajectoriesT](Protocol):
    def get(self) -> TrajectoriesT:
        """Provides the batch of trajectories for which the risk metric should be computed."""
        ...

    @property
    def time_steps(self) -> int:
        """Number of time steps in the provided trajectories."""
        ...

    @property
    def trajectory_count(self) -> int:
        """Number of trajectories provided."""
        ...


class Uncertainties[UncertaintySamplesT](Protocol):
    def sample(self, count: int) -> UncertaintySamplesT:
        """Returns samples from the distribution(s) of the uncertain variable(s)."""
        ...


class Compute[ArrayT: ArrayLike](Protocol):
    def sum(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Computes the sum of the given data along the specified axis."""
        ...

    def mean(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Computes the mean of the given data along the specified axis."""
        ...

    def var(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Computes the variance of the given data along the specified axis."""
        ...

    def quantile(self, data: ArrayT, *, q: float, axis: int) -> ArrayT:
        """Computes the q-th quantile of the given data along the specified axis."""
        ...

    def sort(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Sorts the given data along the specified axis."""
        ...

    def take(self, data: ArrayT, *, indices: ArrayT, axis: int) -> ArrayT:
        """Takes elements from the given data at the specified indices along the axis."""
        ...

    def exp(self, data: ArrayT) -> ArrayT:
        """Computes the element-wise exponential of the given data."""
        ...

    def log(self, data: ArrayT) -> ArrayT:
        """Computes the element-wise natural logarithm of the given data."""
        ...

    def max(self, data: ArrayT, *, axis: int, keepdims: bool = False) -> ArrayT:
        """Computes the maximum of the given data along the specified axis."""
        ...

    def arange(self, start: int, stop: int) -> ArrayT:
        """Returns evenly spaced values within a given interval."""
        ...

    def axpby(self, *, a: float = 1.0, x: ArrayT, b: float = 1.0, y: ArrayT) -> ArrayT:
        """Computes the operation a * x + b * y."""
        ...

    def scale(self, scalar: float, data: ArrayT) -> ArrayT:
        """Multiplies the given data by the scalar."""
        ...

    def subtract(self, x: ArrayT, y: ArrayT) -> ArrayT:
        """Computes x - y with broadcasting."""
        ...


class ComputeFunction[T, ArrayT: ArrayLike, *Args](Protocol):
    def __call__(self, compute: Compute[ArrayT], costs: ArrayT, *args: *Args) -> T:
        """A pure function that performs computations using the provided Compute namespace."""
        ...


class Backend[CostsT: Costs, RiskT: Risk, ArrayT: ArrayLike](Protocol):
    def execute[T, *Args](
        self,
        fn: ComputeFunction[T, ArrayT, *Args],
        costs: CostsT,
        *args: *Args,
        static_argument_indices: tuple[int, ...] | None = None,
    ) -> T:
        """Executes the given pure function with the provided arguments.

        Args:
            fn: A pure function that performs the computations.
            costs: An array like object representing the costs.
            *args: Additional arguments to pass to the function.
            static_argument_indices: Indices of arguments that should be treated as static
                (i.e., known at compile time) during execution.
        """
        ...

    @overload
    def to_risk(self, array: ArrayT) -> RiskT:
        """Converts the given array to the backend's risk type."""
        ...

    @overload
    def to_risk(self, array: ArrayT, *, time_steps: int) -> RiskT:
        """Converts the given array to the backend's risk type.

        Note:
            It is assumed that the provided array has dimensions (trajectories,). Thus, the
            risk values will be shared equally across all time steps to generate a risk of
            shape (time steps, trajectories).
        """
        ...


class SamplingResult[UncertaintySamplesT](NamedTuple):
    samples: UncertaintySamplesT
    sample_count: int


class Sampler[UncertaintySamplesT](Protocol):
    def sample_from(
        self, uncertainties: Uncertainties[UncertaintySamplesT]
    ) -> SamplingResult[UncertaintySamplesT]:
        """Samples from the given uncertainties."""
        ...


class EvaluationCallback[CostsT: Costs, RiskT: Risk](Protocol):
    def __call__(self, costs: CostsT, risk: RiskT) -> None:
        """Called with the computed costs and risk values.

        Args:
            costs: The (T, M, N) cost array from the batch cost function.
            risk: The (T, M) risk array from the metric.
        """
        ...


class RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT: Costs, RiskT: Risk](
    Protocol
):
    def compute(
        self,
        *,
        trajectories: TrajectoriesProvider[TrajectoriesT],
        uncertainties: Uncertainties[UncertaintySamplesT],
    ) -> RiskT:
        """Computes the risk metric for the given trajectories and uncertainties."""
        ...

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]":
        """Returns a new risk metric that uses the given sampler to sample from uncertainties."""
        ...

    def on_evaluation(
        self, callback: EvaluationCallback[CostsT, RiskT]
    ) -> "RiskMetric[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT]":
        """Returns a new risk metric that invokes the callback after each evaluation.

        The callback receives the computed costs and risk values after each call to compute().

        Args:
            callback: The callback to invoke after each evaluation.
        """
        ...


def noop_callback(costs: Costs, risk: Risk) -> None:
    """A no-op callback that does nothing."""
    pass
