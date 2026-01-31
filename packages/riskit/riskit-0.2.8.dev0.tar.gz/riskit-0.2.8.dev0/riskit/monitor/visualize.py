from typing import Literal, Mapping, Final, TYPE_CHECKING
from dataclasses import dataclass

from riskit.monitor.monitor import EvaluationData

from numtypes import Array, Dims

import numpy as np

if TYPE_CHECKING:
    from plotly.graph_objs import Figure
    from anyio import Path as AsyncPath

type ImageFormat = Literal["html", "png", "svg", "pdf", "json"]

RISK_COLORS: Final = [
    "#E63946",
    "#2A9D8F",
    "#E9C46A",
    "#F4A261",
    "#9B5DE5",
    "#00BBF9",
]


@dataclass(kw_only=True, frozen=True)
class SliderConfig:
    alpha_min: float
    alpha_max: float
    steps: int


@dataclass(frozen=True)
class VisualizationResult:
    figure: "Figure"

    async def save(self, *, to: "AsyncPath") -> None:
        """Saves the figure to the specified path.

        Args:
            to: The async path to save the figure to.
                Format is inferred from the file extension.
        """
        await to.parent.mkdir(parents=True, exist_ok=True)

        match fmt := self._infer_format(to.suffix):
            case "html":
                content = self.figure.to_html()
                await to.write_text(content, encoding="utf-8")

            case "json":
                content = self.figure.to_json()
                await to.write_text(str(content), encoding="utf-8")

            case "png" | "svg" | "pdf":
                self._check_kaleido_installed()
                content = self.figure.to_image(format=fmt)
                await to.write_bytes(content)

    def show(self) -> None:
        """Displays the figure."""
        self.figure.show()

    def _infer_format(self, suffix: str) -> ImageFormat:
        formats: dict[str, ImageFormat] = {
            ".html": "html",
            ".png": "png",
            ".svg": "svg",
            ".pdf": "pdf",
            ".json": "json",
        }

        if suffix not in formats:
            raise ValueError(
                f"Unsupported file format '{suffix}'. "
                f"Supported: {', '.join(formats.keys())}"
            )

        return formats[suffix]

    def _check_kaleido_installed(self) -> None:
        try:
            import kaleido as kaleido  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "kaleido is required for image export. "
                "Install it with: pip install kaleido"
            ) from e


class RiskMetricVisualizer:
    def plot(
        self,
        evaluations: Mapping[str, EvaluationData],
        *,
        trajectory_index: int = 0,
        time_step: int = 0,
        quantile_slider: SliderConfig | tuple[float, float, int] | None = None,
        show_histogram: bool = False,
        show_kde: bool = True,
        show_rug: bool = True,
    ) -> VisualizationResult:
        """Creates a visualization of the cost distribution and computed risks.

        Args:
            evaluations: Mapping from risk metric name to its evaluation data.
                All evaluations must have identical costs (same underlying distribution).
            trajectory_index: Which trajectory to visualize.
            time_step: Which time step to visualize.
            quantile_slider: If provided, adds an interactive alpha slider for
                VaR/CVaR verification. Tuple of (alpha_min, alpha_max, steps).
            show_histogram: Whether to show the histogram.
            show_kde: Whether to show the kernel density estimate.
            show_rug: Whether to show the rug plot of samples.
        """
        self._check_plotly_installed()
        import plotly.graph_objects as go

        costs, risks = self._extract_and_validate(
            evaluations,
            trajectory_index=trajectory_index,
            time_step=time_step,
        )
        y_max = self._compute_y_max(costs)

        figure = go.Figure()

        if show_histogram:
            self._add_histogram(figure, costs)

        if show_kde:
            self._add_kde(figure, costs)

        if show_rug:
            self._add_rug_plot(figure, costs)

        self._add_statistics(figure, costs, y_max=y_max)
        self._add_risk_lines(figure, risks, y_max=y_max)

        if quantile_slider is not None:
            self._add_quantile_slider(
                figure, costs, config=quantile_slider, y_max=y_max
            )

        self._apply_layout(
            figure,
            trajectory_index=trajectory_index,
            time_step=time_step,
            sample_count=len(costs),
            y_max=y_max,
        )

        return VisualizationResult(figure)

    def _check_plotly_installed(self) -> None:
        try:
            import plotly as plotly  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "Plotly is required for visualization. "
                "Install it with: pip install riskit[viz]"
            ) from e

    def _check_scipy_installed(self) -> None:
        try:
            import scipy as scipy  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "SciPy is required for certain visualizations. "
                "Install it with: pip install riskit[viz]"
            ) from e

    def _extract_and_validate[N: int = int](
        self,
        evaluations: Mapping[str, EvaluationData],
        *,
        trajectory_index: int,
        time_step: int,
    ) -> tuple[Array[Dims[N]], dict[str, float]]:
        assert len(evaluations) > 0, "At least one evaluation must be provided."

        reference_costs: Array[Dims[N]] | None = None
        risks: dict[str, float] = {}

        for name, evaluation in evaluations.items():
            reference_costs, selected_risk = self._extract_and_validate_single(
                name,
                evaluation,
                reference_costs=reference_costs,
                trajectory_index=trajectory_index,
                time_step=time_step,
            )

            risks[name] = selected_risk

        assert reference_costs is not None
        return reference_costs, risks

    def _extract_and_validate_single[N: int = int](
        self,
        name: str,
        evaluation: EvaluationData,
        *,
        reference_costs: Array[Dims[N]] | None,
        trajectory_index: int,
        time_step: int,
    ) -> tuple[Array[Dims[N]], float]:
        costs = np.asarray(evaluation.costs)
        risk = np.asarray(evaluation.risk)

        T, M, _ = costs.shape

        assert time_step < T, f"time_step {time_step} >= number of time steps {T}"
        assert trajectory_index < M, (
            f"trajectory_index {trajectory_index} >= number of trajectories {M}"
        )

        selected_costs = costs[time_step, trajectory_index, :]
        selected_risk = float(risk[time_step, trajectory_index])

        assert reference_costs is None or np.allclose(
            reference_costs, selected_costs
        ), (
            f"Costs for '{name}' differ from reference. "
            "All evaluations must have identical costs.\n"
            f"Reference costs: {reference_costs}\n"
            f"Current costs: {selected_costs}"
        )

        return selected_costs, selected_risk

    def _add_histogram[N: int = int](
        self, figure: "Figure", costs: Array[Dims[N]]
    ) -> None:
        import plotly.graph_objects as go

        figure.add_trace(
            go.Histogram(
                x=costs,
                name="Histogram",
                opacity=0.4,
                marker_color="#636EFA",
                histnorm="probability density",
                hovertemplate="Cost: %{x:.4f}<br>Density: %{y:.4f}<extra></extra>",
                legendgroup="distribution",
                legendgrouptitle_text="Distribution",
            )
        )

    def _add_kde[N: int = int](self, figure: "Figure", costs: Array[Dims[N]]) -> None:
        self._check_scipy_installed()

        from scipy.stats import gaussian_kde
        import plotly.graph_objects as go

        kde = gaussian_kde(costs)
        x_range = np.linspace(costs.min(), costs.max(), 500)
        density = kde(x_range)

        figure.add_trace(
            go.Scatter(
                x=x_range,
                y=density,
                mode="lines",
                name="KDE",
                line=dict(color="#636EFA", width=2),
                hovertemplate="Cost: %{x:.4f}<br>Density: %{y:.4f}<extra></extra>",
                legendgroup="distribution",
                legendgrouptitle_text="Distribution",
            )
        )

    def _add_rug_plot[N: int = int](
        self, figure: "Figure", costs: Array[Dims[N]]
    ) -> None:
        import plotly.graph_objects as go

        figure.add_trace(
            go.Scatter(
                x=costs,
                y=np.zeros_like(costs),
                mode="markers",
                name="Samples",
                marker=dict(
                    symbol="line-ns",
                    size=8,
                    color="#636EFA",
                    opacity=0.3,
                    line=dict(width=1, color="#636EFA"),
                ),
                hovertemplate="Cost: %{x:.4f}<extra></extra>",
                legendgroup="distribution",
                legendgrouptitle_text="Distribution",
            )
        )

    def _add_statistics[N: int = int](
        self, figure: "Figure", costs: Array[Dims[N]], *, y_max: float
    ) -> None:
        mean = float(np.mean(costs))
        median = float(np.median(costs))
        std = float(np.std(costs))

        self._add_std_region(figure, mean=mean, std=std, y_max=y_max)
        self._add_mean_line(figure, mean=mean, y_max=y_max)
        self._add_median_line(figure, median=median, y_max=y_max)

    def _add_std_region(
        self, figure: "Figure", *, mean: float, std: float, y_max: float
    ) -> None:
        import plotly.graph_objects as go

        figure.add_trace(
            go.Scatter(
                x=[mean - std, mean - std, mean + std, mean + std, mean - std],
                y=[0, y_max, y_max, 0, 0],
                fill="toself",
                fillcolor="rgba(128, 128, 128, 0.15)",
                line=dict(width=0),
                name=f"±1σ = [{mean - std:.3f}, {mean + std:.3f}]",
                legendgroup="statistics",
                legendgrouptitle_text="Statistics",
                hoverinfo="skip",
            )
        )

    def _add_mean_line(self, figure: "Figure", *, mean: float, y_max: float) -> None:
        import plotly.graph_objects as go

        figure.add_trace(
            go.Scatter(
                x=[mean, mean],
                y=[0, y_max],
                mode="lines",
                name=f"Mean = {mean:.4f}",
                line=dict(color="#555555", width=2),
                legendgroup="statistics",
                legendgrouptitle_text="Statistics",
            )
        )

    def _add_median_line(
        self, figure: "Figure", *, median: float, y_max: float
    ) -> None:
        import plotly.graph_objects as go

        figure.add_trace(
            go.Scatter(
                x=[median, median],
                y=[0, y_max],
                mode="lines",
                name=f"Median = {median:.4f}",
                line=dict(color="#888888", width=2, dash="dot"),
                legendgroup="statistics",
                legendgrouptitle_text="Statistics",
            )
        )

    def _add_risk_lines(
        self, figure: "Figure", risks: dict[str, float], *, y_max: float
    ) -> None:
        import plotly.graph_objects as go

        for i, (name, risk) in enumerate(risks.items()):
            color = RISK_COLORS[i % len(RISK_COLORS)]

            figure.add_trace(
                go.Scatter(
                    x=[risk, risk],
                    y=[0, y_max],
                    mode="lines",
                    name=f"{name} = {risk:.4f}",
                    line=dict(color=color, width=3),
                    legendgroup="risks",
                    legendgrouptitle_text="Risk Metrics",
                )
            )

    def _add_quantile_slider[N: int = int](
        self,
        figure: "Figure",
        costs: Array[Dims[N]],
        *,
        config: SliderConfig | tuple[float, float, int],
        y_max: float,
    ) -> None:
        import plotly.graph_objects as go

        if isinstance(config, tuple):
            alpha_min, alpha_max, steps = config
            config = SliderConfig(alpha_min=alpha_min, alpha_max=alpha_max, steps=steps)

        alphas = np.linspace(config.alpha_min, config.alpha_max, config.steps)
        quantiles = np.quantile(costs, alphas)

        initial_quantile = quantiles[0]

        quantile_trace_idx = len(figure.data)  # type: ignore

        figure.add_trace(
            go.Scatter(
                x=[initial_quantile, initial_quantile],
                y=[0, y_max],
                mode="lines",
                name="Quantile",
                line=dict(color="#00CC96", width=2, dash="dash"),
                legendgroup="slider",
                legendgrouptitle_text="Quantile Slider",
            )
        )

        figure.update_layout(
            sliders=[
                dict(
                    active=0,
                    currentvalue=dict(prefix="α = ", visible=True, xanchor="center"),
                    pad=dict(b=10, t=50),
                    steps=[
                        dict(
                            args=[
                                {"x": [[q, q]]},
                                [quantile_trace_idx],
                            ],
                            label=f"{alpha:.2f}",
                            method="restyle",
                        )
                        for alpha, q in zip(alphas, quantiles)
                    ],
                    x=0.1,
                    xanchor="left",
                    len=0.8,
                )
            ]
        )

    def _compute_y_max[N: int = int](self, costs: Array[Dims[N]]) -> float:
        from scipy.stats import gaussian_kde

        kde = gaussian_kde(costs)
        x_range = np.linspace(costs.min(), costs.max(), 200)
        return float(np.max(kde(x_range))) * 1.1  # 10% padding

    def _apply_layout(
        self,
        figure: "Figure",
        *,
        trajectory_index: int,
        time_step: int,
        sample_count: int,
        y_max: float,
    ) -> None:
        figure.update_layout(
            title=dict(
                text=(
                    f"Cost Distribution<br>"
                    f"<sup>Trajectory {trajectory_index}, t={time_step}, "
                    f"N={sample_count} samples</sup>"
                ),
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Cost",
            yaxis_title="Density",
            yaxis=dict(range=[0, y_max]),
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
                groupclick="toggleitem",
            ),
            hovermode="x unified",
            margin=dict(r=200),
        )
