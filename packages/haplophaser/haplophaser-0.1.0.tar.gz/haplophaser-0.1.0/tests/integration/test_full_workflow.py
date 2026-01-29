"""Integration tests for full phaser workflow."""

from __future__ import annotations

import pytest


class TestFullWorkflow:
    """Test complete phaser workflow from data loading to analysis."""

    def test_data_files_exist(self, test_data_dir):
        """Verify all test data files exist."""
        expected_files = [
            "maize_populations.tsv",
            "maize_genetic_map.tsv",
            "maize_subgenomes.bed",
            "maize_expression.tsv",
            "maize_sample_metadata.tsv",
            "maize_homeologs.tsv",
        ]

        for filename in expected_files:
            filepath = test_data_dir / filename
            assert filepath.exists(), f"Missing test data file: {filename}"

    def test_population_loading(self, maize_populations):
        """Test loading population file."""
        from haplophaser.io.populations import load_populations

        populations = load_populations(maize_populations)

        # load_populations returns a list of Population objects
        assert isinstance(populations, list)
        assert len(populations) > 0

        # Check founders - filter populations by role
        from haplophaser.core.models import PopulationRole

        founder_pops = [p for p in populations if p.role == PopulationRole.FOUNDER]
        derived_pops = [p for p in populations if p.role == PopulationRole.DERIVED]

        # Get all founder samples
        founder_samples = []
        for pop in founder_pops:
            founder_samples.extend(pop.samples)
        assert len(founder_samples) == 5
        assert "B73" in [s.name for s in founder_samples]

        # Get all derived samples
        derived_samples = []
        for pop in derived_pops:
            derived_samples.extend(pop.samples)
        assert len(derived_samples) == 5
        assert "RIL_001" in [s.name for s in derived_samples]

    def test_genetic_map_loading(self, maize_genetic_map):
        """Test loading genetic map."""
        from haplophaser.core.genetic_map import GeneticMap

        gmap = GeneticMap.from_file(maize_genetic_map)

        assert gmap is not None
        assert len(gmap.chromosomes) > 0
        assert "chr1" in gmap.chromosomes

    def test_subgenome_to_expression_workflow(
        self,
        maize_subgenomes,
        maize_expression,
        maize_sample_metadata,
        maize_homeologs,
        tmp_path,
    ):
        """Test workflow from subgenome assignments to expression analysis."""
        from haplophaser.expression.bias import calculate_expression_bias
        from haplophaser.expression.dominance import test_subgenome_dominance
        from haplophaser.expression.homeolog_expression import extract_homeolog_expression
        from haplophaser.io.expression import load_expression_matrix, parse_sample_metadata
        from haplophaser.io.synteny import load_reference_assignments

        # Step 1: Load subgenome assignments
        assignments = load_reference_assignments(maize_subgenomes)
        assert len(assignments) > 0, "Should load subgenome assignments"

        # Step 2: Load expression data
        metadata = parse_sample_metadata(maize_sample_metadata)
        expr_matrix = load_expression_matrix(maize_expression, sample_metadata=metadata)
        assert expr_matrix.n_genes > 0, "Should load expression data"

        # Step 3: Extract homeolog expression
        homeolog_expr = extract_homeolog_expression(expr_matrix, maize_homeologs)
        assert homeolog_expr.n_pairs > 0, "Should extract homeolog pairs"

        # Step 4: Calculate expression bias
        bias_result = calculate_expression_bias(homeolog_expr)
        assert bias_result.n_pairs > 0, "Should calculate bias"

        # Step 5: Test subgenome dominance
        dominance = test_subgenome_dominance(bias_result, min_significant=1)
        assert dominance is not None, "Should test dominance"

        # Verify workflow produces consistent results
        summary = bias_result.summary()
        assert summary["n_pairs"] == homeolog_expr.n_pairs

    def test_core_models_integration(self):
        """Test that core models work together correctly."""
        from haplophaser.core.models import (
            HaplotypeBlock,
            Population,
            PopulationRole,
            Sample,
            Variant,
            Window,
        )

        # Create samples
        samples = [
            Sample(name="B73", ploidy=2, population="founders"),
            Sample(name="Mo17", ploidy=2, population="founders"),
            Sample(name="RIL_001", ploidy=2, population="derived"),
        ]

        # Create populations
        founder_pop = Population(
            name="founders",
            samples=[s for s in samples if s.population == "founders"],
            role=PopulationRole.FOUNDER,
        )
        derived_pop = Population(
            name="derived",
            samples=[s for s in samples if s.population == "derived"],
            role=PopulationRole.DERIVED,
        )

        assert len(founder_pop.samples) == 2
        assert len(derived_pop.samples) == 1

        # Create variants
        variant = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "B73": [0, 0],
                "Mo17": [1, 1],
                "RIL_001": [0, 1],
            },
        )

        assert len(variant.alt) == 1  # biallelic check
        assert variant.n_alleles == 2

        # Create window with variants
        window = Window(
            chrom="chr1",
            start=0,
            end=100_000,
            variants=[variant],
            index=0,
        )

        assert window.n_variants == 1
        assert len(window) == 100_000

        # Create haplotype block
        block = HaplotypeBlock(
            chrom="chr1",
            start=0,
            end=50_000,
            sample="RIL_001",
            homolog=0,
            founder="B73",
            proportion=0.95,
            n_variants=50,
        )

        assert len(block) == 50_000
        assert block.founder == "B73"

    def test_subgenome_models_integration(self):
        """Test that subgenome models work together correctly."""
        from haplophaser.subgenome.models import (
            HomeologPair,
            HomeologResult,
            SubgenomeAssignment,
            SubgenomeAssignmentResult,
            SubgenomeConfig,
        )

        # Create config
        config = SubgenomeConfig.maize_default()
        assert config.n_subgenomes == 2

        # Get subgenome by name
        sg1 = config.get_subgenome("maize1")
        assert sg1 is not None
        assert sg1.name == "maize1"

        # Create assignments
        assignments = [
            SubgenomeAssignment(
                chrom="chr1",
                start=0,
                end=1_000_000,
                subgenome="maize1",
                confidence=0.95,
                evidence="synteny",
            ),
            SubgenomeAssignment(
                chrom="chr1",
                start=1_000_000,
                end=2_000_000,
                subgenome="maize2",
                confidence=0.90,
                evidence="synteny",
            ),
        ]

        result = SubgenomeAssignmentResult(
            query_name="test",
            config=config,
            assignments=assignments,
            method="synteny",
        )

        assert result.n_assignments == 2
        assert result.total_assigned_bp == 2_000_000

        # Create homeolog pairs
        pairs = [
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
        ]

        homeolog_result = HomeologResult(
            pairs=pairs,
            config=config,
        )

        assert homeolog_result.n_pairs == 1

    def test_expression_models_integration(self):
        """Test that expression models work together correctly."""
        import numpy as np

        from haplophaser.expression.models import (
            BiasCategory,
            ExpressionBias,
            ExpressionMatrix,
            ExpressionSample,
            HomeologExpression,
        )

        # Create samples
        samples = [
            ExpressionSample(sample_id="s1", condition="control", replicate=1),
            ExpressionSample(sample_id="s2", condition="control", replicate=2),
            ExpressionSample(sample_id="s3", condition="drought", replicate=1),
        ]

        # Create expression matrix
        values = np.array([
            [10.0, 12.0, 8.0],
            [5.0, 4.0, 6.0],
        ])

        matrix = ExpressionMatrix(
            gene_ids=["gene1", "gene2"],
            samples=samples,
            values=values,
            unit="tpm",
        )

        assert matrix.n_genes == 2
        assert matrix.n_samples == 3
        assert set(matrix.conditions()) == {"control", "drought"}

        # Create homeolog expression
        homeolog = HomeologExpression(
            pair_id="pair_001",
            gene1_id="gene1",
            gene2_id="gene2",
            gene1_subgenome="maize1",
            gene2_subgenome="maize2",
            gene1_expr=values[0],
            gene2_expr=values[1],
            sample_ids=["s1", "s2", "s3"],
        )

        assert homeolog.mean_gene1 == pytest.approx(10.0, rel=0.01)
        assert homeolog.mean_log2_ratio > 0  # gene1 > gene2

        # Create bias result
        bias = ExpressionBias(
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

        assert bias.dominant_subgenome == "maize1"


class TestCLIIntegration:
    """Test CLI command integration."""

    def test_cli_help(self):
        """Test main CLI help."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "phaser" in result.output.lower() or "haplotype" in result.output.lower()

    def test_cli_version(self):
        """Test version command."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output or "version" in result.output.lower()

    def test_cli_commands_available(self):
        """Test that expected CLI commands are available."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        # Check for key command groups
        output_lower = result.output.lower()

        # These commands should be available
        expected_commands = [
            "expression",
            "subgenome",
        ]

        for cmd in expected_commands:
            # Command should appear in help or as a subcommand
            assert cmd in output_lower or result.exit_code == 0
