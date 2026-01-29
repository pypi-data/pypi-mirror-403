"""Tests for visualization module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestVizUtils:
    """Tests for viz utilities."""

    def test_get_founder_colors(self):
        """Test founder color assignment."""
        from haplophaser.viz.utils import get_founder_colors

        # Mock the chromoplot module
        with patch("haplophaser.viz.utils.cp") as mock_cp:
            mock_cp.founder_colors.return_value = {
                "B73": "#FF0000",
                "Mo17": "#00FF00",
                "W22": "#0000FF",
            }

            colors = get_founder_colors(["B73", "Mo17", "W22"], use_maize_colors=False)

            assert len(colors) == 3
            assert "B73" in colors
            mock_cp.founder_colors.assert_called_once()

    def test_results_to_bed(self, tmp_path: Path):
        """Test converting results to BED format."""
        from haplophaser.viz.utils import results_to_bed

        # Create mock blocks
        class MockBlock:
            def __init__(self, chrom, start, end, founder):
                self.chrom = chrom
                self.start = start
                self.end = end
                self.founder = founder
                self.confidence = 0.95

        blocks = [
            MockBlock("chr1", 0, 1000, "B73"),
            MockBlock("chr1", 1000, 2000, "Mo17"),
        ]

        output = tmp_path / "output.bed"
        result = results_to_bed(blocks, output)

        assert result.exists()
        content = result.read_text()
        assert "chr1" in content
        assert "B73" in content
        assert "Mo17" in content

    def test_load_reference_fai(self, test_fai: Path):
        """Test loading reference from FAI file."""
        from haplophaser.viz.utils import load_reference

        with patch("haplophaser.viz.utils.cp") as mock_cp:
            mock_coords = MagicMock()
            mock_cp.GenomeCoordinates.from_fai.return_value = mock_coords

            coords = load_reference(test_fai)

            assert coords == mock_coords
            mock_cp.GenomeCoordinates.from_fai.assert_called_once_with(test_fai)


class TestProportionFigure:
    """Tests for ProportionFigure class."""

    def test_creation(self, test_fai: Path):
        """Test figure creation."""
        with patch("haplophaser.viz.proportion.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_coords.n_chromosomes = 3
            mock_load.return_value = mock_coords

            from haplophaser.viz import ProportionFigure

            fig = ProportionFigure(test_fai, region="chr1:1-1000000")

            assert fig.coordinates is not None
            assert fig.region == "chr1:1-1000000"
            assert len(fig._tracks) == 0

    def test_add_tracks(self, test_fai: Path, test_haplotypes: Path):
        """Test adding tracks to figure."""
        with patch("haplophaser.viz.proportion.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import ProportionFigure

            fig = ProportionFigure(test_fai)
            fig.add_ideogram()
            fig.add_haplotypes(test_haplotypes)
            fig.add_scale_bar()

            assert len(fig._tracks) == 3

    def test_fluent_interface(self, test_fai: Path, test_haplotypes: Path):
        """Test fluent interface (method chaining)."""
        with patch("haplophaser.viz.proportion.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import ProportionFigure

            fig = (
                ProportionFigure(test_fai)
                .add_ideogram()
                .add_haplotypes(test_haplotypes)
                .add_scale_bar()
            )

            assert len(fig._tracks) == 3


class TestProportionGenomeFigure:
    """Tests for ProportionGenomeFigure class."""

    def test_creation(self, test_fai: Path):
        """Test genome-wide figure creation."""
        with patch("haplophaser.viz.proportion.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_coords.n_chromosomes = 3
            mock_load.return_value = mock_coords

            from haplophaser.viz import ProportionGenomeFigure

            fig = ProportionGenomeFigure(test_fai, n_cols=5)

            assert fig.n_cols == 5
            assert fig.coordinates is not None


class TestAssemblyPaintingFigure:
    """Tests for AssemblyPaintingFigure class."""

    def test_creation(self, test_fai: Path):
        """Test assembly figure creation."""
        with patch("haplophaser.viz.assembly.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import AssemblyPaintingFigure

            fig = AssemblyPaintingFigure(test_fai)

            assert fig.coordinates is not None

    def test_add_chimeras(self, test_fai: Path, test_haplotypes: Path):
        """Test adding chimera markers."""
        with patch("haplophaser.viz.assembly.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import AssemblyPaintingFigure

            fig = AssemblyPaintingFigure(test_fai)
            fig.add_painting(test_haplotypes)
            fig.add_chimeras(test_haplotypes)  # Using same file for simplicity

            assert len(fig._tracks) == 2


class TestSubgenomeFigure:
    """Tests for SubgenomeFigure class."""

    def test_creation(self, test_fai: Path):
        """Test subgenome figure creation."""
        with patch("haplophaser.viz.subgenome.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import SubgenomeFigure

            fig = SubgenomeFigure(
                test_fai, subgenomes=["maize1", "maize2"], organism="maize"
            )

            assert fig.subgenomes == ["maize1", "maize2"]
            assert fig.organism == "maize"

    def test_get_subgenome_colors(self):
        """Test subgenome color assignment."""
        from haplophaser.viz.subgenome import get_subgenome_colors

        with patch("haplophaser.viz.subgenome.cp") as mock_cp:
            mock_cp.get_palette.return_value = ["#FF0000", "#00FF00"]

            # Test maize colors
            colors = get_subgenome_colors(["maize1", "maize2"], organism="maize")
            assert "maize1" in colors
            assert "maize2" in colors

            # Test wheat colors
            colors = get_subgenome_colors(["A", "B", "D"], organism="wheat")
            assert "A" in colors
            assert "B" in colors
            assert "D" in colors


class TestExpressionBiasFigure:
    """Tests for ExpressionBiasFigure class."""

    @pytest.fixture
    def mock_matplotlib(self):
        """Mock matplotlib for testing."""
        with patch("haplophaser.viz.expression.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            yield mock_plt, mock_fig, mock_ax

    def test_creation(self, test_expression_bias: Path, mock_matplotlib):
        """Test expression figure creation."""
        from haplophaser.viz import ExpressionBiasFigure

        fig = ExpressionBiasFigure(test_expression_bias)

        assert fig.bias_results is not None
        assert fig.figsize == (8, 6)

    def test_plot_ma(self, test_expression_bias: Path, mock_matplotlib):
        """Test MA plot generation."""
        mock_plt, mock_fig, mock_ax = mock_matplotlib

        from haplophaser.viz import ExpressionBiasFigure

        fig = ExpressionBiasFigure(test_expression_bias)
        result = fig.plot_ma()

        assert result is fig  # Fluent interface
        mock_ax.scatter.assert_called_once()
        mock_ax.axhline.assert_called()

    def test_plot_distribution(self, test_expression_bias: Path, mock_matplotlib):
        """Test distribution plot generation."""
        mock_plt, mock_fig, mock_ax = mock_matplotlib

        from haplophaser.viz import ExpressionBiasFigure

        fig = ExpressionBiasFigure(test_expression_bias)
        result = fig.plot_bias_distribution()

        assert result is fig
        mock_ax.hist.assert_called_once()

    def test_save(self, test_expression_bias: Path, mock_matplotlib, tmp_path: Path):
        """Test figure saving."""
        mock_plt, mock_fig, mock_ax = mock_matplotlib

        from haplophaser.viz import ExpressionBiasFigure

        fig = ExpressionBiasFigure(test_expression_bias)
        fig.plot_ma()

        output = tmp_path / "test.pdf"
        fig.save(output)

        mock_fig.savefig.assert_called_once()


class TestSyntenyFigure:
    """Tests for SyntenyFigure class."""

    def test_creation(self, test_fai: Path):
        """Test synteny figure creation."""
        with patch("haplophaser.viz.comparative.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import SyntenyFigure

            fig = SyntenyFigure(test_fai, test_fai)  # Using same for both

            assert fig.ref_coordinates is not None
            assert fig.query_coordinates is not None

    def test_add_tracks(self, test_fai: Path, test_haplotypes: Path):
        """Test adding tracks to synteny figure."""
        with patch("haplophaser.viz.comparative.load_reference") as mock_load:
            mock_coords = MagicMock()
            mock_load.return_value = mock_coords

            from haplophaser.viz import SyntenyFigure

            fig = SyntenyFigure(test_fai, test_fai)
            fig.add_ref_ideogram()
            fig.add_query_ideogram()
            fig.add_synteny(test_haplotypes)

            assert len(fig._ref_tracks) == 1
            assert len(fig._query_tracks) == 1
            assert fig._synteny_track is not None


class TestPresets:
    """Tests for preset visualization functions."""

    def test_plot_haplotype_proportions_imports(self):
        """Test that preset function can be imported."""
        from haplophaser.viz import plot_haplotype_proportions

        assert callable(plot_haplotype_proportions)

    def test_plot_genome_haplotypes_imports(self):
        """Test that preset function can be imported."""
        from haplophaser.viz import plot_genome_haplotypes

        assert callable(plot_genome_haplotypes)

    def test_plot_assembly_painting_imports(self):
        """Test that preset function can be imported."""
        from haplophaser.viz import plot_assembly_painting

        assert callable(plot_assembly_painting)

    def test_plot_subgenome_assignment_imports(self):
        """Test that preset function can be imported."""
        from haplophaser.viz import plot_subgenome_assignment

        assert callable(plot_subgenome_assignment)

    def test_plot_expression_bias_imports(self):
        """Test that preset function can be imported."""
        from haplophaser.viz import plot_expression_bias

        assert callable(plot_expression_bias)

    def test_plot_synteny_imports(self):
        """Test that preset function can be imported."""
        from haplophaser.viz import plot_synteny

        assert callable(plot_synteny)


class TestVizModuleExports:
    """Test module exports."""

    def test_all_exports_exist(self):
        """Test that all exported items exist."""
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
