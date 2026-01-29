"""
Integration tests for phaser + chromoplot visualization.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


class TestPhaserChromoplotIntegration:
    """Test phaser visualization with chromoplot backend."""

    def test_figure_classes_use_chromoplot(self):
        """Verify figure classes properly wrap chromoplot."""
        from haplophaser.viz import ProportionFigure

        # ProportionFigure should create chromoplot GenomeFigure
        assert hasattr(ProportionFigure, "render")
        assert hasattr(ProportionFigure, "save")
        assert hasattr(ProportionFigure, "add_haplotypes")

    def test_color_utilities_exist(self):
        """Test color utility functions are available."""
        from haplophaser.viz.utils import get_founder_colors, get_phaser_theme

        # Test theme creation
        with patch("haplophaser.viz.utils.cp") as mock_cp:
            mock_theme = MagicMock()
            mock_cp.Theme.return_value = mock_theme
            theme = get_phaser_theme()
            assert theme is not None

    def test_results_to_chromoplot_format(self, tmp_path):
        """Test converting phaser results to chromoplot-ready files."""
        from haplophaser.viz.utils import results_to_bed

        # Create mock results
        class MockBlock:
            def __init__(self, chrom, start, end, founder):
                self.chrom = chrom
                self.start = start
                self.end = end
                self.founder = founder
                self.confidence = 0.95

        blocks = [
            MockBlock("chr1", 0, 1000000, "B73"),
            MockBlock("chr1", 1000000, 2000000, "Mo17"),
            MockBlock("chr1", 2000000, 3000000, "B73"),
        ]

        output = tmp_path / "blocks.bed"
        results_to_bed(blocks, output)

        assert output.exists()

        # Verify format
        with open(output) as f:
            lines = [line for line in f if not line.startswith("#")]
            assert len(lines) == 3

            # Check first line
            parts = lines[0].strip().split("\t")
            assert parts[0] == "chr1"
            assert parts[3] == "B73"

    def test_viz_module_exports(self):
        """Test that viz module exports expected items."""
        from haplophaser import viz

        expected_exports = [
            # Presets
            "plot_haplotype_proportions",
            "plot_genome_haplotypes",
            "plot_assembly_painting",
            "plot_subgenome_assignment",
            "plot_expression_bias",
            "plot_synteny",
            # Figure classes
            "ProportionFigure",
            "ProportionGenomeFigure",
            "AssemblyPaintingFigure",
            "SubgenomeFigure",
            "ExpressionBiasFigure",
            "SyntenyFigure",
            # Utilities
            "get_phaser_theme",
            "get_founder_colors",
            "results_to_bed",
        ]

        for name in expected_exports:
            assert hasattr(viz, name), f"Missing export: {name}"

    def test_proportion_figure_creation(self, test_fai):
        """Test ProportionFigure can be created."""
        with patch("haplophaser.viz.proportion.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_coords.n_chromosomes = 3
            mock_load.return_value = mock_coords

            from haplophaser.viz import ProportionFigure

            fig = ProportionFigure(test_fai, region="chr1:1-1000000")

            assert fig.coordinates is not None
            assert fig.region == "chr1:1-1000000"
            assert len(fig._tracks) == 0

    def test_proportion_figure_add_tracks(self, test_fai, test_haplotypes):
        """Test adding tracks to ProportionFigure."""
        with patch("haplophaser.viz.proportion.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import ProportionFigure

            fig = ProportionFigure(test_fai)
            fig.add_ideogram()
            fig.add_haplotypes(test_haplotypes)
            fig.add_scale_bar()

            assert len(fig._tracks) == 3

    def test_expression_bias_figure(self, test_expression_bias):
        """Test ExpressionBiasFigure creation and plotting."""
        with patch("haplophaser.viz.expression.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)

            from haplophaser.viz import ExpressionBiasFigure

            fig = ExpressionBiasFigure(test_expression_bias)

            assert fig.bias_results is not None
            assert fig.figsize == (8, 6)

            # Test MA plot
            result = fig.plot_ma()
            assert result is fig  # Fluent interface
            mock_ax.scatter.assert_called_once()

    def test_subgenome_figure_creation(self, test_fai):
        """Test SubgenomeFigure creation."""
        with patch("haplophaser.viz.subgenome.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import SubgenomeFigure

            fig = SubgenomeFigure(
                test_fai,
                subgenomes=["maize1", "maize2"],
                organism="maize",
            )

            assert fig.subgenomes == ["maize1", "maize2"]
            assert fig.organism == "maize"

    def test_assembly_painting_figure(self, test_fai, test_haplotypes):
        """Test AssemblyPaintingFigure creation."""
        with patch("haplophaser.viz.assembly.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import AssemblyPaintingFigure

            fig = AssemblyPaintingFigure(test_fai)
            fig.add_ideogram()
            fig.add_painting(test_haplotypes)

            assert len(fig._tracks) == 2

    def test_synteny_figure_creation(self, test_fai):
        """Test SyntenyFigure creation."""
        with patch("haplophaser.viz.comparative.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import SyntenyFigure

            fig = SyntenyFigure(test_fai, test_fai)  # Using same for both

            assert fig.ref_coordinates is not None
            assert fig.query_coordinates is not None


class TestVisualizationCLI:
    """Test visualization CLI commands."""

    def test_viz_cli_help(self):
        """Test viz CLI help."""
        from typer.testing import CliRunner

        from haplophaser.cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["viz", "--help"])

        assert result.exit_code == 0
        # Check for viz subcommands
        output_lower = result.output.lower()
        assert "proportion" in output_lower or "visualization" in output_lower

    def test_viz_commands_available(self):
        """Test that viz commands are available."""
        from typer.testing import CliRunner

        from haplophaser.cli.viz import viz_app

        runner = CliRunner()
        result = runner.invoke(viz_app, ["--help"])

        # Check that expected commands appear in help output
        output_lower = result.output.lower()
        expected = ["proportions", "genome", "assembly", "subgenome", "expression", "synteny"]
        for cmd in expected:
            assert cmd in output_lower, f"Missing viz command: {cmd}"
