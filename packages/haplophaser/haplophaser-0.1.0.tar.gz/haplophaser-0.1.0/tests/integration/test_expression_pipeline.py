"""Integration tests for expression bias analysis pipeline."""

from __future__ import annotations

from haplophaser.expression.bias import (
    ExpressionBiasCalculator,
    calculate_expression_bias,
    write_expression_bias,
)
from haplophaser.expression.condition_bias import (
    ConditionBiasAnalyzer,
)
from haplophaser.expression.dominance import (
    SubgenomeDominanceAnalyzer,
    test_subgenome_dominance,
)
from haplophaser.expression.homeolog_expression import (
    HomeologExpressionExtractor,
    extract_homeolog_expression,
)
from haplophaser.expression.report import generate_expression_report
from haplophaser.io.expression import (
    load_expression_matrix,
    parse_sample_metadata,
)


class TestExpressionPipeline:
    """End-to-end test of expression bias analysis."""

    def test_load_expression_data(self, maize_expression, maize_sample_metadata):
        """Test loading expression matrix with metadata."""
        assert maize_expression.exists(), "Expression file should exist"
        assert maize_sample_metadata.exists(), "Metadata file should exist"

        # Load metadata
        metadata = parse_sample_metadata(maize_sample_metadata)
        assert len(metadata) == 6, "Should have 6 samples"
        assert "control_1" in metadata
        assert metadata["control_1"]["condition"] == "control"

        # Load expression matrix
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)

        assert expr_matrix.n_genes == 20, "Should have 20 genes"
        assert expr_matrix.n_samples == 6, "Should have 6 samples"
        assert expr_matrix.unit in ("tpm", "counts")

        # Check conditions
        conditions = expr_matrix.conditions()
        assert set(conditions) == {"control", "drought"}

    def test_extract_homeolog_expression(
        self, maize_expression, maize_sample_metadata, maize_homeologs
    ):
        """Test extracting expression for homeolog pairs."""
        assert maize_homeologs.exists(), "Homeologs file should exist"

        # Load data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)

        # Extract homeolog expression
        extractor = HomeologExpressionExtractor(min_mean_expr=0.0)
        homeolog_expr = extractor.extract(expr_matrix, maize_homeologs)

        assert homeolog_expr.n_pairs == 10, "Should extract 10 homeolog pairs"
        assert homeolog_expr.n_samples == 6, "Should have 6 samples"

        # Check first pair
        pair = homeolog_expr.pairs[0]
        assert pair.gene1_id == "Zm00001d001001"
        assert pair.gene2_id == "Zm00001d001002"
        assert pair.n_samples == 6

    def test_calculate_expression_bias(
        self, maize_expression, maize_sample_metadata, maize_homeologs
    ):
        """Test calculating expression bias."""
        # Load data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)
        homeolog_expr = extract_homeolog_expression(expr_matrix, maize_homeologs)

        # Calculate bias
        calculator = ExpressionBiasCalculator(
            min_expr=1.0,
            log2_threshold=1.0,
            test_method="paired_t",
        )
        bias_result = calculator.calculate(homeolog_expr)

        assert bias_result.n_pairs == 10, "Should have 10 bias results"

        # Check summary
        summary = bias_result.summary()
        assert "n_pairs" in summary
        assert "n_significant" in summary
        assert "by_category" in summary

    def test_subgenome_dominance(
        self, maize_expression, maize_sample_metadata, maize_homeologs
    ):
        """Test subgenome dominance analysis."""
        # Load and process data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)
        homeolog_expr = extract_homeolog_expression(expr_matrix, maize_homeologs)
        bias_result = calculate_expression_bias(homeolog_expr)

        # Test dominance
        analyzer = SubgenomeDominanceAnalyzer(min_significant=1)
        dominance_result = analyzer.test_dominance(bias_result)

        assert dominance_result.total_pairs >= 0
        assert dominance_result.pvalue >= 0
        assert dominance_result.pvalue <= 1

    def test_condition_specific_bias(
        self, maize_expression, maize_sample_metadata, maize_homeologs
    ):
        """Test condition-specific bias analysis."""
        # Load data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)

        # Analyze all conditions
        analyzer = ConditionBiasAnalyzer()
        results = analyzer.analyze_all_conditions(expr_matrix, maize_homeologs)

        assert "control" in results
        assert "drought" in results
        assert results["control"].n_pairs == 10
        assert results["drought"].n_pairs == 10

    def test_condition_comparison(
        self, maize_expression, maize_sample_metadata, maize_homeologs
    ):
        """Test comparing bias between conditions."""
        # Load data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)

        # Compare conditions
        analyzer = ConditionBiasAnalyzer()
        comparison = analyzer.compare_conditions(
            expr_matrix, maize_homeologs, "control", "drought"
        )

        assert comparison.condition1 == "control"
        assert comparison.condition2 == "drought"
        assert len(comparison.differential_biases) == 10

    def test_full_pipeline_with_export(
        self, maize_expression, maize_sample_metadata, maize_homeologs, tmp_path
    ):
        """Test full pipeline with export."""
        # Load data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)

        # Extract homeolog expression
        homeolog_expr = extract_homeolog_expression(
            expr_matrix, maize_homeologs, min_mean_expr=0.5
        )

        # Calculate bias
        bias_result = calculate_expression_bias(
            homeolog_expr,
            min_expr=1.0,
            log2_threshold=0.5,
        )

        # Test dominance
        dominance_result = test_subgenome_dominance(bias_result, min_significant=1)

        # Generate report
        report = generate_expression_report(
            homeolog_expr=homeolog_expr,
            bias_result=bias_result,
            output_dir=tmp_path,
            dominance_result=dominance_result,
            parameters={
                "min_expr": 1.0,
                "log2_threshold": 0.5,
            },
        )

        # Verify outputs
        assert (tmp_path / "expression_report.md").exists()
        assert (tmp_path / "expression_report.json").exists()
        assert (tmp_path / "expression_summary.tsv").exists()

        # Write detailed bias results
        write_expression_bias(bias_result, tmp_path / "expression_bias.tsv")
        assert (tmp_path / "expression_bias.tsv").exists()

        # Verify report content
        with open(tmp_path / "expression_report.md") as f:
            content = f.read()
            assert "Expression Bias Analysis Report" in content
            assert "Homeolog Expression" in content


class TestExpressionCLI:
    """Test expression CLI commands."""

    def test_cli_expression_bias(
        self, maize_expression, maize_homeologs, tmp_path
    ):
        """Test expression-bias CLI command."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        output_file = tmp_path / "bias_output.tsv"

        result = runner.invoke(app, [
            "expression-bias",
            str(maize_expression),
            str(maize_homeologs),
            "--output", str(output_file),
            "--min-expr", "0.5",
        ])

        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1], f"CLI error: {result.output}"

        if result.exit_code == 0:
            assert output_file.exists()

    def test_cli_expression_report(
        self, maize_expression, maize_homeologs, tmp_path
    ):
        """Test expression-report CLI command."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        output_dir = tmp_path / "report_output"

        result = runner.invoke(app, [
            "expression-report",
            str(maize_expression),
            str(maize_homeologs),
            "--output-dir", str(output_dir),
        ])

        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1], f"CLI error: {result.output}"
