from typing import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property

from numtypes import Array, Dim1

import numpy as np


@dataclass(frozen=True)
class ComputedRisks:
    name: str
    risks_by_sample_count: Mapping[int, Array[Dim1]]
    ground_truth: float | None

    def __post_init__(self) -> None:
        assert len(self.risks_by_sample_count) > 0, (
            "At least one sample count with computed risks is required."
        )

    def relative_errors(self) -> Array[Dim1] | None:
        """Computes relative errors (|estimate - truth| / |truth|) at each sample count, if
        ground truth is provided."""
        if self.ground_truth is None:
            return

        truth = self.ground_truth

        return (
            np.abs(self.estimates - truth)
            if self.error_is_absolute
            else np.abs(self.estimates - truth) / abs(truth)
        )

    @property
    def error_is_absolute(self) -> bool:
        """Indicates if absolute error is used due to near-zero ground truth."""
        return self.ground_truth is not None and abs(self.ground_truth) < 1e-10

    @cached_property
    def sample_counts(self) -> Sequence[int]:
        """Returns the sorted sample counts used in the analysis."""
        return sorted(self.risks_by_sample_count.keys())

    @cached_property
    def estimates(self) -> Array[Dim1]:
        """Returns the mean estimates at each sample count."""
        risks = self.risks_by_sample_count

        return np.asarray([risks[n].mean() for n in self.sample_counts])

    @cached_property
    def closest_estimate(self) -> float:
        """Returns the mean estimate at the maximum sample count."""
        return self.estimates[-1]

    @cached_property
    def standard_errors(self) -> Array[Dim1]:
        """Returns the standard errors at each sample count."""
        risks = self.risks_by_sample_count
        return np.asarray(
            [np.std(risks[n], ddof=1) for n in self.sample_counts], dtype=np.float64
        )

    @cached_property
    def max_sample_count(self) -> int:
        """Returns the maximum sample count used in the analysis."""
        return max(self.risks_by_sample_count.keys())
