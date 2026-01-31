from typing import Any, Protocol, NamedTuple, Self, Annotated, overload, cast, Callable

from riskit.risk.common import Backend, Compute

from numtypes import Array, Dims, Shape, AnyShape, shape_of

import numpy as np


class NumPyCompute(Compute[Array]):
    def sum(self, data: Array, *, axis: int) -> Array:
        return np.sum(data, axis=axis)

    def mean(self, data: Array, *, axis: int) -> Array:
        return np.mean(data, axis=axis)

    def var(self, data: Array, *, axis: int) -> Array:
        return np.var(data, axis=axis)

    def quantile(self, data: Array, *, q: float, axis: int) -> Array:
        return np.quantile(data, q, axis=axis)

    def sort(self, data: Array, *, axis: int) -> Array:
        return np.sort(data, axis=axis)

    def take(self, data: Array, *, indices: Array, axis: int) -> Array:
        return np.take(data, indices=indices, axis=axis)  # type: ignore

    def exp(self, data: Array) -> Array:
        return np.exp(data)

    def log(self, data: Array) -> Array:
        return np.log(data)

    def max(self, data: Array, *, axis: int, keepdims: bool = False) -> Array:
        return np.max(data, axis=axis, keepdims=keepdims)

    def arange(self, start: int, stop: int) -> Array:
        return np.arange(start, stop)  # type: ignore

    def axpby[S: Shape](
        self, *, a: float = 1.0, x: Array[S], b: float = 1.0, y: Array[S]
    ) -> Array[S]:
        result = a * x + b * y
        assert shape_of(result, matches=x.shape)
        return result

    def scale(self, scalar: float, data: Array) -> Array:
        return scalar * data

    def subtract(self, x: Array, y: Array) -> Array:
        return x - y


def numpy_backend() -> "NumPyBackend":
    return NumPyBackend()


class NumPyBackend(
    Backend["NumPyCosts", "NumPyRisk", Array],
):
    @staticmethod
    def create() -> "NumPyBackend":
        return numpy_backend()

    def execute[T](
        self,
        fn: Callable[[Compute[Array], Array], T],
        costs: "NumPyCosts",
        *args: Any,
        static_argument_indices: tuple[int, ...] | None = None,
    ) -> T:
        return fn(NumPyCompute(), costs, *args)

    @overload
    def to_risk(self, array: Array) -> "NumPyRisk": ...

    @overload
    def to_risk(self, array: Array, *, time_steps: int) -> "NumPyRisk": ...

    def to_risk[T: int, M: int](
        self,
        array: Array[Dims[T, M]] | Array[Dims[M]] | Array,
        *,
        time_steps: T | None = None,
    ) -> "NumPyRisk[T, M]":
        match array.shape:
            case (M,):
                assert time_steps is not None, (
                    f"Received array of shape ({M},). You must specify the number of time steps "
                    "the risk should be padded to."
                )

                risk = np.full((time_steps, M), array / time_steps)

                assert shape_of(risk, matches=(time_steps, M), name="risk")

                return cast(NumPyRisk, risk)

            case (T, M):
                assert time_steps is None, (
                    f"Received array of shape ({T}, {M}). Do not specify time_steps in this case."
                )
                assert shape_of(array, matches=(T, M), name="risk")
                return cast(NumPyRisk, array)
            case _:
                assert False, (
                    f"Cannot convert array of shape {array.shape} to NumPyRisk."
                )


type NumPyInputs[T: int = Any, D_u: int = Any, M: int = Any] = Array[Dims[T, D_u, M]]
"""Batch of control inputs. The dimensions are (time steps, control dimensions, trajectories)."""

type NumPyStates[T: int = Any, D_x: int = Any, M: int = Any] = Array[Dims[T, D_x, M]]
"""Batch of states. The dimensions are (time steps, state dimensions, trajectories)."""

type NumPyUncertaintySamples[ShapeT: Shape = AnyShape, N: int = Any] = Array[
    Dims[*ShapeT, N]
]
"""Batch of uncertainty samples. The dimensions are (...uncertainty dimensions, uncertainty samples)."""

type NumPyCosts[T: int = Any, M: int = Any, N: int = Any] = Annotated[
    Array[Dims[T, M, N]], numpy_backend
]
"""Batch of costs. The dimensions are (time steps, trajectories, uncertainty samples)."""

type NumPyRisk[T: int = Any, M: int = Any] = Array[Dims[T, M]]
"""Batch of risk values. The dimensions are (time steps, trajectories)."""


class NumPyUncertainty[ShapeT: Shape](Protocol):
    def sample[N: int](self, count: N) -> NumPyUncertaintySamples[ShapeT, N]:
        """Returns samples from the distribution of the uncertain variable(s)."""
        ...


class NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT](Protocol):
    def __call__(
        self, *, trajectories: TrajectoriesT, uncertainties: UncertaintySamplesT
    ) -> NumPyCosts:
        """Describes the cost function that should be used for evaluating risk."""
        ...


class NumPyInputAndState[T: int, D_u: int, D_x: int, M: int](NamedTuple):
    u: NumPyInputs[T, D_u, M]
    x: NumPyStates[T, D_x, M]

    def get(self) -> Self:
        return self

    @property
    def time_steps(self) -> T:
        return self.u.shape[0]

    @property
    def trajectory_count(self) -> M:
        return self.u.shape[2]
