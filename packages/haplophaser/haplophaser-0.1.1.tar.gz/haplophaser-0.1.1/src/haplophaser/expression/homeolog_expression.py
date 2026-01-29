"""
Extract expression data for homeologous gene pairs.

Matches expression data with homeolog pair information to create
HomeologExpression objects for bias analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from haplophaser.expression.models import (
    ExpressionMatrix,
    HomeologExpression,
    HomeologExpressionResult,
)
from haplophaser.subgenome.models import HomeologPair, HomeologResult

logger = logging.getLogger(__name__)


@dataclass
class ExtractionParams:
    """Parameters for homeolog expression extraction.

    Parameters
    ----------
    min_mean_expr : float
        Minimum mean expression (TPM) for inclusion.
    require_both_expressed : bool
        Require both homeologs to be expressed.
    expression_threshold : float
        Expression threshold for "expressed".
    """

    min_mean_expr: float = 0.0
    require_both_expressed: bool = False
    expression_threshold: float = 0.1


class HomeologExpressionExtractor:
    """Extract expression data for homeolog pairs.

    Combines homeolog pair information with expression quantification
    to create matched expression data for bias analysis.

    Parameters
    ----------
    min_mean_expr : float
        Minimum mean expression for pair inclusion.
    require_both_expressed : bool
        Require both genes to be expressed.

    Examples
    --------
    >>> extractor = HomeologExpressionExtractor(min_mean_expr=1.0)
    >>> result = extractor.extract(
    ...     expression_matrix=matrix,
    ...     homeolog_pairs=homeologs,
    ... )
    >>> print(f"Extracted {result.n_pairs} homeolog expression pairs")
    """

    def __init__(
        self,
        min_mean_expr: float = 0.0,
        require_both_expressed: bool = False,
    ) -> None:
        self.params = ExtractionParams(
            min_mean_expr=min_mean_expr,
            require_both_expressed=require_both_expressed,
        )

    def extract(
        self,
        expression_matrix: ExpressionMatrix,
        homeolog_pairs: HomeologResult | list[HomeologPair] | Path | str,
    ) -> HomeologExpressionResult:
        """Extract expression for homeolog pairs.

        Parameters
        ----------
        expression_matrix : ExpressionMatrix
            Gene expression matrix.
        homeolog_pairs : HomeologResult, list[HomeologPair], Path, or str
            Homeolog pairs from detection or file.

        Returns
        -------
        HomeologExpressionResult
            Expression data for homeolog pairs.
        """
        # Load homeolog pairs if needed
        if isinstance(homeolog_pairs, (str, Path)):
            pairs = self._load_homeolog_pairs(homeolog_pairs)
        elif isinstance(homeolog_pairs, HomeologResult):
            pairs = homeolog_pairs.pairs
        else:
            pairs = homeolog_pairs

        logger.info(f"Extracting expression for {len(pairs)} homeolog pairs")

        # Create gene ID to row index mapping
        gene_to_idx = {g: i for i, g in enumerate(expression_matrix.gene_ids)}

        extracted = []
        missing_genes = set()
        low_expr_pairs = 0

        for i, pair in enumerate(pairs):
            # Check if both genes in matrix
            idx1 = gene_to_idx.get(pair.gene1_id)
            idx2 = gene_to_idx.get(pair.gene2_id)

            if idx1 is None:
                missing_genes.add(pair.gene1_id)
                continue
            if idx2 is None:
                missing_genes.add(pair.gene2_id)
                continue

            # Get expression values
            expr1 = expression_matrix.values[idx1, :]
            expr2 = expression_matrix.values[idx2, :]

            # Check expression threshold
            mean1 = np.mean(expr1)
            mean2 = np.mean(expr2)

            if self.params.require_both_expressed:
                if mean1 < self.params.expression_threshold:
                    low_expr_pairs += 1
                    continue
                if mean2 < self.params.expression_threshold:
                    low_expr_pairs += 1
                    continue

            total_mean = (mean1 + mean2) / 2
            if total_mean < self.params.min_mean_expr:
                low_expr_pairs += 1
                continue

            # Create pair ID
            pair_id = f"pair_{i:06d}"

            extracted.append(HomeologExpression(
                pair_id=pair_id,
                gene1_id=pair.gene1_id,
                gene2_id=pair.gene2_id,
                gene1_subgenome=pair.gene1_subgenome,
                gene2_subgenome=pair.gene2_subgenome,
                gene1_expr=expr1.copy(),
                gene2_expr=expr2.copy(),
                sample_ids=expression_matrix.sample_ids,
            ))

        if missing_genes:
            logger.warning(
                f"{len(missing_genes)} genes from homeolog pairs not found in expression matrix"
            )

        if low_expr_pairs:
            logger.info(
                f"Filtered {low_expr_pairs} pairs below expression threshold"
            )

        logger.info(f"Extracted expression for {len(extracted)} homeolog pairs")

        return HomeologExpressionResult(
            pairs=extracted,
            samples=expression_matrix.samples,
            parameters={
                "min_mean_expr": self.params.min_mean_expr,
                "require_both_expressed": self.params.require_both_expressed,
            },
        )

    def extract_for_condition(
        self,
        expression_matrix: ExpressionMatrix,
        homeolog_pairs: HomeologResult | list[HomeologPair],
        condition: str,
    ) -> HomeologExpressionResult:
        """Extract expression for a specific condition.

        Parameters
        ----------
        expression_matrix : ExpressionMatrix
            Gene expression matrix.
        homeolog_pairs : HomeologResult or list[HomeologPair]
            Homeolog pairs.
        condition : str
            Condition to filter samples by.

        Returns
        -------
        HomeologExpressionResult
            Expression data for the condition.
        """
        # Subset matrix to condition samples
        condition_samples = [
            s.sample_id for s in expression_matrix.samples
            if s.condition == condition
        ]

        if not condition_samples:
            raise ValueError(f"No samples found for condition: {condition}")

        subset_matrix = expression_matrix.subset_samples(condition_samples)

        return self.extract(subset_matrix, homeolog_pairs)

    def _load_homeolog_pairs(self, path: Path | str) -> list[HomeologPair]:
        """Load homeolog pairs from file.

        Parameters
        ----------
        path : Path or str
            Path to homeolog pairs TSV file.

        Returns
        -------
        list[HomeologPair]
            Loaded homeolog pairs.
        """
        path = Path(path)
        pairs = []

        with open(path) as f:
            header = f.readline().strip().split("\t")

            # Find column indices
            cols = {col: i for i, col in enumerate(header)}

            for line in f:
                fields = line.strip().split("\t")
                if len(fields) < 6:
                    continue

                pair = HomeologPair(
                    gene1_id=fields[cols.get("gene1_id", 0)],
                    gene1_chrom=fields[cols.get("gene1_chrom", 1)],
                    gene1_subgenome=fields[cols.get("gene1_subgenome", 2)],
                    gene2_id=fields[cols.get("gene2_id", 3)],
                    gene2_chrom=fields[cols.get("gene2_chrom", 4)],
                    gene2_subgenome=fields[cols.get("gene2_subgenome", 5)],
                )
                pairs.append(pair)

        return pairs


def extract_homeolog_expression(
    expression_matrix: ExpressionMatrix,
    homeolog_pairs: HomeologResult | list[HomeologPair] | Path | str,
    min_mean_expr: float = 0.0,
    require_both_expressed: bool = False,
) -> HomeologExpressionResult:
    """Convenience function to extract homeolog expression.

    Parameters
    ----------
    expression_matrix : ExpressionMatrix
        Gene expression matrix.
    homeolog_pairs : HomeologResult, list[HomeologPair], Path, or str
        Homeolog pairs.
    min_mean_expr : float
        Minimum mean expression for inclusion.
    require_both_expressed : bool
        Require both homeologs to be expressed.

    Returns
    -------
    HomeologExpressionResult
        Expression data for homeolog pairs.
    """
    extractor = HomeologExpressionExtractor(
        min_mean_expr=min_mean_expr,
        require_both_expressed=require_both_expressed,
    )

    return extractor.extract(expression_matrix, homeolog_pairs)


def write_homeolog_expression(
    result: HomeologExpressionResult,
    output: Path | str,
) -> None:
    """Write homeolog expression data to file.

    Parameters
    ----------
    result : HomeologExpressionResult
        Homeolog expression results.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        # Write header
        header = [
            "pair_id", "gene1_id", "gene2_id",
            "gene1_subgenome", "gene2_subgenome",
            "mean_gene1", "mean_gene2", "mean_log2_ratio",
        ]
        f.write("\t".join(header) + "\n")

        # Write data
        for pair in result.pairs:
            row = [
                pair.pair_id,
                pair.gene1_id,
                pair.gene2_id,
                pair.gene1_subgenome,
                pair.gene2_subgenome,
                f"{pair.mean_gene1:.4f}",
                f"{pair.mean_gene2:.4f}",
                f"{pair.mean_log2_ratio:.4f}",
            ]
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {result.n_pairs} homeolog expression pairs to {output}")
