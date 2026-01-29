"""Tests for subgenome data models."""

from __future__ import annotations

import pytest

from haplophaser.subgenome.models import (
    Subgenome,
    SubgenomeConfig,
)


class TestSubgenome:
    """Tests for Subgenome dataclass."""

    def test_creation(self):
        """Test basic subgenome creation."""
        sg = Subgenome("maize1", "Dominant subgenome", "#e41a1c")
        assert sg.name == "maize1"
        assert sg.description == "Dominant subgenome"
        assert sg.color == "#e41a1c"

    def test_equality(self):
        """Test subgenome equality based on name."""
        sg1 = Subgenome("A", "First")
        sg2 = Subgenome("A", "Second")
        sg3 = Subgenome("B", "First")

        assert sg1 == sg2  # Same name
        assert sg1 != sg3  # Different name

    def test_hash(self):
        """Test subgenome can be used in sets."""
        sg1 = Subgenome("A")
        sg2 = Subgenome("A")

        s = {sg1, sg2}
        assert len(s) == 1


class TestSubgenomeConfig:
    """Tests for SubgenomeConfig."""

    def test_maize_default(self):
        """Test maize default configuration."""
        config = SubgenomeConfig.maize_default()

        assert config.n_subgenomes == 2
        assert "maize1" in config.subgenome_names
        assert "maize2" in config.subgenome_names
        assert config.reference_species == "Zm-B73-v5"
        assert "Sorghum_bicolor" in config.outgroup_species

    def test_wheat_default(self):
        """Test wheat default configuration."""
        config = SubgenomeConfig.wheat_default()

        assert config.n_subgenomes == 3
        assert set(config.subgenome_names) == {"A", "B", "D"}

    def test_brassica_default(self):
        """Test Brassica default configuration."""
        config = SubgenomeConfig.brassica_default()

        assert config.n_subgenomes == 2
        assert set(config.subgenome_names) == {"A", "C"}

    def test_get_subgenome(self, maize_config):
        """Test getting subgenome by name."""
        sg = maize_config.get_subgenome("maize1")
        assert sg is not None
        assert sg.name == "maize1"

        assert maize_config.get_subgenome("nonexistent") is None


class TestSubgenomeAssignment:
    """Tests for SubgenomeAssignment."""

    def test_creation(self, subgenome_assignment):
        """Test assignment creation."""
        assert subgenome_assignment.chrom == "chr1"
        assert subgenome_assignment.start == 0
        assert subgenome_assignment.end == 1_000_000
        assert subgenome_assignment.subgenome == "maize1"
        assert subgenome_assignment.confidence == 0.95

    def test_length(self, subgenome_assignment):
        """Test length calculation."""
        assert subgenome_assignment.length == 1_000_000

    def test_midpoint(self, subgenome_assignment):
        """Test midpoint calculation."""
        assert subgenome_assignment.midpoint == 500_000

    def test_overlaps(self, subgenome_assignment):
        """Test overlap detection."""
        # Overlapping
        assert subgenome_assignment.overlaps("chr1", 500_000, 1_500_000)
        assert subgenome_assignment.overlaps("chr1", 0, 100)

        # Not overlapping
        assert not subgenome_assignment.overlaps("chr1", 1_000_000, 2_000_000)
        assert not subgenome_assignment.overlaps("chr2", 0, 1_000_000)

    def test_to_bed_fields(self, subgenome_assignment):
        """Test BED format conversion."""
        fields = subgenome_assignment.to_bed_fields()
        assert len(fields) == 6
        assert fields[0] == "chr1"
        assert fields[1] == 0
        assert fields[2] == 1_000_000
        assert "maize1" in fields[3]
        assert fields[4] == 950  # confidence * 1000

    def test_to_dict(self, subgenome_assignment):
        """Test dictionary conversion."""
        d = subgenome_assignment.to_dict()
        assert d["chrom"] == "chr1"
        assert d["subgenome"] == "maize1"
        assert d["confidence"] == 0.95


class TestSubgenomeAssignmentResult:
    """Tests for SubgenomeAssignmentResult."""

    def test_creation(self, assignment_result):
        """Test result creation."""
        assert assignment_result.query_name == "test_assembly"
        assert assignment_result.n_assignments == 3

    def test_total_assigned_bp(self, assignment_result):
        """Test total base pairs calculation."""
        expected = 1_000_000 + 1_000_000 + 500_000
        assert assignment_result.total_assigned_bp == expected

    def test_assignments_by_subgenome(self, assignment_result):
        """Test filtering by subgenome."""
        maize1 = assignment_result.assignments_by_subgenome("maize1")
        assert len(maize1) == 2

        maize2 = assignment_result.assignments_by_subgenome("maize2")
        assert len(maize2) == 1

    def test_assignments_for_region(self, assignment_result):
        """Test regional query."""
        overlapping = assignment_result.assignments_for_region("chr1", 500_000, 1_500_000)
        assert len(overlapping) == 2

    def test_summary(self, assignment_result):
        """Test summary generation."""
        summary = assignment_result.summary()
        assert summary["n_regions"] == 3
        assert "by_subgenome" in summary
        assert "maize1" in summary["by_subgenome"]


class TestSyntenyBlock:
    """Tests for SyntenyBlock."""

    def test_creation(self, synteny_block):
        """Test block creation."""
        assert synteny_block.query_chrom == "chr1"
        assert synteny_block.orientation == "+"
        assert synteny_block.n_anchors == 50

    def test_lengths(self, synteny_block):
        """Test length calculations."""
        assert synteny_block.query_length == 1_000_000
        assert synteny_block.ref_length == 1_000_000

    def test_is_inverted(self, synteny_blocks):
        """Test inversion detection."""
        assert not synteny_blocks[0].is_inverted
        assert synteny_blocks[1].is_inverted

    def test_overlaps(self, synteny_block):
        """Test overlap detection."""
        assert synteny_block.query_overlaps("chr1", 500_000, 1_500_000)
        assert synteny_block.ref_overlaps("chr1", 1_000_000, 2_000_000)


class TestSubgenomeMarker:
    """Tests for SubgenomeMarker."""

    def test_creation(self, subgenome_marker):
        """Test marker creation."""
        assert subgenome_marker.marker_id == "chr1_1000"
        assert subgenome_marker.pos == 1000
        assert subgenome_marker.divergence == 0.05

    def test_pos_1based(self, subgenome_marker):
        """Test 1-based position conversion."""
        assert subgenome_marker.pos_1based == 1001

    def test_allele_for_subgenome(self, subgenome_marker):
        """Test allele lookup by subgenome."""
        assert subgenome_marker.allele_for_subgenome("maize1") == "A"
        assert subgenome_marker.allele_for_subgenome("maize2") == "G"
        assert subgenome_marker.allele_for_subgenome("unknown") is None

    def test_subgenome_for_allele(self, subgenome_marker):
        """Test subgenome lookup by allele."""
        assert subgenome_marker.subgenome_for_allele("A") == "maize1"
        assert subgenome_marker.subgenome_for_allele("G") == "maize2"
        assert subgenome_marker.subgenome_for_allele("C") is None


class TestGeneSubgenomeCall:
    """Tests for GeneSubgenomeCall."""

    def test_creation(self, gene_call):
        """Test gene call creation."""
        assert gene_call.gene_id == "Zm00001d001234"
        assert gene_call.subgenome == "maize1"
        assert gene_call.orthogroup == "OG0000001"

    def test_is_assigned(self, gene_calls):
        """Test assignment status."""
        assert gene_calls[0].is_assigned
        assert gene_calls[1].is_assigned
        assert not gene_calls[2].is_assigned

    def test_length(self, gene_call):
        """Test gene length."""
        assert gene_call.length == 5000


class TestHomeologPair:
    """Tests for HomeologPair."""

    def test_creation(self, homeolog_pair):
        """Test pair creation."""
        assert homeolog_pair.gene1_id == "Zm00001d001234"
        assert homeolog_pair.gene2_id == "Zm00001d054321"
        assert homeolog_pair.ks == 0.15
        assert homeolog_pair.synteny_support

    def test_ka_ks_ratio(self, homeolog_pair):
        """Test Ka/Ks ratio calculation."""
        ratio = homeolog_pair.ka_ks_ratio
        assert ratio is not None
        assert ratio == pytest.approx(0.02 / 0.15, rel=0.01)

    def test_is_purifying(self, homeolog_pair):
        """Test purifying selection detection."""
        assert homeolog_pair.is_purifying is True

    def test_genes(self, homeolog_pair):
        """Test gene tuple."""
        genes = homeolog_pair.genes()
        assert "Zm00001d001234" in genes
        assert "Zm00001d054321" in genes

    def test_involves_gene(self, homeolog_pair):
        """Test gene involvement check."""
        assert homeolog_pair.involves_gene("Zm00001d001234")
        assert homeolog_pair.involves_gene("Zm00001d054321")
        assert not homeolog_pair.involves_gene("other_gene")

    def test_partner(self, homeolog_pair):
        """Test partner gene lookup."""
        assert homeolog_pair.partner("Zm00001d001234") == "Zm00001d054321"
        assert homeolog_pair.partner("Zm00001d054321") == "Zm00001d001234"
        assert homeolog_pair.partner("other") is None


class TestHomeologResult:
    """Tests for HomeologResult."""

    def test_creation(self, homeolog_result):
        """Test result creation."""
        assert homeolog_result.n_pairs == 3

    def test_median_ks(self, homeolog_result):
        """Test median Ks calculation."""
        # Ks values: 0.15, 0.12, 0.18
        assert homeolog_result.median_ks == pytest.approx(0.15, rel=0.01)

    def test_mean_identity(self, homeolog_result):
        """Test mean identity calculation."""
        # Identities: 0.85, 0.88, 0.82
        expected = (0.85 + 0.88 + 0.82) / 3
        assert homeolog_result.mean_identity == pytest.approx(expected, rel=0.01)

    def test_pairs_by_subgenome_combination(self, homeolog_result):
        """Test filtering by subgenome pair."""
        pairs = homeolog_result.pairs_by_subgenome_combination("maize1", "maize2")
        assert len(pairs) == 3  # All pairs are between maize1 and maize2

    def test_to_dataframe(self, homeolog_result):
        """Test DataFrame conversion."""
        df = homeolog_result.to_dataframe()
        assert len(df) == 3
        assert "gene1_id" in df.columns
        assert "ks" in df.columns
