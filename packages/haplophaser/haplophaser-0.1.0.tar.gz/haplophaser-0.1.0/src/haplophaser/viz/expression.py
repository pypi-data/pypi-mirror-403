"""Expression bias visualization."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..expression.bias import BiasResults

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def _check_matplotlib():
    """Check if matplotlib is available."""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib is required for expression visualization. "
            "Install with: pip install phaser[viz]"
        )


class ExpressionBiasFigure:
    """
    Homeolog expression bias visualization.

    Creates publication-ready figures for expression bias analysis
    including MA plots, bias distributions, and heatmaps.

    Parameters
    ----------
    bias_results : BiasResults or str
        Bias results object or path to TSV
    figsize : tuple, optional
        Figure size

    Examples
    --------
    >>> fig = ExpressionBiasFigure(bias_results)
    >>> fig.plot_ma()
    >>> fig.save("ma_plot.pdf")

    >>> fig.plot_bias_distribution()
    >>> fig.save("bias_distribution.pdf")
    """

    def __init__(
        self,
        bias_results: "BiasResults | str | Path",
        figsize: tuple[float, float] | None = None,
    ):
        _check_matplotlib()
        self.bias_results = self._load_results(bias_results)
        self.figsize = figsize or (8, 6)
        self._fig: plt.Figure | None = None
        self._ax: plt.Axes | None = None

    def _load_results(self, results):
        """Load results from file if needed."""
        if isinstance(results, (str, Path)):
            import pandas as pd

            return pd.read_csv(results, sep="\t")
        return results

    def plot_ma(
        self,
        highlight_significant: bool = True,
        fdr_threshold: float = 0.05,
        **kwargs,
    ) -> "ExpressionBiasFigure":
        """
        Create MA plot (log2 ratio vs mean expression).

        Parameters
        ----------
        highlight_significant : bool
            Color significant pairs differently
        fdr_threshold : float
            FDR threshold for significance
        """
        self._fig, self._ax = plt.subplots(figsize=self.figsize)

        # Extract data
        if hasattr(self.bias_results, "homeolog_biases"):
            log2ratios = [b.mean_log2ratio for b in self.bias_results.homeolog_biases]
            mean_expr = [
                np.log10(
                    np.mean([
                        (
                            b.pair.gene1_expression.mean()
                            if hasattr(b.pair, "gene1_expression")
                            else 1
                        ),
                        (
                            b.pair.gene2_expression.mean()
                            if hasattr(b.pair, "gene2_expression")
                            else 1
                        ),
                    ])
                    + 1
                )
                for b in self.bias_results.homeolog_biases
            ]
            fdrs = [b.fdr for b in self.bias_results.homeolog_biases]
        else:
            # DataFrame input
            log2ratios = self.bias_results["mean_log2ratio"].values
            mean_expr = (
                self.bias_results["mean_expression"].values
                if "mean_expression" in self.bias_results.columns
                else np.ones(len(log2ratios))
            )
            fdrs = (
                self.bias_results["fdr"].values
                if "fdr" in self.bias_results.columns
                else np.ones(len(log2ratios))
            )

        # Create colors
        if highlight_significant:
            colors = ["#d62728" if fdr < fdr_threshold else "#1f77b4" for fdr in fdrs]
        else:
            colors = "#1f77b4"

        # Plot
        self._ax.scatter(mean_expr, log2ratios, c=colors, alpha=0.5, s=10)

        # Add reference lines
        self._ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
        self._ax.axhline(y=1, color="lightgray", linestyle=":", linewidth=0.5)
        self._ax.axhline(y=-1, color="lightgray", linestyle=":", linewidth=0.5)

        # Labels
        self._ax.set_xlabel("Mean Expression (log10)", fontsize=10)
        self._ax.set_ylabel("Log2(SG1/SG2)", fontsize=10)
        self._ax.set_title("Homeolog Expression Bias", fontsize=12)

        plt.tight_layout()
        return self

    def plot_bias_distribution(
        self,
        bins: int = 50,
        show_stats: bool = True,
        **kwargs,
    ) -> "ExpressionBiasFigure":
        """
        Plot distribution of expression bias values.

        Parameters
        ----------
        bins : int
            Number of histogram bins
        show_stats : bool
            Show mean/median lines and statistics
        """
        self._fig, self._ax = plt.subplots(figsize=self.figsize)

        # Extract log2 ratios
        if hasattr(self.bias_results, "homeolog_biases"):
            log2ratios = [b.mean_log2ratio for b in self.bias_results.homeolog_biases]
        else:
            log2ratios = self.bias_results["mean_log2ratio"].values

        log2ratios = np.array(log2ratios)
        log2ratios = log2ratios[~np.isnan(log2ratios)]

        # Plot histogram
        self._ax.hist(
            log2ratios, bins=bins, color="#1f77b4", alpha=0.7, edgecolor="white"
        )

        # Add statistics
        if show_stats:
            mean_val = np.mean(log2ratios)
            median_val = np.median(log2ratios)

            self._ax.axvline(
                mean_val,
                color="#d62728",
                linestyle="-",
                linewidth=2,
                label=f"Mean: {mean_val:.3f}",
            )
            self._ax.axvline(
                median_val,
                color="#2ca02c",
                linestyle="--",
                linewidth=2,
                label=f"Median: {median_val:.3f}",
            )
            self._ax.axvline(0, color="gray", linestyle=":", linewidth=1)

            self._ax.legend(loc="upper right")

        # Labels
        self._ax.set_xlabel("Log2(SG1/SG2)", fontsize=10)
        self._ax.set_ylabel("Number of Homeolog Pairs", fontsize=10)
        self._ax.set_title("Distribution of Expression Bias", fontsize=12)

        plt.tight_layout()
        return self

    def plot_bias_by_chromosome(
        self,
        **kwargs,
    ) -> "ExpressionBiasFigure":
        """Plot expression bias by chromosome."""
        # Implementation for chromosome-level bias plot
        self._fig, self._ax = plt.subplots(figsize=self.figsize)

        # Extract data
        if hasattr(self.bias_results, "homeolog_biases"):
            chroms = []
            log2ratios = []
            for b in self.bias_results.homeolog_biases:
                if hasattr(b.pair, "gene1_chrom"):
                    chroms.append(b.pair.gene1_chrom)
                    log2ratios.append(b.mean_log2ratio)
        else:
            if "chrom" in self.bias_results.columns:
                chroms = self.bias_results["chrom"].values
                log2ratios = self.bias_results["mean_log2ratio"].values
            else:
                raise ValueError("No chromosome information in results")

        # Group by chromosome
        chrom_data = {}
        for chrom, ratio in zip(chroms, log2ratios):
            if chrom not in chrom_data:
                chrom_data[chrom] = []
            if not np.isnan(ratio):
                chrom_data[chrom].append(ratio)

        # Create boxplot
        sorted_chroms = sorted(chrom_data.keys())
        data = [chrom_data[c] for c in sorted_chroms]

        self._ax.boxplot(data, labels=sorted_chroms)
        self._ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)

        self._ax.set_xlabel("Chromosome", fontsize=10)
        self._ax.set_ylabel("Log2(SG1/SG2)", fontsize=10)
        self._ax.set_title("Expression Bias by Chromosome", fontsize=12)
        self._ax.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        return self

    def save(self, path: str | Path, dpi: int = 300, **kwargs) -> None:
        """Save figure."""
        if self._fig is not None:
            self._fig.savefig(path, dpi=dpi, bbox_inches="tight", **kwargs)

    def show(self) -> None:
        """Display figure."""
        if self._fig is not None:
            plt.show()
