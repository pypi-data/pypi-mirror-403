from typing import Protocol, NamedTuple, Self, Annotated, Any, cast, overload, Callable

from riskit.type import jaxtyped
from riskit.risk.common import Backend, Compute

from jax import Array as JaxArray
from jaxtyping import Float
from numtypes import Shape, AnyShape

import jax
import jax.numpy as jnp


class JaxCompute(Compute[JaxArray]):
    def sum(self, data: JaxArray, *, axis: int) -> JaxArray:
        return jnp.sum(data, axis=axis)

    def mean(self, data: JaxArray, *, axis: int) -> JaxArray:
        return jnp.mean(data, axis=axis)

    def var(self, data: JaxArray, *, axis: int) -> JaxArray:
        return jnp.var(data, axis=axis)

    def quantile(self, data: JaxArray, *, q: float, axis: int) -> JaxArray:
        return jnp.quantile(data, q, axis=axis)

    def sort(self, data: JaxArray, *, axis: int) -> JaxArray:
        return jnp.sort(data, axis=axis)

    def take(self, data: JaxArray, *, indices: JaxArray, axis: int) -> JaxArray:
        return jnp.take(data, indices=indices, axis=axis)

    def exp(self, data: JaxArray) -> JaxArray:
        return jnp.exp(data)

    def log(self, data: JaxArray) -> JaxArray:
        return jnp.log(data)

    def max(self, data: JaxArray, *, axis: int, keepdims: bool = False) -> JaxArray:
        return jnp.max(data, axis=axis, keepdims=keepdims)

    def arange(self, start: int, stop: int) -> JaxArray:
        return jnp.arange(start, stop)

    def axpby(
        self, *, a: float = 1.0, x: JaxArray, b: float = 1.0, y: JaxArray
    ) -> JaxArray:
        return a * x + b * y

    def scale(self, scalar: float, data: JaxArray) -> JaxArray:
        return scalar * data

    def subtract(self, x: JaxArray, y: JaxArray) -> JaxArray:
        return x - y


_JIT_CACHE: dict[tuple[int, tuple[int, ...] | None], Callable[..., Any]] = {}
_JAX_COMPUTE = JaxCompute()


def jax_backend() -> "JaxBackend":
    return JaxBackend()


class JaxBackend(
    Backend["JaxCosts", "JaxRisk", JaxArray],
):
    @staticmethod
    def create() -> "JaxBackend":
        return jax_backend()

    def execute[T](
        self,
        fn: Callable[[Compute[JaxArray], JaxArray], T],
        costs: "JaxCosts",
        *args: Any,
        static_argument_indices: tuple[int, ...] | None = None,
    ) -> T:
        assert fn.__closure__ is None, (
            "Do not use risk metric functions with closures with JAX backend."
        )

        cache_key = (id(fn), static_argument_indices)

        if cache_key not in _JIT_CACHE:
            # NOTE: static_argument_indices shifted by 1 to account for compute being static
            adjusted_static = (
                (0,)
                if static_argument_indices is None
                else (0,) + tuple(i + 1 for i in static_argument_indices)
            )
            _JIT_CACHE[cache_key] = jax.jit(fn, static_argnums=adjusted_static)

        return _JIT_CACHE[cache_key](_JAX_COMPUTE, costs, *args)

    @overload
    def to_risk(self, array: Float[JaxArray, "T M"]) -> "JaxRisk": ...

    @overload
    def to_risk(self, array: Float[JaxArray, "M"], *, time_steps: int) -> "JaxRisk": ...

    @jaxtyped
    def to_risk(
        self,
        array: Float[JaxArray, "T M"] | Float[JaxArray, "M"],
        *,
        time_steps: int | None = None,
    ) -> "JaxRisk":
        match array.shape:
            case (M,):
                assert time_steps is not None, (
                    f"Received array of shape ({M},). You must specify the number of time steps "
                    "the risk should be padded to."
                )
                return jnp.broadcast_to(array / time_steps, (time_steps, M))

            case (T, M):
                assert time_steps is None, (
                    f"Received array of shape ({T}, {M}). Do not specify time_steps in this case."
                )
                return array
            case _:
                assert False, f"Unexpected array shape {array.shape} for risk."


type JaxInputs[T: int = Any, D_u: int = Any, M: int = Any] = Float[JaxArray, "T D_u M"]
"""Batch of control inputs. The dimensions are (time steps, control dimensions, trajectories)."""

type JaxStates[T: int = Any, D_x: int = Any, M: int = Any] = Float[JaxArray, "T D_x M"]
"""Batch of states. The dimensions are (time steps, state dimensions, trajectories)."""

type JaxUncertaintySamples[ShapeT: Shape = AnyShape, N: int = Any] = Float[
    JaxArray, "*S N"
]
"""Batch of uncertainty samples. The dimensions are (...uncertainty dimensions, uncertainty samples)."""

type JaxCosts[T: int = Any, M: int = Any, N: int = Any] = Annotated[
    Float[JaxArray, "T M N"], jax_backend
]
"""Batch of costs. The dimensions are (time steps, trajectories, uncertainty samples)."""

type JaxRisk[T: int = Any, M: int = Any] = Float[JaxArray, "T M"]
"""Batch of risk values. The dimensions are (time steps, trajectories)."""


class JaxUncertainty[ShapeT: Shape](Protocol):
    def sample[N: int](self, count: N) -> JaxUncertaintySamples[ShapeT, N]:
        """Returns samples from the distribution of the uncertain variable(s)."""
        ...


class JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT](Protocol):
    def __call__(
        self, *, trajectories: TrajectoriesT, uncertainties: UncertaintySamplesT
    ) -> JaxCosts:
        """Describes the cost function that should be used for evaluating risk."""
        ...


class JaxInputAndState[T: int, D_u: int, D_x: int, M: int](NamedTuple):
    u: JaxInputs[T, D_u, M]
    x: JaxStates[T, D_x, M]

    def get(self) -> Self:
        return self

    @property
    def time_steps(self) -> T:
        return cast(T, self.u.shape[0])

    @property
    def trajectory_count(self) -> M:
        return cast(M, self.u.shape[2])
