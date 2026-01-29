"""
Report generation for expression bias analysis.

Creates summary reports in various formats for expression analysis results.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from haplophaser.expression.condition_bias import ConditionComparisonResult
from haplophaser.expression.models import (
    DominanceResult,
    ExpressionBiasResult,
    HomeologExpressionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ExpressionReport:
    """Expression analysis report.

    Parameters
    ----------
    homeolog_summary : dict
        Homeolog expression summary.
    bias_summary : dict
        Expression bias summary.
    dominance_summary : dict, optional
        Dominance analysis summary.
    condition_comparisons : list[dict], optional
        Condition comparison summaries.
    parameters : dict
        Analysis parameters.
    """

    homeolog_summary: dict[str, Any]
    bias_summary: dict[str, Any]
    dominance_summary: dict[str, Any] | None = None
    condition_comparisons: list[dict[str, Any]] | None = None
    parameters: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "homeolog_summary": self.homeolog_summary,
            "bias_summary": self.bias_summary,
            "dominance_summary": self.dominance_summary,
            "condition_comparisons": self.condition_comparisons,
            "parameters": self.parameters,
            "generated_at": datetime.now().isoformat(),
        }


class ReportGenerator:
    """Generate reports for expression analysis.

    Examples
    --------
    >>> generator = ReportGenerator()
    >>> report = generator.generate(
    ...     homeolog_expr=homeolog_result,
    ...     bias_result=bias_result,
    ...     dominance_result=dominance_result,
    ... )
    >>> generator.write_markdown(report, "report.md")
    """

    def generate(
        self,
        homeolog_expr: HomeologExpressionResult,
        bias_result: ExpressionBiasResult,
        dominance_result: DominanceResult | None = None,
        condition_comparisons: list[ConditionComparisonResult] | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> ExpressionReport:
        """Generate expression analysis report.

        Parameters
        ----------
        homeolog_expr : HomeologExpressionResult
            Homeolog expression data.
        bias_result : ExpressionBiasResult
            Expression bias results.
        dominance_result : DominanceResult, optional
            Dominance analysis results.
        condition_comparisons : list[ConditionComparisonResult], optional
            Condition comparison results.
        parameters : dict, optional
            Analysis parameters.

        Returns
        -------
        ExpressionReport
            Generated report.
        """
        homeolog_summary = self._summarize_homeolog_expr(homeolog_expr)
        bias_summary = bias_result.summary()

        dominance_summary = None
        if dominance_result:
            dominance_summary = dominance_result.to_dict()

        comparison_summaries = None
        if condition_comparisons:
            comparison_summaries = [c.summary() for c in condition_comparisons]

        return ExpressionReport(
            homeolog_summary=homeolog_summary,
            bias_summary=bias_summary,
            dominance_summary=dominance_summary,
            condition_comparisons=comparison_summaries,
            parameters=parameters,
        )

    def _summarize_homeolog_expr(
        self,
        homeolog_expr: HomeologExpressionResult,
    ) -> dict[str, Any]:
        """Summarize homeolog expression data.

        Parameters
        ----------
        homeolog_expr : HomeologExpressionResult
            Homeolog expression data.

        Returns
        -------
        dict
            Summary statistics.
        """
        import numpy as np

        if not homeolog_expr.pairs:
            return {
                "n_pairs": 0,
                "n_samples": homeolog_expr.n_samples,
            }

        total_expr = [p.mean_gene1 + p.mean_gene2 for p in homeolog_expr.pairs]
        log2_ratios = [p.mean_log2_ratio for p in homeolog_expr.pairs]

        return {
            "n_pairs": homeolog_expr.n_pairs,
            "n_samples": homeolog_expr.n_samples,
            "mean_total_expression": float(np.mean(total_expr)),
            "median_total_expression": float(np.median(total_expr)),
            "mean_log2_ratio": float(np.mean(log2_ratios)),
            "median_log2_ratio": float(np.median(log2_ratios)),
            "std_log2_ratio": float(np.std(log2_ratios)),
        }

    def write_markdown(
        self,
        report: ExpressionReport,
        output: Path | str,
    ) -> None:
        """Write report as Markdown.

        Parameters
        ----------
        report : ExpressionReport
            Report to write.
        output : Path or str
            Output file path.
        """
        output = Path(output)

        lines = [
            "# Expression Bias Analysis Report",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Overview",
            "",
        ]

        # Homeolog expression summary
        hs = report.homeolog_summary
        lines.extend([
            "### Homeolog Expression",
            "",
            f"- **Total homeolog pairs:** {hs.get('n_pairs', 0)}",
            f"- **Samples analyzed:** {hs.get('n_samples', 0)}",
        ])

        if hs.get('mean_total_expression') is not None:
            lines.extend([
                f"- **Mean total expression:** {hs['mean_total_expression']:.2f} TPM",
                f"- **Mean log2 ratio:** {hs['mean_log2_ratio']:.3f}",
            ])

        lines.append("")

        # Bias summary
        bs = report.bias_summary
        lines.extend([
            "### Expression Bias",
            "",
            f"- **Pairs analyzed:** {bs.get('n_pairs', 0)}",
            f"- **Significantly biased:** {bs.get('n_significant', 0)} "
            f"({bs.get('n_significant', 0) / max(bs.get('n_pairs', 1), 1) * 100:.1f}%)",
            "",
            "#### Bias Categories",
            "",
            "| Category | Count | Percentage |",
            "|----------|------:|------------|",
        ])

        by_cat = bs.get('by_category', {})
        total = bs.get('n_pairs', 1) or 1
        for cat, count in by_cat.items():
            pct = count / total * 100
            lines.append(f"| {cat} | {count} | {pct:.1f}% |")

        lines.append("")

        # Dominance summary
        if report.dominance_summary:
            ds = report.dominance_summary
            lines.extend([
                "### Subgenome Dominance",
                "",
                f"- **Test statistic (χ²):** {ds.get('chi2_statistic', 0):.2f}",
                f"- **P-value:** {ds.get('pvalue', 1):.2e}",
                f"- **Effect size:** {ds.get('effect_size', 0):.3f}",
            ])

            if ds.get('dominant_subgenome'):
                lines.append(f"- **Dominant subgenome:** {ds['dominant_subgenome']}")

            lines.append("")
            lines.append("#### Counts by Subgenome")
            lines.append("")
            lines.append("| Subgenome | Dominant Pairs | Proportion |")
            lines.append("|-----------|---------------:|------------|")

            props = ds.get('proportions', {})
            for sg, count in ds.get('subgenome_counts', {}).items():
                prop = props.get(sg, 0)
                lines.append(f"| {sg} | {count} | {prop:.1%} |")

            lines.append("")

        # Condition comparisons
        if report.condition_comparisons:
            lines.extend([
                "### Condition Comparisons",
                "",
            ])

            for comp in report.condition_comparisons:
                lines.extend([
                    f"#### {comp['condition1']} vs {comp['condition2']}",
                    "",
                    f"- **Pairs compared:** {comp.get('n_pairs', 0)}",
                    f"- **Differentially biased:** {comp.get('n_differential', 0)}",
                    f"- **Category changed:** {comp.get('n_category_changed', 0)}",
                    "",
                ])

        # Parameters
        if report.parameters:
            lines.extend([
                "## Analysis Parameters",
                "",
                "```",
            ])
            for key, value in report.parameters.items():
                lines.append(f"{key}: {value}")
            lines.extend(["```", ""])

        with open(output, "w") as f:
            f.write("\n".join(lines))

        logger.info(f"Wrote Markdown report to {output}")

    def write_json(
        self,
        report: ExpressionReport,
        output: Path | str,
    ) -> None:
        """Write report as JSON.

        Parameters
        ----------
        report : ExpressionReport
            Report to write.
        output : Path or str
            Output file path.
        """
        output = Path(output)

        with open(output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        logger.info(f"Wrote JSON report to {output}")

    def write_tsv_summary(
        self,
        report: ExpressionReport,
        output: Path | str,
    ) -> None:
        """Write summary statistics as TSV.

        Parameters
        ----------
        report : ExpressionReport
            Report to write.
        output : Path or str
            Output file path.
        """
        output = Path(output)

        with open(output, "w") as f:
            f.write("metric\tvalue\n")

            # Homeolog summary
            for key, value in report.homeolog_summary.items():
                f.write(f"homeolog.{key}\t{value}\n")

            # Bias summary
            for key, value in report.bias_summary.items():
                if key != "by_category":
                    f.write(f"bias.{key}\t{value}\n")
                else:
                    for cat, count in value.items():
                        f.write(f"bias.category.{cat}\t{count}\n")

            # Dominance summary
            if report.dominance_summary:
                for key, value in report.dominance_summary.items():
                    if key not in ("subgenome_counts", "proportions"):
                        f.write(f"dominance.{key}\t{value}\n")

        logger.info(f"Wrote TSV summary to {output}")


def generate_expression_report(
    homeolog_expr: HomeologExpressionResult,
    bias_result: ExpressionBiasResult,
    output_dir: Path | str,
    dominance_result: DominanceResult | None = None,
    condition_comparisons: list[ConditionComparisonResult] | None = None,
    parameters: dict[str, Any] | None = None,
) -> ExpressionReport:
    """Convenience function to generate and write reports.

    Parameters
    ----------
    homeolog_expr : HomeologExpressionResult
        Homeolog expression data.
    bias_result : ExpressionBiasResult
        Expression bias results.
    output_dir : Path or str
        Output directory.
    dominance_result : DominanceResult, optional
        Dominance results.
    condition_comparisons : list[ConditionComparisonResult], optional
        Condition comparisons.
    parameters : dict, optional
        Analysis parameters.

    Returns
    -------
    ExpressionReport
        Generated report.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = ReportGenerator()

    report = generator.generate(
        homeolog_expr=homeolog_expr,
        bias_result=bias_result,
        dominance_result=dominance_result,
        condition_comparisons=condition_comparisons,
        parameters=parameters,
    )

    # Write all formats
    generator.write_markdown(report, output_dir / "expression_report.md")
    generator.write_json(report, output_dir / "expression_report.json")
    generator.write_tsv_summary(report, output_dir / "expression_summary.tsv")

    return report
