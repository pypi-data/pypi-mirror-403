"""Tests for expression data models."""

from __future__ import annotations

import pytest

from haplophaser.expression.models import (
    BiasCategory,
    DominanceResult,
    ExpressionBias,
    ExpressionSample,
)


class TestExpressionSample:
    """Tests for ExpressionSample."""

    def test_creation(self):
        """Test sample creation."""
        sample = ExpressionSample(
            sample_id="s1",
            condition="drought",
            tissue="leaf",
            replicate=1,
        )
        assert sample.sample_id == "s1"
        assert sample.condition == "drought"
        assert sample.tissue == "leaf"
        assert sample.replicate == 1

    def test_group_key(self):
        """Test group key generation."""
        sample = ExpressionSample(
            sample_id="s1",
            condition="drought",
            tissue="leaf",
        )
        assert sample.group_key == "drought_leaf"

        sample_no_tissue = ExpressionSample(sample_id="s2", condition="control")
        assert sample_no_tissue.group_key == "control"


class TestExpressionMatrix:
    """Tests for ExpressionMatrix."""

    def test_creation(self, expression_matrix):
        """Test matrix creation."""
        assert expression_matrix.n_genes == 8
        assert expression_matrix.n_samples == 4
        assert expression_matrix.unit == "tpm"

    def test_get_expression(self, expression_matrix):
        """Test getting gene expression."""
        expr = expression_matrix.get_expression("gene1")
        assert len(expr) == 4
        assert expr[0] == 10.0

    def test_get_expression_invalid(self, expression_matrix):
        """Test getting non-existent gene."""
        with pytest.raises(KeyError):
            expression_matrix.get_expression("invalid_gene")

    def test_sample_ids(self, expression_matrix):
        """Test sample ID list."""
        ids = expression_matrix.sample_ids
        assert len(ids) == 4
        assert "sample1" in ids

    def test_subset_samples(self, expression_matrix):
        """Test subsetting by samples."""
        subset = expression_matrix.subset_samples(["sample1", "sample2"])
        assert subset.n_samples == 2
        assert subset.n_genes == 8

    def test_subset_genes(self, expression_matrix):
        """Test subsetting by genes."""
        subset = expression_matrix.subset_genes(["gene1", "gene2"])
        assert subset.n_genes == 2
        assert subset.n_samples == 4

    def test_samples_by_condition(self, expression_matrix):
        """Test filtering samples by condition."""
        control = expression_matrix.samples_by_condition("control")
        assert len(control) == 2

        drought = expression_matrix.samples_by_condition("drought")
        assert len(drought) == 2

    def test_conditions(self, expression_matrix):
        """Test getting unique conditions."""
        conds = expression_matrix.conditions()
        assert set(conds) == {"control", "drought"}

    def test_mean_expression(self, expression_matrix):
        """Test mean expression calculation."""
        mean_all = expression_matrix.mean_expression("gene1")
        assert mean_all == pytest.approx(9.75, rel=0.01)

        mean_control = expression_matrix.mean_expression("gene1", condition="control")
        assert mean_control == pytest.approx(11.0, rel=0.01)

    def test_to_dataframe(self, expression_matrix):
        """Test DataFrame conversion."""
        df = expression_matrix.to_dataframe()
        assert len(df) == 8
        assert len(df.columns) == 4


class TestHomeologExpression:
    """Tests for HomeologExpression."""

    def test_creation(self, homeolog_expression):
        """Test homeolog expression creation."""
        assert homeolog_expression.pair_id == "pair_001"
        assert homeolog_expression.gene1_id == "gene1"
        assert homeolog_expression.gene2_id == "gene2"
        assert homeolog_expression.n_samples == 4

    def test_total_expr(self, homeolog_expression):
        """Test total expression calculation."""
        total = homeolog_expression.total_expr
        assert len(total) == 4
        assert total[0] == 15.0  # 10 + 5

    def test_log2_ratio(self, homeolog_expression):
        """Test log2 ratio calculation."""
        ratios = homeolog_expression.log2_ratio
        assert len(ratios) == 4
        # gene1 is roughly 2x gene2, so log2 should be ~1
        assert ratios[0] > 0

    def test_mean_values(self, homeolog_expression):
        """Test mean calculations."""
        assert homeolog_expression.mean_gene1 == pytest.approx(9.75, rel=0.01)
        assert homeolog_expression.mean_gene2 == pytest.approx(5.125, rel=0.01)

    def test_gene1_fraction(self, homeolog_expression):
        """Test gene1 fraction calculation."""
        fractions = homeolog_expression.gene1_fraction()
        assert len(fractions) == 4
        # gene1 should be > 0.5 of total
        assert all(f > 0.5 for f in fractions)

    def test_is_expressed(self, homeolog_expression):
        """Test expression detection."""
        expressed = homeolog_expression.is_expressed(min_tpm=10.0)
        assert all(expressed)  # Total is >= 10 for all samples

        not_expressed = homeolog_expression.is_expressed(min_tpm=20.0)
        assert not all(not_expressed)


class TestHomeologExpressionResult:
    """Tests for HomeologExpressionResult."""

    def test_creation(self, homeolog_expression_result):
        """Test result creation."""
        assert homeolog_expression_result.n_pairs == 4
        assert homeolog_expression_result.n_samples == 4

    def test_get_pair(self, homeolog_expression_result):
        """Test getting pair by ID."""
        pair = homeolog_expression_result.get_pair("pair_001")
        assert pair is not None
        assert pair.gene1_id == "gene1"

        none_pair = homeolog_expression_result.get_pair("invalid")
        assert none_pair is None

    def test_get_pair_by_gene(self, homeolog_expression_result):
        """Test getting pair by gene ID."""
        pair = homeolog_expression_result.get_pair_by_gene("gene3")
        assert pair is not None
        assert pair.pair_id == "pair_002"

    def test_expressed_pairs(self, homeolog_expression_result):
        """Test filtering expressed pairs."""
        # Use higher threshold to ensure filtering occurs
        # pair_001 has lowest mean total expression (~14.9)
        expressed = homeolog_expression_result.expressed_pairs(min_tpm=16.0)
        # At least one pair should be filtered with this threshold
        assert len(expressed) < homeolog_expression_result.n_pairs


class TestExpressionBias:
    """Tests for ExpressionBias."""

    def test_creation(self, expression_bias):
        """Test bias creation."""
        assert expression_bias.pair_id == "pair_001"
        assert expression_bias.log2_ratio == 1.0
        assert expression_bias.category == BiasCategory.SG1_DOMINANT

    def test_is_significant(self, expression_bias):
        """Test significance detection."""
        assert expression_bias.is_significant is False  # fdr=0.05

        significant = ExpressionBias(
            pair_id="test",
            gene1_id="g1",
            gene2_id="g2",
            gene1_subgenome="sg1",
            gene2_subgenome="sg2",
            log2_ratio=1.0,
            fold_change=2.0,
            category=BiasCategory.SG1_DOMINANT,
            pvalue=0.001,
            fdr=0.01,
            mean_gene1=10.0,
            mean_gene2=5.0,
        )
        assert significant.is_significant is True

    def test_dominant_subgenome(self, expression_bias):
        """Test dominant subgenome property."""
        assert expression_bias.dominant_subgenome == "maize1"

        sg2_dominant = ExpressionBias(
            pair_id="test",
            gene1_id="g1",
            gene2_id="g2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            log2_ratio=-1.5,
            fold_change=0.35,
            category=BiasCategory.SG2_DOMINANT,
            pvalue=0.01,
            fdr=0.04,
            mean_gene1=5.0,
            mean_gene2=15.0,
        )
        assert sg2_dominant.dominant_subgenome == "maize2"


class TestExpressionBiasResult:
    """Tests for ExpressionBiasResult."""

    def test_creation(self, expression_bias_result):
        """Test result creation."""
        assert expression_bias_result.n_pairs == 4

    def test_counts(self, expression_bias_result):
        """Test category counts."""
        assert expression_bias_result.n_significant == 2  # fdr < 0.05
        assert expression_bias_result.n_sg1_dominant == 1
        assert expression_bias_result.n_sg2_dominant == 1
        assert expression_bias_result.n_balanced == 2

    def test_by_category(self, expression_bias_result):
        """Test grouping by category."""
        by_cat = expression_bias_result.by_category()
        assert len(by_cat[BiasCategory.SG1_DOMINANT]) == 1
        assert len(by_cat[BiasCategory.BALANCED]) == 2

    def test_summary(self, expression_bias_result):
        """Test summary generation."""
        summary = expression_bias_result.summary()
        assert summary["n_pairs"] == 4
        assert summary["n_significant"] == 2
        assert "by_category" in summary


class TestDominanceResult:
    """Tests for DominanceResult."""

    def test_creation(self):
        """Test dominance result creation."""
        result = DominanceResult(
            subgenome_counts={"maize1": 30, "maize2": 20},
            total_pairs=50,
            chi2_statistic=2.0,
            pvalue=0.15,
            dominant_subgenome=None,
            effect_size=0.2,
        )
        assert result.total_pairs == 50
        assert result.is_significant is False

    def test_significant_result(self):
        """Test significant dominance result."""
        result = DominanceResult(
            subgenome_counts={"maize1": 45, "maize2": 15},
            total_pairs=60,
            chi2_statistic=15.0,
            pvalue=0.0001,
            dominant_subgenome="maize1",
            effect_size=0.5,
        )
        assert result.is_significant is True
        assert result.dominant_subgenome == "maize1"

    def test_proportions(self):
        """Test proportion calculation."""
        result = DominanceResult(
            subgenome_counts={"maize1": 30, "maize2": 20},
            total_pairs=50,
            chi2_statistic=2.0,
            pvalue=0.15,
            dominant_subgenome=None,
            effect_size=0.2,
        )
        props = result.proportions()
        assert props["maize1"] == pytest.approx(0.6, rel=0.01)
        assert props["maize2"] == pytest.approx(0.4, rel=0.01)
