"""Integration tests for subgenome deconvolution pipeline."""

from __future__ import annotations

from haplophaser.subgenome.integrate import SubgenomeIntegrator
from haplophaser.subgenome.models import (
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    SubgenomeConfig,
)
from haplophaser.subgenome.synteny import SyntenySubgenomeAssigner


class TestSubgenomePipeline:
    """End-to-end test of subgenome deconvolution."""

    def test_subgenome_config_creation(self):
        """Test creating subgenome configurations."""
        # Maize config
        maize_config = SubgenomeConfig.maize_default()
        assert maize_config.n_subgenomes == 2
        assert "maize1" in maize_config.subgenome_names
        assert "maize2" in maize_config.subgenome_names
        assert maize_config.reference_species == "Zm-B73-v5"

        # Wheat config
        wheat_config = SubgenomeConfig.wheat_default()
        assert wheat_config.n_subgenomes == 3
        assert set(wheat_config.subgenome_names) == {"A", "B", "D"}

        # Brassica config
        brassica_config = SubgenomeConfig.brassica_default()
        assert brassica_config.n_subgenomes == 2
        assert set(brassica_config.subgenome_names) == {"A", "C"}

    def test_load_reference_assignments(self, maize_subgenomes):
        """Test loading reference subgenome assignments."""
        from haplophaser.io.synteny import load_reference_assignments

        assert maize_subgenomes.exists(), "Subgenome file should exist"

        assignments = load_reference_assignments(maize_subgenomes)

        assert len(assignments) > 0, "Should load assignments"
        assert "chr1" in assignments
        assert "chr2" in assignments

        # Check structure
        chr1_assignments = assignments["chr1"]
        assert len(chr1_assignments) == 2
        start, end, sg = chr1_assignments[0]
        assert start == 0
        assert sg in ("maize1", "maize2")

    def test_assignment_result_operations(self, maize_subgenomes):
        """Test SubgenomeAssignmentResult operations."""
        from haplophaser.io.synteny import load_reference_assignments

        # Create result from loaded assignments
        assignments_dict = load_reference_assignments(maize_subgenomes)
        config = SubgenomeConfig.maize_default()

        assignments = []
        for chrom, regions in assignments_dict.items():
            for start, end, sg in regions:
                assignments.append(SubgenomeAssignment(
                    chrom=chrom,
                    start=start,
                    end=end,
                    subgenome=sg,
                    confidence=0.95,
                    evidence="reference",
                ))

        result = SubgenomeAssignmentResult(
            query_name="test_assembly",
            config=config,
            assignments=assignments,
            method="reference",
        )

        # Test operations
        assert result.n_assignments > 0
        assert result.total_assigned_bp > 0

        # Test by subgenome
        maize1 = result.assignments_by_subgenome("maize1")
        maize2 = result.assignments_by_subgenome("maize2")
        assert len(maize1) > 0
        assert len(maize2) > 0

        # Test regional query
        overlapping = result.assignments_for_region("chr1", 1000000, 3000000)
        assert len(overlapping) > 0

        # Test summary
        summary = result.summary()
        assert "n_regions" in summary
        assert "by_subgenome" in summary
        assert "maize1" in summary["by_subgenome"]

    def test_synteny_assigner_creation(self):
        """Test SyntenySubgenomeAssigner creation."""
        config = SubgenomeConfig.maize_default()
        assigner = SyntenySubgenomeAssigner(
            config=config,
            min_block_size=50_000,
        )

        assert assigner is not None
        assert assigner.config == config

    def test_integrator_single_source(self, maize_subgenomes):
        """Test SubgenomeIntegrator with single evidence source."""
        from haplophaser.io.synteny import load_reference_assignments

        # Create synteny result
        assignments_dict = load_reference_assignments(maize_subgenomes)
        config = SubgenomeConfig.maize_default()

        assignments = []
        for chrom, regions in assignments_dict.items():
            for start, end, sg in regions:
                assignments.append(SubgenomeAssignment(
                    chrom=chrom,
                    start=start,
                    end=end,
                    subgenome=sg,
                    confidence=0.95,
                    evidence="synteny",
                ))

        synteny_result = SubgenomeAssignmentResult(
            query_name="test",
            config=config,
            assignments=assignments,
            method="synteny",
        )

        # Integrate
        integrator = SubgenomeIntegrator()
        result = integrator.integrate(
            synteny_assignments=synteny_result,
            config=config,
        )

        assert result.n_assignments > 0
        assert result.method == "combined"

    def test_integrator_weighted_vote(self, maize_subgenomes):
        """Test SubgenomeIntegrator with weighted voting."""
        from haplophaser.io.synteny import load_reference_assignments

        assignments_dict = load_reference_assignments(maize_subgenomes)
        config = SubgenomeConfig.maize_default()

        # Create synteny result
        synteny_assignments = []
        for chrom, regions in assignments_dict.items():
            for start, end, sg in regions:
                synteny_assignments.append(SubgenomeAssignment(
                    chrom=chrom,
                    start=start,
                    end=end,
                    subgenome=sg,
                    confidence=0.95,
                    evidence="synteny",
                ))

        synteny_result = SubgenomeAssignmentResult(
            query_name="test",
            config=config,
            assignments=synteny_assignments,
            method="synteny",
        )

        # Create ortholog result (slightly different assignments)
        ortholog_assignments = []
        for chrom, regions in assignments_dict.items():
            for start, end, sg in regions:
                ortholog_assignments.append(SubgenomeAssignment(
                    chrom=chrom,
                    start=start,
                    end=end,
                    subgenome=sg,  # Same for test
                    confidence=0.85,
                    evidence="orthologs",
                ))

        ortholog_result = SubgenomeAssignmentResult(
            query_name="test",
            config=config,
            assignments=ortholog_assignments,
            method="orthologs",
        )

        # Integrate with weighted voting
        integrator = SubgenomeIntegrator(
            weights={"synteny": 1.0, "orthologs": 0.5},
            conflict_resolution="weighted_vote",
        )

        result = integrator.integrate(
            synteny_assignments=synteny_result,
            ortholog_assignments=ortholog_result,
            config=config,
        )

        assert result.n_assignments > 0

    def test_export_to_bed(self, maize_subgenomes, tmp_path):
        """Test exporting assignments to BED format."""
        from haplophaser.io.synteny import load_reference_assignments

        assignments_dict = load_reference_assignments(maize_subgenomes)
        config = SubgenomeConfig.maize_default()

        assignments = []
        for chrom, regions in assignments_dict.items():
            for start, end, sg in regions:
                assignments.append(SubgenomeAssignment(
                    chrom=chrom,
                    start=start,
                    end=end,
                    subgenome=sg,
                    confidence=0.95,
                    evidence="synteny",
                ))

        result = SubgenomeAssignmentResult(
            query_name="test",
            config=config,
            assignments=assignments,
            method="synteny",
        )

        # Export to BED
        output_bed = tmp_path / "subgenome_assignments.bed"
        result.to_bed(output_bed)

        assert output_bed.exists()

        # Verify content
        with open(output_bed) as f:
            lines = f.readlines()
            assert len(lines) > 0
            # Check BED format
            fields = lines[0].strip().split("\t")
            assert len(fields) >= 4


class TestSubgenomeCLI:
    """Test subgenome CLI commands."""

    def test_cli_subgenome_assign_help(self):
        """Test subgenome-assign CLI help."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["subgenome-assign", "--help"])

        assert result.exit_code == 0
        assert "synteny" in result.output.lower() or "assign" in result.output.lower()
