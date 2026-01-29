"""Tests for expression bias calculation."""

from __future__ import annotations

import numpy as np

from haplophaser.expression.bias import (
    ExpressionBiasCalculator,
    calculate_expression_bias,
)
from haplophaser.expression.models import BiasCategory, HomeologExpression


class TestExpressionBiasCalculator:
    """Tests for ExpressionBiasCalculator."""

    def test_calculate_basic(self, homeolog_expression_result):
        """Test basic bias calculation."""
        calculator = ExpressionBiasCalculator()
        result = calculator.calculate(homeolog_expression_result)

        assert result.n_pairs == 4
        assert len(result.biases) == 4

    def test_calculate_with_list(self, homeolog_expression_list):
        """Test calculation with list input."""
        calculator = ExpressionBiasCalculator()
        result = calculator.calculate(homeolog_expression_list)

        assert result.n_pairs == 4

    def test_bias_classification(self, homeolog_expression_list):
        """Test bias classification."""
        calculator = ExpressionBiasCalculator(
            min_expr=1.0,
            log2_threshold=1.0,
        )
        result = calculator.calculate(homeolog_expression_list)

        # Check that categories are assigned
        categories = [b.category for b in result.biases]
        assert any(c == BiasCategory.BALANCED for c in categories)

    def test_fdr_correction(self, homeolog_expression_list):
        """Test FDR correction is applied."""
        calculator = ExpressionBiasCalculator()
        result = calculator.calculate(homeolog_expression_list)

        # FDR should be >= pvalue
        for bias in result.biases:
            assert bias.fdr >= bias.pvalue

    def test_sg1_dominant_detection(self):
        """Test detection of SG1 dominant pairs."""
        # Create pair with clear SG1 dominance
        pair = HomeologExpression(
            pair_id="test",
            gene1_id="g1",
            gene2_id="g2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([20.0, 22.0, 18.0, 21.0]),
            gene2_expr=np.array([5.0, 4.0, 6.0, 5.0]),
            sample_ids=["s1", "s2", "s3", "s4"],
        )

        calculator = ExpressionBiasCalculator(log2_threshold=1.0)
        result = calculator.calculate([pair])

        # Should detect SG1 dominance (gene1 >> gene2)
        assert result.biases[0].log2_ratio > 1.0

    def test_sg2_dominant_detection(self):
        """Test detection of SG2 dominant pairs."""
        # Create pair with clear SG2 dominance
        pair = HomeologExpression(
            pair_id="test",
            gene1_id="g1",
            gene2_id="g2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([2.0, 3.0, 2.5, 2.0]),
            gene2_expr=np.array([20.0, 22.0, 18.0, 21.0]),
            sample_ids=["s1", "s2", "s3", "s4"],
        )

        calculator = ExpressionBiasCalculator(log2_threshold=1.0)
        result = calculator.calculate([pair])

        # Should detect SG2 dominance (gene2 >> gene1)
        assert result.biases[0].log2_ratio < -1.0

    def test_balanced_detection(self):
        """Test detection of balanced expression."""
        # Create pair with balanced expression
        pair = HomeologExpression(
            pair_id="test",
            gene1_id="g1",
            gene2_id="g2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=np.array([10.0, 11.0, 9.5, 10.5]),
            gene2_expr=np.array([10.0, 10.5, 10.0, 10.0]),
            sample_ids=["s1", "s2", "s3", "s4"],
        )

        calculator = ExpressionBiasCalculator(log2_threshold=1.0)
        result = calculator.calculate([pair])

        # Log2 ratio should be close to 0
        assert abs(result.biases[0].log2_ratio) < 0.5

    def test_test_methods(self, homeolog_expression_list):
        """Test different statistical methods."""
        for method in ["paired_t", "wilcoxon"]:
            calculator = ExpressionBiasCalculator(test_method=method)
            result = calculator.calculate(homeolog_expression_list)
            assert result.n_pairs == 4


class TestCalculateExpressionBiasFunction:
    """Tests for convenience function."""

    def test_basic_usage(self, homeolog_expression_result):
        """Test basic function usage."""
        result = calculate_expression_bias(homeolog_expression_result)
        assert result is not None
        assert result.n_pairs == 4

    def test_custom_parameters(self, homeolog_expression_result):
        """Test with custom parameters."""
        result = calculate_expression_bias(
            homeolog_expression_result,
            min_expr=2.0,
            log2_threshold=0.5,
            test_method="wilcoxon",
        )
        assert result is not None
