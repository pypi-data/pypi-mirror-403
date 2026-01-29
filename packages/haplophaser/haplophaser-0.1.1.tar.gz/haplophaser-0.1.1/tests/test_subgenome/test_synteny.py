"""Tests for synteny-based subgenome assignment."""

from __future__ import annotations

from haplophaser.io.synteny import (
    load_reference_assignments,
    load_synteny,
)
from haplophaser.subgenome.models import SubgenomeConfig
from haplophaser.subgenome.synteny import SyntenySubgenomeAssigner, assign_by_synteny


class TestSyntenyParsing:
    """Tests for synteny file parsing."""

    def test_load_tsv_format(self, tmp_synteny_tsv):
        """Test loading TSV synteny file."""
        blocks = load_synteny(tmp_synteny_tsv)

        assert len(blocks) == 3
        assert blocks[0].query_chrom == "chr1"
        assert blocks[0].orientation == "+"
        assert blocks[1].orientation == "-"

    def test_load_with_min_length(self, tmp_synteny_tsv):
        """Test loading with minimum length filter."""
        blocks = load_synteny(tmp_synteny_tsv, min_length=600_000)

        # Only blocks with length >= 600000 should be included
        assert all(b.query_length >= 600_000 or b.ref_length >= 600_000 for b in blocks)

    def test_load_reference_assignments(self, tmp_reference_assignments):
        """Test loading reference subgenome assignments."""
        assignments = load_reference_assignments(tmp_reference_assignments)

        assert "chr1" in assignments
        assert "chr2" in assignments
        assert len(assignments["chr1"]) == 2

        # Check first assignment
        start, end, sg = assignments["chr1"][0]
        assert start == 0
        assert end == 1_000_000
        assert sg == "maize1"


class TestSyntenySubgenomeAssigner:
    """Tests for SyntenySubgenomeAssigner."""

    def test_assign_from_synteny(
        self, tmp_synteny_tsv, tmp_reference_assignments, maize_config
    ):
        """Test assigning subgenomes via synteny."""
        assigner = SyntenySubgenomeAssigner(
            config=maize_config,
            min_block_size=10_000,
        )

        result = assigner.assign(
            synteny_blocks=tmp_synteny_tsv,
            reference_assignments=tmp_reference_assignments,
        )

        assert result.n_assignments > 0
        assert result.method == "synteny"

    def test_assign_with_blocks_list(
        self, synteny_blocks, tmp_reference_assignments, maize_config
    ):
        """Test assigning with pre-parsed blocks."""
        assigner = SyntenySubgenomeAssigner(
            config=maize_config,
            min_block_size=10_000,
        )

        result = assigner.assign(
            synteny_blocks=synteny_blocks,
            reference_assignments=tmp_reference_assignments,
        )

        assert result.n_assignments > 0

    def test_min_block_size_filter(
        self, tmp_synteny_tsv, tmp_reference_assignments, maize_config
    ):
        """Test that min_block_size filters small blocks."""
        # With very large min_block_size, no blocks should qualify
        assigner = SyntenySubgenomeAssigner(
            config=maize_config,
            min_block_size=10_000_000,
        )

        result = assigner.assign(
            synteny_blocks=tmp_synteny_tsv,
            reference_assignments=tmp_reference_assignments,
        )

        assert result.n_assignments == 0


class TestAssignBySyntenyFunction:
    """Tests for convenience function."""

    def test_basic_usage(self, tmp_synteny_tsv, tmp_reference_assignments):
        """Test basic convenience function usage."""
        result = assign_by_synteny(
            synteny_blocks=tmp_synteny_tsv,
            reference_assignments=tmp_reference_assignments,
            min_block_size=10_000,
        )

        assert result is not None
        assert result.method == "synteny"

    def test_with_custom_config(self, tmp_synteny_tsv, tmp_reference_assignments):
        """Test with custom configuration."""
        config = SubgenomeConfig.wheat_default()

        result = assign_by_synteny(
            synteny_blocks=tmp_synteny_tsv,
            reference_assignments=tmp_reference_assignments,
            config=config,
        )

        # Should work but likely no assignments since wheat has A/B/D
        assert result is not None
