"""Tests for homeolog expression extraction."""

from __future__ import annotations

from haplophaser.expression.homeolog_expression import (
    HomeologExpressionExtractor,
    extract_homeolog_expression,
)


class TestHomeologExpressionExtractor:
    """Tests for HomeologExpressionExtractor."""

    def test_extract_basic(self, expression_matrix, homeolog_result):
        """Test basic expression extraction."""
        extractor = HomeologExpressionExtractor()
        result = extractor.extract(expression_matrix, homeolog_result)

        assert result.n_pairs == 4
        assert result.n_samples == 4

    def test_extract_with_pairs_list(self, expression_matrix, homeolog_pairs):
        """Test extraction with pairs list."""
        extractor = HomeologExpressionExtractor()
        result = extractor.extract(expression_matrix, homeolog_pairs)

        assert result.n_pairs == 4

    def test_extract_with_min_expr(self, expression_matrix, homeolog_pairs):
        """Test extraction with minimum expression filter."""
        extractor = HomeologExpressionExtractor(min_mean_expr=10.0)
        result = extractor.extract(expression_matrix, homeolog_pairs)

        # Some pairs should be filtered out
        assert result.n_pairs < 4

    def test_extract_require_both_expressed(self, expression_matrix, homeolog_pairs):
        """Test requiring both genes expressed."""
        extractor = HomeologExpressionExtractor(
            require_both_expressed=True,
            min_mean_expr=0.0,
        )
        result = extractor.extract(expression_matrix, homeolog_pairs)

        # pair_003 has very low gene5 expression
        assert result.n_pairs > 0

    def test_extract_from_file(
        self, expression_matrix, tmp_homeolog_pairs
    ):
        """Test extraction from homeolog pairs file."""
        extractor = HomeologExpressionExtractor()
        result = extractor.extract(expression_matrix, tmp_homeolog_pairs)

        assert result.n_pairs == 4

    def test_extract_missing_genes(self, expression_matrix, homeolog_pairs):
        """Test handling of missing genes."""
        # Add a pair with non-existent gene
        from haplophaser.subgenome.models import HomeologPair

        pairs_with_missing = homeolog_pairs + [
            HomeologPair(
                gene1_id="missing1",
                gene1_chrom="chr1",
                gene1_subgenome="maize1",
                gene2_id="missing2",
                gene2_chrom="chr5",
                gene2_subgenome="maize2",
            )
        ]

        extractor = HomeologExpressionExtractor()
        result = extractor.extract(expression_matrix, pairs_with_missing)

        # Should only extract pairs with both genes present
        assert result.n_pairs == 4

    def test_extract_for_condition(
        self, expression_matrix, homeolog_result
    ):
        """Test extraction for specific condition."""
        extractor = HomeologExpressionExtractor()
        result = extractor.extract_for_condition(
            expression_matrix, homeolog_result, "control"
        )

        assert result.n_samples == 2  # Only control samples


class TestExtractHomeologExpressionFunction:
    """Tests for convenience function."""

    def test_basic_usage(self, expression_matrix, homeolog_pairs):
        """Test basic function usage."""
        result = extract_homeolog_expression(expression_matrix, homeolog_pairs)

        assert result is not None
        assert result.n_pairs == 4

    def test_with_options(self, expression_matrix, homeolog_pairs):
        """Test with custom options."""
        result = extract_homeolog_expression(
            expression_matrix,
            homeolog_pairs,
            min_mean_expr=5.0,
            require_both_expressed=True,
        )

        assert result is not None
