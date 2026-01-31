from typing import Mapping, Sequence, Final, Protocol, TYPE_CHECKING
from dataclasses import dataclass
from functools import partial

from riskit.convergence.common import ComputedRisks


import numpy as np


if TYPE_CHECKING:
    from plotly.graph_objs import Figure
    from anyio import Path as AsyncPath


METRIC_COLORS: Final = [
    "#E63946",
    "#2A9D8F",
    "#E9C46A",
    "#F4A261",
    "#9B5DE5",
    "#00BBF9",
    "#FF6B6B",
    "#4ECDC4",
]


def to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


class Analysis(Protocol):
    @property
    def sample_counts(self) -> Sequence[int]:
        """Returns the sample counts used in the analysis."""
        ...

    @property
    def results_by_metric(self) -> Mapping[str, ComputedRisks]:
        """Mapping from metric name to computed risks."""
        ...


@dataclass(frozen=True)
class AnalysisVisualizer:
    async def save(self, analysis: Analysis, *, to: "AsyncPath") -> None:
        from anyio import create_task_group

        async with create_task_group() as tasks:
            tasks.start_soon(partial(self._save_figure, to=to), self._figure(analysis))
            tasks.start_soon(
                partial(
                    self._save_figure,
                    to=to.with_name(to.stem + "-relative-error" + to.suffix),
                ),
                self._relative_error_figure(analysis),
            )

    def _figure(self, analysis: Analysis) -> "Figure":
        import plotly.graph_objects as go

        figure = go.Figure()

        for i, (_, result) in enumerate(analysis.results_by_metric.items()):
            color = METRIC_COLORS[i % len(METRIC_COLORS)]
            self._add_estimate_trace(figure, result, color=color)

            if result.ground_truth is not None:
                self._add_ground_truth_line(figure, result, color=color)

        self._apply_convergence_layout(figure)

        return figure

    def _relative_error_figure(self, analysis: Analysis) -> "Figure":
        import plotly.graph_objects as go

        figure = go.Figure()

        for i, (name, result) in enumerate(analysis.results_by_metric.items()):
            if (errors := result.relative_errors()) is None:
                continue

            self._add_relative_error_trace(
                figure,
                sample_counts=result.sample_counts,
                errors=errors.tolist(),
                name=f"{name} (abs)" if result.error_is_absolute else name,
                color=METRIC_COLORS[i % len(METRIC_COLORS)],
                is_absolute=result.error_is_absolute,
            )

        self._add_theoretical_convergence_lines(figure, analysis)
        self._apply_relative_error_layout(figure)

        return figure

    def _add_estimate_trace(
        self, figure: "Figure", result: ComputedRisks, *, color: str
    ) -> None:
        import plotly.graph_objects as go

        std_errors = result.standard_errors

        upper = [e + s for e, s in zip(result.estimates, std_errors)]
        lower = [e - s for e, s in zip(result.estimates, std_errors)]

        figure.add_trace(
            go.Scatter(
                x=result.sample_counts,
                y=upper,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        figure.add_trace(
            go.Scatter(
                x=result.sample_counts,
                y=lower,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor=to_rgba(color, 0.2),
                name=f"{result.name} ±σ",
                legendgroup=result.name,
                showlegend=True,
                hoverinfo="skip",
            )
        )

        figure.add_trace(
            go.Scatter(
                x=result.sample_counts,
                y=result.estimates,
                mode="lines+markers",
                name=result.name,
                legendgroup=result.name,
                line=dict(color=color, width=2),
                marker=dict(size=6),
                customdata=list(zip(result.estimates, std_errors)),
                hovertemplate=(
                    f"<b>{result.name}</b><br>"
                    "N = %{x}<br>"
                    "Estimate = %{customdata[0]:.4f} ± %{customdata[1]:.4f}<extra></extra>"
                ),
            )
        )

    def _add_ground_truth_line(
        self, figure: "Figure", result: ComputedRisks, *, color: str
    ) -> None:
        import plotly.graph_objects as go

        assert result.ground_truth is not None

        figure.add_trace(
            go.Scatter(
                x=[result.sample_counts[0], result.sample_counts[-1]],
                y=[result.ground_truth, result.ground_truth],
                mode="lines",
                name=f"{result.name} (truth)",
                line=dict(color=color, width=2, dash="dash"),
                hovertemplate=(
                    f"<b>{result.name} Ground Truth</b><br>"
                    f"Value = {result.ground_truth:.4f}<extra></extra>"
                ),
            )
        )

    def _add_relative_error_trace(
        self,
        figure: "Figure",
        *,
        sample_counts: Sequence[int],
        errors: Sequence[float],
        name: str,
        color: str,
        is_absolute: bool = False,
    ) -> None:
        import plotly.graph_objects as go

        error_label = "Absolute Error" if is_absolute else "Relative Error"

        figure.add_trace(
            go.Scatter(
                x=sample_counts,
                y=errors,
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=2),
                marker=dict(size=6),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "N = %{x}<br>"
                    f"{error_label} = %{{y:.4e}}<extra></extra>"
                ),
            )
        )

    def _add_theoretical_convergence_lines(
        self, figure: "Figure", analysis: Analysis
    ) -> None:
        import plotly.graph_objects as go

        min_n = min(analysis.sample_counts)
        max_n = max(analysis.sample_counts)

        n_range = np.logspace(np.log10(min_n), np.log10(max_n), 50)
        theoretical_rate = 1.0 / np.sqrt(n_range)
        normalized_rate = theoretical_rate * 0.5

        figure.add_trace(
            go.Scatter(
                x=n_range.tolist(),
                y=normalized_rate.tolist(),
                mode="lines",
                name="O(1/√N) reference",
                line=dict(color="#999999", width=1, dash="dot"),
                hoverinfo="skip",
            )
        )

    def _apply_convergence_layout(self, figure: "Figure") -> None:
        figure.update_layout(
            title=dict(
                text="Risk Metric Convergence Analysis",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Number of Samples (N)",
            yaxis_title="Risk Estimate",
            xaxis=dict(type="log", tickformat=",d"),
            yaxis=dict(rangemode="tozero"),
            showlegend=True,
            template="plotly_white",
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#ddd",
                borderwidth=1,
            ),
            hovermode="x unified",
            margin=dict(r=200),
        )

    def _apply_relative_error_layout(self, figure: "Figure") -> None:
        figure.update_layout(
            title=dict(
                text="Convergence Rate Analysis (Log-Log Scale)",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Number of Samples (N)",
            yaxis_title="Relative Error |estimate - truth| / |truth|",
            xaxis=dict(type="log", tickformat=",d"),
            yaxis=dict(type="log", tickformat=".0e"),
            showlegend=True,
            template="plotly_white",
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#ddd",
                borderwidth=1,
            ),
            hovermode="x unified",
            margin=dict(r=200),
        )

    async def _save_figure(self, figure: "Figure", *, to: "AsyncPath") -> None:
        await to.parent.mkdir(parents=True, exist_ok=True)

        suffix = to.suffix.lower()

        match suffix:
            case ".html":
                content = figure.to_html()
                await to.write_text(content, encoding="utf-8")

            case ".json":
                content = figure.to_json()
                await to.write_text(str(content), encoding="utf-8")

            case ".png" | ".svg" | ".pdf":
                self._check_kaleido_installed()
                content = figure.to_image(format=suffix[1:])
                await to.write_bytes(content)

            case _:
                raise ValueError(
                    f"Unsupported file format '{suffix}'. "
                    "Supported: .html, .json, .png, .svg, .pdf"
                )

    def _check_kaleido_installed(self) -> None:
        try:
            import kaleido as kaleido  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "kaleido is required for image export. "
                "Install it with: pip install kaleido"
            ) from e
