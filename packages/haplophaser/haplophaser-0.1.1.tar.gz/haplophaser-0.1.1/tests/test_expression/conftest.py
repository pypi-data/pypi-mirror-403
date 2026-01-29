"""Pytest fixtures for expression analysis tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from haplophaser.expression.models import (
    BiasCategory,
    ExpressionBias,
    ExpressionBiasResult,
    ExpressionMatrix,
    ExpressionSample,
    HomeologExpression,
    HomeologExpressionResult,
)
from haplophaser.subgenome.models import HomeologPair, HomeologResult, SubgenomeConfig

# ============================================================================
# Sample fixtures
# ============================================================================


@pytest.fixture
def expression_samples() -> list[ExpressionSample]:
    """Create test expression samples."""
    return [
        ExpressionSample(
            sample_id="sample1",
            condition="control",
            tissue="leaf",
            replicate=1,
        ),
        ExpressionSample(
            sample_id="sample2",
            condition="control",
            tissue="leaf",
            replicate=2,
        ),
        ExpressionSample(
            sample_id="sample3",
            condition="drought",
            tissue="leaf",
            replicate=1,
        ),
        ExpressionSample(
            sample_id="sample4",
            condition="drought",
            tissue="leaf",
            replicate=2,
        ),
    ]


@pytest.fixture
def expression_matrix(expression_samples) -> ExpressionMatrix:
    """Create test expression matrix."""
    gene_ids = [
        "gene1", "gene2", "gene3", "gene4",
        "gene5", "gene6", "gene7", "gene8",
    ]

    # Create expression values (genes x samples)
    # Simulate different expression patterns
    np.random.seed(42)
    values = np.array([
        [10.0, 12.0, 8.0, 9.0],    # gene1 - moderate expression
        [5.0, 4.0, 6.0, 5.5],      # gene2 - lower, homeolog of gene1
        [20.0, 22.0, 25.0, 28.0],  # gene3 - high, increases in drought
        [18.0, 19.0, 12.0, 10.0],  # gene4 - homeolog of gene3, decreases
        [0.5, 0.3, 0.4, 0.2],      # gene5 - lowly expressed
        [15.0, 16.0, 14.0, 15.0],  # gene6 - homeolog of gene5, higher
        [8.0, 9.0, 8.5, 9.0],      # gene7 - balanced
        [7.5, 8.5, 8.0, 8.5],      # gene8 - homeolog of gene7, balanced
    ])

    return ExpressionMatrix(
        gene_ids=gene_ids,
        samples=expression_samples,
        values=values,
        unit="tpm",
    )


@pytest.fixture
def homeolog_pairs() -> list[HomeologPair]:
    """Create test homeolog pairs."""
    return [
        HomeologPair(
            gene1_id="gene1",
            gene1_chrom="chr1",
            gene1_subgenome="maize1",
            gene2_id="gene2",
            gene2_chrom="chr5",
            gene2_subgenome="maize2",
            ks=0.15,
            synteny_support=True,
        ),
        HomeologPair(
            gene1_id="gene3",
            gene1_chrom="chr1",
            gene1_subgenome="maize1",
            gene2_id="gene4",
            gene2_chrom="chr5",
            gene2_subgenome="maize2",
            ks=0.12,
            synteny_support=True,
        ),
        HomeologPair(
            gene1_id="gene5",
            gene1_chrom="chr2",
            gene1_subgenome="maize1",
            gene2_id="gene6",
            gene2_chrom="chr4",
            gene2_subgenome="maize2",
            ks=0.18,
            synteny_support=False,
        ),
        HomeologPair(
            gene1_id="gene7",
            gene1_chrom="chr3",
            gene1_subgenome="maize1",
            gene2_id="gene8",
            gene2_chrom="chr6",
            gene2_subgenome="maize2",
            ks=0.14,
            synteny_support=True,
        ),
    ]


@pytest.fixture
def homeolog_result(homeolog_pairs) -> HomeologResult:
    """Create homeolog result."""
    config = SubgenomeConfig.maize_default()
    return HomeologResult(
        pairs=homeolog_pairs,
        config=config,
        parameters={"method": "synteny"},
    )


# ============================================================================
# Homeolog expression fixtures
# ============================================================================


@pytest.fixture
def homeolog_expression() -> HomeologExpression:
    """Create a single homeolog expression pair."""
    return HomeologExpression(
        pair_id="pair_001",
        gene1_id="gene1",
        gene2_id="gene2",
        gene1_subgenome="maize1",
        gene2_subgenome="maize2",
        gene1_expr=np.array([10.0, 12.0, 8.0, 9.0]),
        gene2_expr=np.array([5.0, 4.0, 6.0, 5.5]),
        sample_ids=["s1", "s2", "s3", "s4"],
    )


@pytest.fixture
def homeolog_expression_list() -> list[HomeologExpression]:
    """Create list of homeolog expression pairs."""
    return [
        HomeologExpression(
            pair_id="pair_001",
            gene1_id="gene1",
            gene2_id="gene2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([10.0, 12.0, 8.0, 9.0]),
            gene2_expr=np.array([5.0, 4.0, 6.0, 5.5]),
            sample_ids=["s1", "s2", "s3", "s4"],
        ),
        HomeologExpression(
            pair_id="pair_002",
            gene1_id="gene3",
            gene2_id="gene4",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([20.0, 22.0, 25.0, 28.0]),
            gene2_expr=np.array([18.0, 19.0, 12.0, 10.0]),
            sample_ids=["s1", "s2", "s3", "s4"],
        ),
        HomeologExpression(
            pair_id="pair_003",
            gene1_id="gene5",
            gene2_id="gene6",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([0.5, 0.3, 0.4, 0.2]),
            gene2_expr=np.array([15.0, 16.0, 14.0, 15.0]),
            sample_ids=["s1", "s2", "s3", "s4"],
        ),
        HomeologExpression(
            pair_id="pair_004",
            gene1_id="gene7",
            gene2_id="gene8",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([8.0, 9.0, 8.5, 9.0]),
            gene2_expr=np.array([7.5, 8.5, 8.0, 8.5]),
            sample_ids=["s1", "s2", "s3", "s4"],
        ),
    ]


@pytest.fixture
def homeolog_expression_result(
    homeolog_expression_list, expression_samples
) -> HomeologExpressionResult:
    """Create homeolog expression result."""
    return HomeologExpressionResult(
        pairs=homeolog_expression_list,
        samples=expression_samples,
        parameters={"min_mean_expr": 0.0},
    )


# ============================================================================
# Bias fixtures
# ============================================================================


@pytest.fixture
def expression_bias() -> ExpressionBias:
    """Create a single expression bias result."""
    return ExpressionBias(
        pair_id="pair_001",
        gene1_id="gene1",
        gene2_id="gene2",
        gene1_subgenome="maize1",
        gene2_subgenome="maize2",
        log2_ratio=1.0,
        fold_change=2.0,
        category=BiasCategory.SG1_DOMINANT,
        pvalue=0.01,
        fdr=0.05,
        mean_gene1=10.0,
        mean_gene2=5.0,
    )


@pytest.fixture
def expression_bias_list() -> list[ExpressionBias]:
    """Create list of expression bias results."""
    return [
        ExpressionBias(
            pair_id="pair_001",
            gene1_id="gene1",
            gene2_id="gene2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            log2_ratio=1.0,
            fold_change=2.0,
            category=BiasCategory.SG1_DOMINANT,
            pvalue=0.01,
            fdr=0.04,
            mean_gene1=10.0,
            mean_gene2=5.0,
        ),
        ExpressionBias(
            pair_id="pair_002",
            gene1_id="gene3",
            gene2_id="gene4",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            log2_ratio=0.5,
            fold_change=1.4,
            category=BiasCategory.BALANCED,
            pvalue=0.1,
            fdr=0.15,
            mean_gene1=22.0,
            mean_gene2=15.0,
        ),
        ExpressionBias(
            pair_id="pair_003",
            gene1_id="gene5",
            gene2_id="gene6",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            log2_ratio=-5.0,
            fold_change=0.03,
            category=BiasCategory.SG2_DOMINANT,
            pvalue=0.001,
            fdr=0.01,
            mean_gene1=0.35,
            mean_gene2=15.0,
        ),
        ExpressionBias(
            pair_id="pair_004",
            gene1_id="gene7",
            gene2_id="gene8",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            log2_ratio=0.1,
            fold_change=1.07,
            category=BiasCategory.BALANCED,
            pvalue=0.5,
            fdr=0.6,
            mean_gene1=8.5,
            mean_gene2=8.0,
        ),
    ]


@pytest.fixture
def expression_bias_result(expression_bias_list) -> ExpressionBiasResult:
    """Create expression bias result."""
    return ExpressionBiasResult(
        biases=expression_bias_list,
        parameters={"min_expr": 1.0, "log2_threshold": 1.0},
    )


# ============================================================================
# File fixtures
# ============================================================================


@pytest.fixture
def tmp_expression_matrix(tmp_path: Path) -> Path:
    """Create temporary expression matrix file."""
    content = """gene_id\tsample1\tsample2\tsample3\tsample4
gene1\t10.0\t12.0\t8.0\t9.0
gene2\t5.0\t4.0\t6.0\t5.5
gene3\t20.0\t22.0\t25.0\t28.0
gene4\t18.0\t19.0\t12.0\t10.0
gene5\t0.5\t0.3\t0.4\t0.2
gene6\t15.0\t16.0\t14.0\t15.0
gene7\t8.0\t9.0\t8.5\t9.0
gene8\t7.5\t8.5\t8.0\t8.5
"""
    path = tmp_path / "expression.tsv"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_sample_metadata(tmp_path: Path) -> Path:
    """Create temporary sample metadata file."""
    content = """sample_id\tcondition\ttissue\treplicate
sample1\tcontrol\tleaf\t1
sample2\tcontrol\tleaf\t2
sample3\tdrought\tleaf\t1
sample4\tdrought\tleaf\t2
"""
    path = tmp_path / "metadata.tsv"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_homeolog_pairs(tmp_path: Path) -> Path:
    """Create temporary homeolog pairs file."""
    content = """gene1_id\tgene1_chrom\tgene1_subgenome\tgene2_id\tgene2_chrom\tgene2_subgenome\tks\tka\tsynteny_support\tsequence_identity\tconfidence
gene1\tchr1\tmaize1\tgene2\tchr5\tmaize2\t0.15\t0.02\ttrue\t0.85\t0.95
gene3\tchr1\tmaize1\tgene4\tchr5\tmaize2\t0.12\t0.015\ttrue\t0.88\t0.92
gene5\tchr2\tmaize1\tgene6\tchr4\tmaize2\t0.18\t0.03\tfalse\t0.82\t0.80
gene7\tchr3\tmaize1\tgene8\tchr6\tmaize2\t0.14\t0.02\ttrue\t0.86\t0.90
"""
    path = tmp_path / "homeolog_pairs.tsv"
    path.write_text(content)
    return path


@pytest.fixture
def tmp_salmon_dir(tmp_path: Path) -> Path:
    """Create temporary Salmon output directory."""
    sample_dir = tmp_path / "salmon_output" / "sample1"
    sample_dir.mkdir(parents=True)

    content = """Name\tLength\tEffectiveLength\tTPM\tNumReads
gene1\t1000\t850\t10.0\t100
gene2\t1200\t1050\t5.0\t60
gene3\t800\t650\t20.0\t150
gene4\t900\t750\t18.0\t140
"""
    (sample_dir / "quant.sf").write_text(content)

    return sample_dir
