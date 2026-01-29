"""
Data models for expression analysis in paleopolyploids.

Provides structures for expression matrices, homeolog expression pairs,
expression bias metrics, and analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class BiasCategory(str, Enum):
    """Categories of expression bias between homeologs."""

    SG1_DOMINANT = "sg1_dominant"  # Subgenome 1 higher expression
    SG2_DOMINANT = "sg2_dominant"  # Subgenome 2 higher expression
    BALANCED = "balanced"  # No significant bias
    SG1_ONLY = "sg1_only"  # Only SG1 expressed
    SG2_ONLY = "sg2_only"  # Only SG2 expressed
    SILENT = "silent"  # Neither expressed


class ExpressionFormat(str, Enum):
    """Supported expression data formats."""

    SALMON = "salmon"
    KALLISTO = "kallisto"
    FEATURECOUNTS = "featurecounts"
    TPM_MATRIX = "tpm_matrix"
    RAW_COUNTS = "raw_counts"


@dataclass
class ExpressionSample:
    """An expression quantification sample.

    Parameters
    ----------
    sample_id : str
        Unique sample identifier.
    condition : str, optional
        Experimental condition (e.g., "drought", "control").
    tissue : str, optional
        Tissue type (e.g., "leaf", "root").
    replicate : int, optional
        Biological replicate number.
    metadata : dict
        Additional sample metadata.

    Examples
    --------
    >>> sample = ExpressionSample(
    ...     sample_id="sample1",
    ...     condition="drought",
    ...     tissue="leaf",
    ...     replicate=1,
    ... )
    """

    sample_id: str
    condition: str | None = None
    tissue: str | None = None
    replicate: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def group_key(self) -> str:
        """Return grouping key based on condition and tissue."""
        parts = []
        if self.condition:
            parts.append(self.condition)
        if self.tissue:
            parts.append(self.tissue)
        return "_".join(parts) if parts else "default"


@dataclass
class ExpressionMatrix:
    """Gene expression matrix with samples as columns.

    Parameters
    ----------
    gene_ids : list[str]
        List of gene identifiers.
    samples : list[ExpressionSample]
        List of samples (columns).
    values : np.ndarray
        Expression values matrix (genes x samples).
    unit : str
        Expression unit: 'tpm', 'fpkm', 'counts', 'cpm'.

    Examples
    --------
    >>> matrix = ExpressionMatrix(
    ...     gene_ids=["gene1", "gene2"],
    ...     samples=[sample1, sample2],
    ...     values=np.array([[10.5, 12.3], [5.2, 4.8]]),
    ...     unit="tpm",
    ... )
    """

    gene_ids: list[str]
    samples: list[ExpressionSample]
    values: np.ndarray
    unit: str = "tpm"

    def __post_init__(self) -> None:
        """Validate matrix dimensions."""
        if self.values.shape != (len(self.gene_ids), len(self.samples)):
            raise ValueError(
                f"Matrix shape {self.values.shape} does not match "
                f"genes ({len(self.gene_ids)}) x samples ({len(self.samples)})"
            )

    @property
    def n_genes(self) -> int:
        """Return number of genes."""
        return len(self.gene_ids)

    @property
    def n_samples(self) -> int:
        """Return number of samples."""
        return len(self.samples)

    @property
    def sample_ids(self) -> list[str]:
        """Return list of sample IDs."""
        return [s.sample_id for s in self.samples]

    def get_expression(self, gene_id: str) -> np.ndarray:
        """Get expression values for a gene across all samples.

        Parameters
        ----------
        gene_id : str
            Gene identifier.

        Returns
        -------
        np.ndarray
            Expression values for the gene.

        Raises
        ------
        KeyError
            If gene not found.
        """
        try:
            idx = self.gene_ids.index(gene_id)
            return self.values[idx, :]
        except ValueError:
            raise KeyError(f"Gene {gene_id} not found in matrix")

    def get_sample_expression(self, sample_id: str) -> np.ndarray:
        """Get expression values for a sample across all genes.

        Parameters
        ----------
        sample_id : str
            Sample identifier.

        Returns
        -------
        np.ndarray
            Expression values for the sample.
        """
        sample_ids = self.sample_ids
        try:
            idx = sample_ids.index(sample_id)
            return self.values[:, idx]
        except ValueError:
            raise KeyError(f"Sample {sample_id} not found in matrix")

    def subset_samples(self, sample_ids: list[str]) -> ExpressionMatrix:
        """Create subset matrix with specific samples.

        Parameters
        ----------
        sample_ids : list[str]
            Sample IDs to include.

        Returns
        -------
        ExpressionMatrix
            Subset matrix.
        """
        indices = [self.sample_ids.index(sid) for sid in sample_ids]
        return ExpressionMatrix(
            gene_ids=self.gene_ids.copy(),
            samples=[self.samples[i] for i in indices],
            values=self.values[:, indices].copy(),
            unit=self.unit,
        )

    def subset_genes(self, gene_ids: list[str]) -> ExpressionMatrix:
        """Create subset matrix with specific genes.

        Parameters
        ----------
        gene_ids : list[str]
            Gene IDs to include.

        Returns
        -------
        ExpressionMatrix
            Subset matrix.
        """
        indices = [self.gene_ids.index(gid) for gid in gene_ids if gid in self.gene_ids]
        return ExpressionMatrix(
            gene_ids=[self.gene_ids[i] for i in indices],
            samples=self.samples.copy(),
            values=self.values[indices, :].copy(),
            unit=self.unit,
        )

    def samples_by_condition(self, condition: str) -> list[ExpressionSample]:
        """Get samples for a specific condition.

        Parameters
        ----------
        condition : str
            Condition name.

        Returns
        -------
        list[ExpressionSample]
            Matching samples.
        """
        return [s for s in self.samples if s.condition == condition]

    def conditions(self) -> list[str]:
        """Return unique conditions in the matrix."""
        conds = {s.condition for s in self.samples if s.condition}
        return sorted(conds)

    def mean_expression(self, gene_id: str, condition: str | None = None) -> float:
        """Calculate mean expression for a gene.

        Parameters
        ----------
        gene_id : str
            Gene identifier.
        condition : str, optional
            Limit to specific condition.

        Returns
        -------
        float
            Mean expression value.
        """
        expr = self.get_expression(gene_id)

        if condition:
            indices = [
                i for i, s in enumerate(self.samples)
                if s.condition == condition
            ]
            if indices:
                expr = expr[indices]

        return float(np.mean(expr))

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Expression matrix as DataFrame.
        """
        import pandas as pd

        return pd.DataFrame(
            self.values,
            index=self.gene_ids,
            columns=self.sample_ids,
        )


@dataclass
class HomeologExpression:
    """Expression data for a homeolog pair.

    Parameters
    ----------
    pair_id : str
        Homeolog pair identifier.
    gene1_id : str
        First gene (subgenome 1).
    gene2_id : str
        Second gene (subgenome 2).
    gene1_subgenome : str
        Subgenome of gene1.
    gene2_subgenome : str
        Subgenome of gene2.
    gene1_expr : np.ndarray
        Expression values for gene1 across samples.
    gene2_expr : np.ndarray
        Expression values for gene2 across samples.
    sample_ids : list[str]
        Sample identifiers.

    Examples
    --------
    >>> he = HomeologExpression(
    ...     pair_id="pair_001",
    ...     gene1_id="Zm00001d001234",
    ...     gene2_id="Zm00001d054321",
    ...     gene1_subgenome="maize1",
    ...     gene2_subgenome="maize2",
    ...     gene1_expr=np.array([10.5, 12.3, 11.2]),
    ...     gene2_expr=np.array([5.2, 4.8, 5.5]),
    ...     sample_ids=["s1", "s2", "s3"],
    ... )
    """

    pair_id: str
    gene1_id: str
    gene2_id: str
    gene1_subgenome: str
    gene2_subgenome: str
    gene1_expr: np.ndarray
    gene2_expr: np.ndarray
    sample_ids: list[str]

    @property
    def n_samples(self) -> int:
        """Return number of samples."""
        return len(self.sample_ids)

    @property
    def total_expr(self) -> np.ndarray:
        """Return total expression (sum of both homeologs)."""
        return self.gene1_expr + self.gene2_expr

    @property
    def log2_ratio(self) -> np.ndarray:
        """Return log2(gene1/gene2) ratio per sample.

        Adds pseudocount to avoid division by zero.
        """
        pseudocount = 0.01
        return np.log2(
            (self.gene1_expr + pseudocount) / (self.gene2_expr + pseudocount)
        )

    @property
    def mean_gene1(self) -> float:
        """Return mean expression of gene1."""
        return float(np.mean(self.gene1_expr))

    @property
    def mean_gene2(self) -> float:
        """Return mean expression of gene2."""
        return float(np.mean(self.gene2_expr))

    @property
    def mean_log2_ratio(self) -> float:
        """Return mean log2 ratio across samples."""
        return float(np.mean(self.log2_ratio))

    def gene1_fraction(self) -> np.ndarray:
        """Return fraction of expression from gene1.

        Returns
        -------
        np.ndarray
            Gene1 expression / total expression per sample.
        """
        total = self.total_expr
        # Avoid division by zero
        return np.where(total > 0, self.gene1_expr / total, 0.5)

    def is_expressed(self, min_tpm: float = 1.0) -> np.ndarray:
        """Check if pair is expressed per sample.

        Parameters
        ----------
        min_tpm : float
            Minimum TPM for "expressed".

        Returns
        -------
        np.ndarray
            Boolean array indicating expression.
        """
        return self.total_expr >= min_tpm

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pair_id": self.pair_id,
            "gene1_id": self.gene1_id,
            "gene2_id": self.gene2_id,
            "gene1_subgenome": self.gene1_subgenome,
            "gene2_subgenome": self.gene2_subgenome,
            "mean_gene1": self.mean_gene1,
            "mean_gene2": self.mean_gene2,
            "mean_log2_ratio": self.mean_log2_ratio,
            "n_samples": self.n_samples,
        }


@dataclass
class HomeologExpressionResult:
    """Results of homeolog expression extraction.

    Parameters
    ----------
    pairs : list[HomeologExpression]
        Expression data for each homeolog pair.
    samples : list[ExpressionSample]
        Sample metadata.
    parameters : dict
        Parameters used for extraction.
    """

    pairs: list[HomeologExpression]
    samples: list[ExpressionSample]
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def n_pairs(self) -> int:
        """Return number of homeolog pairs."""
        return len(self.pairs)

    @property
    def n_samples(self) -> int:
        """Return number of samples."""
        return len(self.samples)

    def get_pair(self, pair_id: str) -> HomeologExpression | None:
        """Get homeolog expression by pair ID.

        Parameters
        ----------
        pair_id : str
            Pair identifier.

        Returns
        -------
        HomeologExpression or None
            The pair if found.
        """
        for p in self.pairs:
            if p.pair_id == pair_id:
                return p
        return None

    def get_pair_by_gene(self, gene_id: str) -> HomeologExpression | None:
        """Get homeolog expression by gene ID.

        Parameters
        ----------
        gene_id : str
            Gene identifier.

        Returns
        -------
        HomeologExpression or None
            The pair containing this gene if found.
        """
        for p in self.pairs:
            if gene_id in (p.gene1_id, p.gene2_id):
                return p
        return None

    def expressed_pairs(self, min_tpm: float = 1.0) -> list[HomeologExpression]:
        """Get pairs with minimum expression.

        Parameters
        ----------
        min_tpm : float
            Minimum mean TPM.

        Returns
        -------
        list[HomeologExpression]
            Expressed pairs.
        """
        return [
            p for p in self.pairs
            if (p.mean_gene1 + p.mean_gene2) / 2 >= min_tpm
        ]

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Expression data as DataFrame.
        """
        import pandas as pd

        if not self.pairs:
            return pd.DataFrame()

        rows = [p.to_dict() for p in self.pairs]
        return pd.DataFrame(rows)


@dataclass
class ExpressionBias:
    """Expression bias for a single homeolog pair.

    Parameters
    ----------
    pair_id : str
        Homeolog pair identifier.
    gene1_id : str
        First gene (subgenome 1).
    gene2_id : str
        Second gene (subgenome 2).
    gene1_subgenome : str
        Subgenome of gene1.
    gene2_subgenome : str
        Subgenome of gene2.
    log2_ratio : float
        Mean log2(gene1/gene2) ratio.
    fold_change : float
        Fold change between homeologs.
    category : BiasCategory
        Bias classification.
    pvalue : float
        Statistical significance of bias.
    fdr : float
        FDR-corrected p-value.
    mean_gene1 : float
        Mean expression of gene1.
    mean_gene2 : float
        Mean expression of gene2.

    Examples
    --------
    >>> bias = ExpressionBias(
    ...     pair_id="pair_001",
    ...     gene1_id="gene1",
    ...     gene2_id="gene2",
    ...     gene1_subgenome="maize1",
    ...     gene2_subgenome="maize2",
    ...     log2_ratio=1.5,
    ...     fold_change=2.83,
    ...     category=BiasCategory.SG1_DOMINANT,
    ...     pvalue=0.001,
    ...     fdr=0.01,
    ...     mean_gene1=20.0,
    ...     mean_gene2=7.07,
    ... )
    """

    pair_id: str
    gene1_id: str
    gene2_id: str
    gene1_subgenome: str
    gene2_subgenome: str
    log2_ratio: float
    fold_change: float
    category: BiasCategory
    pvalue: float
    fdr: float
    mean_gene1: float
    mean_gene2: float

    @property
    def is_significant(self) -> bool:
        """Return True if bias is statistically significant (FDR < 0.05)."""
        return self.fdr < 0.05

    @property
    def is_biased(self) -> bool:
        """Return True if significantly biased toward either subgenome."""
        return self.is_significant and self.category in (
            BiasCategory.SG1_DOMINANT,
            BiasCategory.SG2_DOMINANT,
        )

    @property
    def dominant_subgenome(self) -> str | None:
        """Return dominant subgenome if biased."""
        if self.category == BiasCategory.SG1_DOMINANT:
            return self.gene1_subgenome
        elif self.category == BiasCategory.SG2_DOMINANT:
            return self.gene2_subgenome
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pair_id": self.pair_id,
            "gene1_id": self.gene1_id,
            "gene2_id": self.gene2_id,
            "gene1_subgenome": self.gene1_subgenome,
            "gene2_subgenome": self.gene2_subgenome,
            "log2_ratio": self.log2_ratio,
            "fold_change": self.fold_change,
            "category": self.category.value,
            "pvalue": self.pvalue,
            "fdr": self.fdr,
            "mean_gene1": self.mean_gene1,
            "mean_gene2": self.mean_gene2,
            "is_significant": self.is_significant,
            "dominant_subgenome": self.dominant_subgenome,
        }


@dataclass
class ExpressionBiasResult:
    """Results of expression bias analysis.

    Parameters
    ----------
    biases : list[ExpressionBias]
        Bias results for each homeolog pair.
    parameters : dict
        Parameters used for analysis.
    """

    biases: list[ExpressionBias]
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def n_pairs(self) -> int:
        """Return number of analyzed pairs."""
        return len(self.biases)

    @property
    def n_significant(self) -> int:
        """Return number of significantly biased pairs."""
        return sum(1 for b in self.biases if b.is_significant)

    @property
    def n_sg1_dominant(self) -> int:
        """Return number of pairs with SG1 dominance."""
        return sum(
            1 for b in self.biases
            if b.category == BiasCategory.SG1_DOMINANT and b.is_significant
        )

    @property
    def n_sg2_dominant(self) -> int:
        """Return number of pairs with SG2 dominance."""
        return sum(
            1 for b in self.biases
            if b.category == BiasCategory.SG2_DOMINANT and b.is_significant
        )

    @property
    def n_balanced(self) -> int:
        """Return number of balanced pairs."""
        return sum(
            1 for b in self.biases
            if b.category == BiasCategory.BALANCED
        )

    def by_category(self) -> dict[BiasCategory, list[ExpressionBias]]:
        """Group biases by category.

        Returns
        -------
        dict
            Category to bias list mapping.
        """
        result: dict[BiasCategory, list[ExpressionBias]] = {}
        for cat in BiasCategory:
            result[cat] = [b for b in self.biases if b.category == cat]
        return result

    def significant_biases(self) -> list[ExpressionBias]:
        """Get significantly biased pairs.

        Returns
        -------
        list[ExpressionBias]
            Pairs with FDR < 0.05.
        """
        return [b for b in self.biases if b.is_significant]

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        by_cat = self.by_category()

        return {
            "n_pairs": self.n_pairs,
            "n_significant": self.n_significant,
            "n_sg1_dominant": self.n_sg1_dominant,
            "n_sg2_dominant": self.n_sg2_dominant,
            "n_balanced": self.n_balanced,
            "by_category": {
                cat.value: len(biases)
                for cat, biases in by_cat.items()
            },
            "mean_log2_ratio": float(np.mean([b.log2_ratio for b in self.biases])),
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Bias results as DataFrame.
        """
        import pandas as pd

        if not self.biases:
            return pd.DataFrame()

        rows = [b.to_dict() for b in self.biases]
        return pd.DataFrame(rows)


@dataclass
class ConditionBiasResult:
    """Expression bias results across conditions.

    Parameters
    ----------
    condition : str
        Condition name.
    bias_result : ExpressionBiasResult
        Bias results for this condition.
    comparison : str, optional
        Comparison condition for differential analysis.
    differential_biases : list[ExpressionBias], optional
        Pairs with changed bias between conditions.
    """

    condition: str
    bias_result: ExpressionBiasResult
    comparison: str | None = None
    differential_biases: list[ExpressionBias] = field(default_factory=list)

    @property
    def n_differential(self) -> int:
        """Return number of pairs with differential bias."""
        return len(self.differential_biases)


@dataclass
class DominanceResult:
    """Results of subgenome dominance analysis.

    Parameters
    ----------
    subgenome_counts : dict[str, int]
        Count of dominant pairs per subgenome.
    total_pairs : int
        Total number of analyzed pairs.
    chi2_statistic : float
        Chi-square test statistic.
    pvalue : float
        P-value for dominance test.
    dominant_subgenome : str, optional
        Overall dominant subgenome if significant.
    effect_size : float
        Effect size (proportion difference).
    """

    subgenome_counts: dict[str, int]
    total_pairs: int
    chi2_statistic: float
    pvalue: float
    dominant_subgenome: str | None
    effect_size: float

    @property
    def is_significant(self) -> bool:
        """Return True if genome-wide dominance is significant."""
        return self.pvalue < 0.05

    def proportions(self) -> dict[str, float]:
        """Return proportion of pairs dominant for each subgenome.

        Returns
        -------
        dict
            Subgenome to proportion mapping.
        """
        if self.total_pairs == 0:
            return {}
        return {
            sg: count / self.total_pairs
            for sg, count in self.subgenome_counts.items()
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "subgenome_counts": self.subgenome_counts,
            "total_pairs": self.total_pairs,
            "chi2_statistic": self.chi2_statistic,
            "pvalue": self.pvalue,
            "dominant_subgenome": self.dominant_subgenome,
            "effect_size": self.effect_size,
            "is_significant": self.is_significant,
            "proportions": self.proportions(),
        }
