from typing import Sequence, NamedTuple
from dataclasses import dataclass
from functools import lru_cache

from numtypes import Array, Dim1

import numpy as np


@dataclass(frozen=True)
class ConvergenceFit:
    """Power-law fit: error ∝ N^(-rate)."""

    intercept: float
    rate: float
    r_squared: float

    class MaskedPoints(NamedTuple):
        sample_counts: Array[Dim1]
        errors: Array[Dim1]
        standard_errors: Array[Dim1]

        @property
        def sufficient(self) -> bool:
            return self.sample_counts.shape[0] >= 2

    class PowerLawCoefficients(NamedTuple):
        intercept: float
        rate: float

    @staticmethod
    def from_data(
        *,
        sample_counts: Sequence[int],
        errors: Array[Dim1],
        standard_errors: Array[Dim1],
        min_error: float,
    ) -> "ConvergenceFit":
        """Fits a power-law model using weighted least squares."""
        masked = ConvergenceFit._filter_converged_points(
            sample_counts=sample_counts,
            errors=errors,
            standard_errors=standard_errors,
            min_error=min_error,
        )

        if not masked.sufficient:
            # NOTE: Likely already converged.
            return ConvergenceFit(intercept=0, rate=0.5, r_squared=0.0)

        log_sample_counts = np.log(masked.sample_counts)
        log_errors = np.log(masked.errors)

        intercept, rate = ConvergenceFit._fit_power_law(
            log_sample_counts=log_sample_counts, log_errors=log_errors
        )
        r_squared = ConvergenceFit._r_squared(
            log_sample_counts=log_sample_counts,
            log_errors=log_errors,
            intercept=intercept,
            rate=rate,
        )

        return ConvergenceFit(intercept=intercept, rate=rate, r_squared=r_squared)

    def samples_for_error(self, target: float) -> int | None:
        """Estimates the number of samples needed to achieve the target error."""
        if self.rate <= 0:
            return None

        log_n = (self.intercept - np.log(target)) / self.rate
        return max(1, int(np.exp(log_n)))

    @staticmethod
    def _filter_converged_points(
        *,
        sample_counts: Sequence[int],
        errors: Array[Dim1],
        standard_errors: Array[Dim1],
        min_error: float,
    ) -> "ConvergenceFit.MaskedPoints":
        mask = np.array(errors) > min_error

        return ConvergenceFit.MaskedPoints(
            sample_counts=np.asarray(sample_counts)[mask],
            errors=np.asarray(errors)[mask],
            standard_errors=np.asarray(standard_errors)[mask],
        )

    @staticmethod
    def _fit_power_law(
        *, log_sample_counts: Array[Dim1], log_errors: Array[Dim1]
    ) -> "ConvergenceFit.PowerLawCoefficients":
        slope, intercept = np.polyfit(log_sample_counts, log_errors, 1)

        return ConvergenceFit.PowerLawCoefficients(
            intercept=float(intercept), rate=-float(slope)
        )

    @staticmethod
    def _r_squared(
        *,
        log_sample_counts: Array[Dim1],
        log_errors: Array[Dim1],
        intercept: float,
        rate: float,
    ) -> float:
        predicted = -rate * log_sample_counts + intercept

        mean = np.mean(log_errors)
        ss_res = np.sum((log_errors - predicted) ** 2)
        ss_tot = np.sum((log_errors - mean) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

        return float(r_squared)


@dataclass(frozen=True, eq=False)
class MetricFit:
    """Convergence fit for one (test, metric) pair."""

    test_name: str
    metric_name: str

    sample_counts: Sequence[int]
    errors: Array[Dim1]
    standard_errors: Array[Dim1]

    @lru_cache
    def get_for(self, *, min_error: float) -> ConvergenceFit:
        return ConvergenceFit.from_data(
            sample_counts=self.sample_counts,
            errors=self.errors,
            standard_errors=self.standard_errors,
            min_error=min_error,
        )

    @property
    def min_sample_count(self) -> int:
        """Returns the initial sample count."""
        return self.sample_counts[0]

    @property
    def max_sample_count(self) -> int:
        """Returns the final sample count."""
        return self.sample_counts[-1]

    @property
    def min_error(self) -> float:
        """Returns the final observed error."""
        return float(self.errors.min())

    @property
    def max_error(self) -> float:
        """Returns the initial observed error."""
        return float(self.errors.max())
