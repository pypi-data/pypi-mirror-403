"""
Visualization data preparation for expression bias analysis.

Prepares data structures optimized for plotting with matplotlib,
plotly, or export to visualization tools.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from haplophaser.expression.condition_bias import ConditionComparisonResult
from haplophaser.expression.models import (
    BiasCategory,
    DominanceResult,
    ExpressionBiasResult,
    HomeologExpressionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ScatterPlotData:
    """Data for scatter plot visualization.

    Parameters
    ----------
    x : np.ndarray
        X-axis values.
    y : np.ndarray
        Y-axis values.
    colors : np.ndarray
        Color values for points.
    labels : list[str]
        Point labels.
    x_label : str
        X-axis label.
    y_label : str
        Y-axis label.
    title : str
        Plot title.
    """

    x: np.ndarray
    y: np.ndarray
    colors: np.ndarray | list[str] | None = None
    labels: list[str] | None = None
    x_label: str = "X"
    y_label: str = "Y"
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "colors": self.colors.tolist() if isinstance(self.colors, np.ndarray) else self.colors,
            "labels": self.labels,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "title": self.title,
        }


@dataclass
class BarPlotData:
    """Data for bar plot visualization.

    Parameters
    ----------
    categories : list[str]
        Category labels.
    values : list[float]
        Bar values.
    errors : list[float], optional
        Error bar values.
    colors : list[str], optional
        Bar colors.
    x_label : str
        X-axis label.
    y_label : str
        Y-axis label.
    title : str
        Plot title.
    """

    categories: list[str]
    values: list[float]
    errors: list[float] | None = None
    colors: list[str] | None = None
    x_label: str = "Category"
    y_label: str = "Value"
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "categories": self.categories,
            "values": self.values,
            "errors": self.errors,
            "colors": self.colors,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "title": self.title,
        }


@dataclass
class HistogramData:
    """Data for histogram visualization.

    Parameters
    ----------
    values : np.ndarray
        Values to histogram.
    bins : int
        Number of bins.
    x_label : str
        X-axis label.
    y_label : str
        Y-axis label.
    title : str
        Plot title.
    """

    values: np.ndarray
    bins: int = 50
    x_label: str = "Value"
    y_label: str = "Frequency"
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "values": self.values.tolist(),
            "bins": self.bins,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "title": self.title,
        }


@dataclass
class HeatmapData:
    """Data for heatmap visualization.

    Parameters
    ----------
    values : np.ndarray
        2D array of values.
    row_labels : list[str]
        Row labels.
    col_labels : list[str]
        Column labels.
    title : str
        Plot title.
    """

    values: np.ndarray
    row_labels: list[str]
    col_labels: list[str]
    title: str = ""
    colormap: str = "RdBu_r"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "values": self.values.tolist(),
            "row_labels": self.row_labels,
            "col_labels": self.col_labels,
            "title": self.title,
            "colormap": self.colormap,
        }


class ExpressionVizPrep:
    """Prepare visualization data for expression analysis."""

    def __init__(self) -> None:
        # Color scheme for bias categories
        self.category_colors = {
            BiasCategory.SG1_DOMINANT: "#e41a1c",  # Red
            BiasCategory.SG2_DOMINANT: "#377eb8",  # Blue
            BiasCategory.BALANCED: "#999999",      # Gray
            BiasCategory.SG1_ONLY: "#ff7f00",      # Orange
            BiasCategory.SG2_ONLY: "#984ea3",      # Purple
            BiasCategory.SILENT: "#f0f0f0",        # Light gray
        }

    def expression_scatter(
        self,
        homeolog_expr: HomeologExpressionResult,
        color_by: str = "ratio",
    ) -> ScatterPlotData:
        """Create scatter plot of homeolog expression.

        Parameters
        ----------
        homeolog_expr : HomeologExpressionResult
            Homeolog expression data.
        color_by : str
            Color scheme: 'ratio', 'total'.

        Returns
        -------
        ScatterPlotData
            Scatter plot data.
        """
        x = []
        y = []
        colors = []
        labels = []

        for pair in homeolog_expr.pairs:
            x.append(pair.mean_gene1)
            y.append(pair.mean_gene2)
            labels.append(pair.pair_id)

            if color_by == "ratio":
                colors.append(pair.mean_log2_ratio)
            else:
                colors.append(pair.mean_gene1 + pair.mean_gene2)

        return ScatterPlotData(
            x=np.log2(np.array(x) + 0.1),
            y=np.log2(np.array(y) + 0.1),
            colors=np.array(colors),
            labels=labels,
            x_label="log2(Gene1 TPM + 0.1)",
            y_label="log2(Gene2 TPM + 0.1)",
            title="Homeolog Expression",
        )

    def bias_ma_plot(
        self,
        bias_result: ExpressionBiasResult,
    ) -> ScatterPlotData:
        """Create MA plot (ratio vs average) for bias analysis.

        Parameters
        ----------
        bias_result : ExpressionBiasResult
            Expression bias results.

        Returns
        -------
        ScatterPlotData
            MA plot data.
        """
        m_values = []  # Log2 ratio
        a_values = []  # Average expression
        colors = []
        labels = []

        for bias in bias_result.biases:
            m_values.append(bias.log2_ratio)
            a_values.append(np.log2((bias.mean_gene1 + bias.mean_gene2) / 2 + 0.1))
            colors.append(self.category_colors.get(bias.category, "#999999"))
            labels.append(bias.pair_id)

        return ScatterPlotData(
            x=np.array(a_values),
            y=np.array(m_values),
            colors=colors,
            labels=labels,
            x_label="A (Mean log2 expression)",
            y_label="M (log2 ratio)",
            title="Expression Bias MA Plot",
        )

    def bias_category_bar(
        self,
        bias_result: ExpressionBiasResult,
    ) -> BarPlotData:
        """Create bar plot of bias categories.

        Parameters
        ----------
        bias_result : ExpressionBiasResult
            Expression bias results.

        Returns
        -------
        BarPlotData
            Bar plot data.
        """
        by_category = bias_result.by_category()

        categories = []
        values = []
        colors = []

        for cat in BiasCategory:
            categories.append(cat.value)
            values.append(len(by_category.get(cat, [])))
            colors.append(self.category_colors.get(cat, "#999999"))

        return BarPlotData(
            categories=categories,
            values=values,
            colors=colors,
            x_label="Bias Category",
            y_label="Number of Pairs",
            title="Expression Bias Distribution",
        )

    def log2_ratio_histogram(
        self,
        bias_result: ExpressionBiasResult,
        bins: int = 50,
    ) -> HistogramData:
        """Create histogram of log2 ratios.

        Parameters
        ----------
        bias_result : ExpressionBiasResult
            Expression bias results.
        bins : int
            Number of bins.

        Returns
        -------
        HistogramData
            Histogram data.
        """
        ratios = np.array([b.log2_ratio for b in bias_result.biases])

        return HistogramData(
            values=ratios,
            bins=bins,
            x_label="log2(Gene1/Gene2)",
            y_label="Number of Pairs",
            title="Distribution of Expression Ratios",
        )

    def dominance_pie_data(
        self,
        dominance_result: DominanceResult,
    ) -> BarPlotData:
        """Create data for dominance pie/bar chart.

        Parameters
        ----------
        dominance_result : DominanceResult
            Dominance test results.

        Returns
        -------
        BarPlotData
            Bar plot data (can be converted to pie).
        """
        categories = list(dominance_result.subgenome_counts.keys())
        values = [dominance_result.subgenome_counts[c] for c in categories]

        return BarPlotData(
            categories=categories,
            values=values,
            x_label="Subgenome",
            y_label="Dominant Pairs",
            title="Subgenome Dominance Distribution",
        )

    def condition_comparison_heatmap(
        self,
        comparison: ConditionComparisonResult,
        top_n: int = 50,
    ) -> HeatmapData:
        """Create heatmap of differential bias.

        Parameters
        ----------
        comparison : ConditionComparisonResult
            Condition comparison results.
        top_n : int
            Number of top differential pairs to show.

        Returns
        -------
        HeatmapData
            Heatmap data.
        """
        # Sort by |log2_ratio_diff|
        sorted_diff = sorted(
            comparison.differential_biases,
            key=lambda x: abs(x.log2_ratio_diff),
            reverse=True,
        )[:top_n]

        row_labels = [d.pair_id for d in sorted_diff]
        col_labels = [comparison.condition1, comparison.condition2]

        values = np.array([
            [d.log2_ratio_cond1, d.log2_ratio_cond2]
            for d in sorted_diff
        ])

        return HeatmapData(
            values=values,
            row_labels=row_labels,
            col_labels=col_labels,
            title="Differential Expression Bias",
            colormap="RdBu_r",
        )

    def ratio_per_sample_heatmap(
        self,
        homeolog_expr: HomeologExpressionResult,
        top_n: int = 50,
    ) -> HeatmapData:
        """Create heatmap of log2 ratios per sample.

        Parameters
        ----------
        homeolog_expr : HomeologExpressionResult
            Homeolog expression data.
        top_n : int
            Number of pairs to show.

        Returns
        -------
        HeatmapData
            Heatmap data.
        """
        # Sort by variance in ratio
        pairs_with_var = [
            (p, np.var(p.log2_ratio))
            for p in homeolog_expr.pairs
        ]
        sorted_pairs = sorted(pairs_with_var, key=lambda x: x[1], reverse=True)[:top_n]

        row_labels = [p.pair_id for p, _ in sorted_pairs]
        col_labels = homeolog_expr.pairs[0].sample_ids if homeolog_expr.pairs else []

        values = np.array([p.log2_ratio for p, _ in sorted_pairs])

        return HeatmapData(
            values=values,
            row_labels=row_labels,
            col_labels=col_labels,
            title="Log2 Ratio by Sample",
            colormap="RdBu_r",
        )


def prepare_chromoplot_data(
    bias_result: ExpressionBiasResult,
    gene_positions: dict[str, tuple[str, int, int]],
) -> dict[str, list[dict]]:
    """Prepare expression bias data for chromoplot visualization.

    Parameters
    ----------
    bias_result : ExpressionBiasResult
        Expression bias results.
    gene_positions : dict[str, tuple[str, int, int]]
        Gene ID to (chrom, start, end) mapping.

    Returns
    -------
    dict[str, list[dict]]
        Chromosome to track data mapping.
    """
    # Color scheme
    category_colors = {
        BiasCategory.SG1_DOMINANT: "#e41a1c",
        BiasCategory.SG2_DOMINANT: "#377eb8",
        BiasCategory.BALANCED: "#999999",
        BiasCategory.SG1_ONLY: "#ff7f00",
        BiasCategory.SG2_ONLY: "#984ea3",
        BiasCategory.SILENT: "#f0f0f0",
    }

    track_data: dict[str, list[dict]] = {}

    for bias in bias_result.biases:
        # Get position for gene1
        pos = gene_positions.get(bias.gene1_id)
        if not pos:
            continue

        chrom, start, end = pos

        if chrom not in track_data:
            track_data[chrom] = []

        track_data[chrom].append({
            "start": start,
            "end": end,
            "value": bias.log2_ratio,
            "color": category_colors.get(bias.category, "#999999"),
            "name": bias.pair_id,
            "gene1": bias.gene1_id,
            "gene2": bias.gene2_id,
            "category": bias.category.value,
        })

    # Sort by position
    for chrom in track_data:
        track_data[chrom].sort(key=lambda x: x["start"])

    return track_data


def write_viz_data(
    data: ScatterPlotData | BarPlotData | HistogramData | HeatmapData,
    output: Path | str,
    format: str = "json",
) -> None:
    """Write visualization data to file.

    Parameters
    ----------
    data : visualization data
        Data to write.
    output : Path or str
        Output file path.
    format : str
        Output format: 'json', 'tsv'.
    """
    import json

    output = Path(output)
    data_dict = data.to_dict()

    if format == "json":
        with open(output, "w") as f:
            json.dump(data_dict, f, indent=2)
    elif format == "tsv":
        # Simple TSV for scatter/bar data
        if isinstance(data, ScatterPlotData):
            with open(output, "w") as f:
                f.write("x\ty\tcolor\tlabel\n")
                for i in range(len(data.x)):
                    color = data.colors[i] if data.colors is not None else ""
                    label = data.labels[i] if data.labels else ""
                    f.write(f"{data.x[i]}\t{data.y[i]}\t{color}\t{label}\n")
    else:
        raise ValueError(f"Unknown format: {format}")

    logger.info(f"Wrote visualization data to {output}")
