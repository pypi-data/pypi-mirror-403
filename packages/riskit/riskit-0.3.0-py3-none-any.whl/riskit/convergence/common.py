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

    @staticmethod
    def merge(
        first: "ComputedRisks | None",
        second: "ComputedRisks | None",
    ) -> "ComputedRisks | None":
        """Merges two risk computation results, combining their sample counts."""
        if first is None:
            return second

        if second is None:
            return first

        assert first.name == second.name, (
            f"Cannot merge computed risks for different metrics: {first.name} and {second.name}."
        )
        assert first.ground_truth == second.ground_truth, (
            f"Cannot merge computed risks with different ground truths. Got {first.ground_truth} and {second.ground_truth}."
        )
        assert first.sample_counts == second.sample_counts, (
            f"Sample counts must match to merge computed risks. Got {first.sample_counts} and {second.sample_counts}."
        )

        return ComputedRisks(
            name=first.name,
            risks_by_sample_count={
                n: np.concatenate(
                    [first.risks_by_sample_count[n], second.risks_by_sample_count[n]]
                )
                for n in first.sample_counts
            },
            ground_truth=first.ground_truth,
        )

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
        return tuple(sorted(self.risks_by_sample_count.keys()))

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
