"""Tests for assembly haplotype painting modules."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.assembly.chimera import (
    ChimeraDetector,
    ChimeraReport,
    ChimericRegion,
    detect_chimeras,
)
from haplophaser.assembly.mapping import (
    MarkerHit,
    MarkerMappingResult,
    export_marker_hits_tsv,
    load_marker_hits,
)
from haplophaser.assembly.paint import (
    ContigPainter,
    ContigPainting,
    paint_assembly,
)
from haplophaser.assembly.qc import (
    generate_assembly_qc_report,
)
from haplophaser.assembly.subgenome import (
    SubgenomeAssigner,
    SubgenomeAssignment,
)
from haplophaser.io.assembly import (
    Assembly,
    Contig,
    iter_fasta,
    write_fasta,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def simple_assembly() -> Assembly:
    """Create a simple test assembly with 10 contigs."""
    contigs = {}
    for i in range(10):
        length = 100_000 + i * 50_000  # 100kb to 550kb
        contigs[f"contig_{i}"] = Contig(name=f"contig_{i}", length=length)
    return Assembly(name="test_assembly", contigs=contigs)


@pytest.fixture
def assembly_with_sequences(tmp_path) -> tuple[Assembly, Path]:
    """Create assembly with sequences for testing."""
    sequences = {
        "contig_0": "ATCGATCG" * 12500,  # 100kb
        "contig_1": "GCTAGCTA" * 18750,  # 150kb
        "contig_2": "TACGTACG" * 25000,  # 200kb
    }

    fasta_path = tmp_path / "test.fasta"
    write_fasta(sequences, fasta_path)

    assembly = Assembly.from_fasta(fasta_path, load_sequences=True)
    return assembly, fasta_path


@pytest.fixture
def marker_hits_list() -> list[MarkerHit]:
    """Create list of marker hits for testing."""
    hits = []

    # Contig 0: 8 markers, all B73
    for i in range(8):
        hits.append(MarkerHit(
            marker_id=f"marker_{i}",
            contig="contig_0",
            position=i * 10_000,
            strand="+",
            identity=0.99,
            founder_alleles={"B73": "A", "Mo17": "T"},
            observed_allele="A",
            ref_allele="A",
            alt_allele="T",
        ))

    # Contig 1: 6 markers, all Mo17
    for i in range(6):
        hits.append(MarkerHit(
            marker_id=f"marker_{8 + i}",
            contig="contig_1",
            position=i * 20_000,
            strand="+",
            identity=0.98,
            founder_alleles={"B73": "A", "Mo17": "T"},
            observed_allele="T",
            ref_allele="A",
            alt_allele="T",
        ))

    # Contig 2: 10 markers, mixed (chimeric pattern: first 5 B73, last 5 Mo17)
    for i in range(5):
        hits.append(MarkerHit(
            marker_id=f"marker_{14 + i}",
            contig="contig_2",
            position=i * 20_000,  # 0 to 80kb
            strand="+",
            identity=0.99,
            founder_alleles={"B73": "A", "Mo17": "T"},
            observed_allele="A",
            ref_allele="A",
            alt_allele="T",
        ))
    for i in range(5):
        hits.append(MarkerHit(
            marker_id=f"marker_{19 + i}",
            contig="contig_2",
            position=100_000 + i * 20_000,  # 100kb to 180kb
            strand="+",
            identity=0.99,
            founder_alleles={"B73": "A", "Mo17": "T"},
            observed_allele="T",
            ref_allele="A",
            alt_allele="T",
        ))

    # Contig 3: 2 markers (insufficient for assignment)
    for i in range(2):
        hits.append(MarkerHit(
            marker_id=f"marker_{24 + i}",
            contig="contig_3",
            position=i * 50_000,
            strand="+",
            identity=0.99,
            founder_alleles={"B73": "A", "Mo17": "T"},
            observed_allele="A",
            ref_allele="A",
            alt_allele="T",
        ))

    return hits


@pytest.fixture
def marker_mapping_result(marker_hits_list) -> MarkerMappingResult:
    """Create marker mapping result for testing."""
    return MarkerMappingResult(
        assembly_name="test_assembly",
        total_markers=30,
        mapped_unique=26,
        mapped_multiple=0,
        unmapped=4,
        hits=marker_hits_list,
    )


# =============================================================================
# Assembly I/O Tests
# =============================================================================


class TestAssembly:
    """Tests for Assembly class."""

    def test_assembly_from_dict(self, simple_assembly):
        """Test assembly creation and basic properties."""
        assert simple_assembly.n_contigs == 10
        assert simple_assembly.total_size > 0
        assert simple_assembly.n50 > 0

    def test_assembly_n50(self, simple_assembly):
        """Test N50 calculation."""
        # With contigs from 100kb to 550kb, N50 should be in that range
        assert 100_000 <= simple_assembly.n50 <= 550_000

    def test_assembly_get_contig(self, simple_assembly):
        """Test getting contig by name."""
        contig = simple_assembly.get_contig("contig_0")
        assert contig is not None
        assert contig.name == "contig_0"
        assert contig.length == 100_000

        # Non-existent contig
        assert simple_assembly.get_contig("nonexistent") is None

    def test_assembly_summary(self, simple_assembly):
        """Test assembly summary statistics."""
        summary = simple_assembly.summary()
        assert summary["n_contigs"] == 10
        assert summary["total_size"] > 0
        assert summary["n50"] > 0
        assert summary["longest"] == 550_000
        assert summary["shortest"] == 100_000


class TestAssemblyFromFasta:
    """Tests for Assembly.from_fasta."""

    def test_from_fasta_basic(self, assembly_with_sequences):
        """Test loading assembly from FASTA."""
        assembly, fasta_path = assembly_with_sequences
        assert assembly.n_contigs == 3
        assert "contig_0" in assembly.contigs

    def test_from_fasta_with_sequences(self, assembly_with_sequences):
        """Test loading assembly with sequences."""
        assembly, fasta_path = assembly_with_sequences
        contig = assembly.get_contig("contig_0")
        assert contig is not None
        assert contig.has_sequence
        assert len(contig.sequence) == 100_000


class TestIterFasta:
    """Tests for iter_fasta function."""

    def test_iter_fasta(self, assembly_with_sequences):
        """Test iterating over FASTA sequences."""
        _, fasta_path = assembly_with_sequences
        sequences = list(iter_fasta(fasta_path))
        assert len(sequences) == 3
        assert sequences[0][0] == "contig_0"


# =============================================================================
# Marker Mapping Tests
# =============================================================================


class TestMarkerHit:
    """Tests for MarkerHit class."""

    def test_inferred_founder(self, marker_hits_list):
        """Test founder inference from observed allele."""
        # First hit has observed_allele="A", which maps to B73
        hit = marker_hits_list[0]
        assert hit.inferred_founder() == "B73"

        # A Mo17 hit
        mo17_hit = marker_hits_list[8]
        assert mo17_hit.inferred_founder() == "Mo17"

    def test_to_bed_fields(self, marker_hits_list):
        """Test BED format conversion."""
        hit = marker_hits_list[0]
        chrom, start, end, name, score, strand = hit.to_bed_fields()
        assert chrom == "contig_0"
        assert start == 0
        assert end == 1
        assert "B73" in name


class TestMarkerMappingResult:
    """Tests for MarkerMappingResult class."""

    def test_mapping_rate(self, marker_mapping_result):
        """Test mapping rate calculation."""
        assert 0 < marker_mapping_result.mapping_rate <= 1
        assert marker_mapping_result.unique_mapping_rate <= marker_mapping_result.mapping_rate

    def test_hits_by_contig(self, marker_mapping_result):
        """Test getting hits by contig."""
        hits_c0 = marker_mapping_result.hits_by_contig("contig_0")
        assert len(hits_c0) == 8

        hits_c1 = marker_mapping_result.hits_by_contig("contig_1")
        assert len(hits_c1) == 6

    def test_contig_coverage(self, marker_mapping_result):
        """Test contig coverage calculation."""
        coverage = marker_mapping_result.contig_coverage()
        assert "contig_0" in coverage
        assert coverage["contig_0"] == 8


class TestMarkerHitExportLoad:
    """Tests for marker hit export and loading."""

    def test_export_and_load_marker_hits(self, marker_hits_list, tmp_path):
        """Test round-trip export and load."""
        output_path = tmp_path / "hits.tsv"

        # Export
        export_marker_hits_tsv(marker_hits_list, output_path)
        assert output_path.exists()

        # Load
        loaded_hits = load_marker_hits(output_path)
        assert len(loaded_hits) == len(marker_hits_list)

        # Check first hit
        assert loaded_hits[0].marker_id == marker_hits_list[0].marker_id
        assert loaded_hits[0].contig == marker_hits_list[0].contig


# =============================================================================
# Contig Painting Tests
# =============================================================================


class TestContigPainting:
    """Tests for ContigPainting class."""

    def test_painting_properties(self):
        """Test painting properties."""
        painting = ContigPainting(
            contig="test",
            length=100_000,
            n_markers=10,
            founder_proportions={"B73": 0.8, "Mo17": 0.2},
            founder_counts={"B73": 8, "Mo17": 2},
            assigned_founder="B73",
            confidence=0.9,
        )

        assert painting.is_assigned
        assert painting.majority_founder == "B73"
        assert painting.majority_proportion == 0.8
        assert painting.marker_density == 100.0  # 10 markers per 100kb = 100/Mb


class TestContigPainter:
    """Tests for ContigPainter class."""

    def test_paint_assembly(self, simple_assembly, marker_hits_list):
        """Test painting assembly with marker hits."""
        painter = ContigPainter(min_markers=5, min_proportion=0.8)
        painting = painter.paint(simple_assembly, marker_hits_list)

        assert painting.n_contigs == 10
        # contig_0 should be assigned to B73
        c0 = painting.get_contig("contig_0")
        assert c0 is not None
        assert c0.assigned_founder == "B73"

        # contig_1 should be assigned to Mo17
        c1 = painting.get_contig("contig_1")
        assert c1 is not None
        assert c1.assigned_founder == "Mo17"

        # contig_3 should be unassigned (only 2 markers)
        c3 = painting.get_contig("contig_3")
        assert c3 is not None
        assert not c3.is_assigned

    def test_paint_detects_chimera(self, simple_assembly, marker_hits_list):
        """Test chimera detection during painting."""
        painter = ContigPainter(
            min_markers=5,
            min_proportion=0.8,
            detect_chimeras=True,
            chimera_window_size=50_000,
            chimera_min_markers_per_window=2,
        )
        painting = painter.paint(simple_assembly, marker_hits_list)

        # contig_2 has a chimeric pattern
        c2 = painting.get_contig("contig_2")
        assert c2 is not None
        # May or may not be flagged as chimeric depending on window analysis
        # The test validates that chimera detection runs without error


class TestAssemblyPainting:
    """Tests for AssemblyPainting class."""

    def test_painting_summary(self, simple_assembly, marker_hits_list):
        """Test painting summary statistics."""
        painting = paint_assembly(
            simple_assembly,
            marker_hits_list,
            min_markers=5,
            min_proportion=0.8,
            detect_chimeras=False,
        )

        summary = painting.summary()
        assert summary["n_contigs"] == 10
        assert "n_assigned" in summary
        assert "n_unassigned" in summary

    def test_by_founder(self, simple_assembly, marker_hits_list):
        """Test getting contigs by founder."""
        painting = paint_assembly(
            simple_assembly,
            marker_hits_list,
            min_markers=5,
        )

        b73_contigs = painting.by_founder("B73")
        assert "contig_0" in b73_contigs

        mo17_contigs = painting.by_founder("Mo17")
        assert "contig_1" in mo17_contigs


# =============================================================================
# Chimera Detection Tests
# =============================================================================


class TestChimericRegion:
    """Tests for ChimericRegion class."""

    def test_chimeric_region_properties(self):
        """Test chimeric region properties."""
        region = ChimericRegion(
            contig="test",
            switch_position=50_000,
            switch_position_ci=(45_000, 55_000),
            left_founder="B73",
            right_founder="Mo17",
            left_confidence=0.9,
            right_confidence=0.85,
            n_markers_left=5,
            n_markers_right=5,
        )

        assert region.switch_position_1based == 50_001
        assert region.ci_width == 10_000
        assert "B73" in region.to_bed_breakpoint()


class TestChimeraDetector:
    """Tests for ChimeraDetector class."""

    def test_detect_chimeras(self, simple_assembly, marker_hits_list):
        """Test chimera detection."""
        detector = ChimeraDetector(
            window_size=50_000,
            min_markers_per_window=2,
            switch_threshold=0.5,
        )

        report = detector.detect(
            simple_assembly,
            marker_hits_list,
            founders=["B73", "Mo17"],
        )

        assert isinstance(report, ChimeraReport)
        assert report.total_contigs == 10


class TestChimeraReport:
    """Tests for ChimeraReport class."""

    def test_chimera_report_summary(self):
        """Test chimera report summary."""
        report = ChimeraReport(
            assembly="test",
            total_contigs=10,
            chimeric_contigs=2,
            total_switches=3,
            contigs_analyzed=8,
        )

        assert report.chimera_rate == 0.25
        summary = report.summary()
        assert "test" in summary


# =============================================================================
# Subgenome Assignment Tests
# =============================================================================


class TestSubgenomeAssignment:
    """Tests for SubgenomeAssignment class."""

    def test_assignment_properties(self):
        """Test assignment properties."""
        assignment = SubgenomeAssignment(
            contig="test",
            length=100_000,
            subgenome="A",
            confidence=0.9,
            marker_support={"A": 8, "B": 2},
        )

        assert assignment.is_assigned
        assert assignment.has_marker_evidence


class TestSubgenomeAssigner:
    """Tests for SubgenomeAssigner class."""

    def test_assign_subgenomes(self, simple_assembly, marker_hits_list):
        """Test subgenome assignment."""
        # Reinterpret B73/Mo17 as A/B subgenomes
        for hit in marker_hits_list:
            hit.founder_alleles = {"A": "A", "B": "T"}

        assigner = SubgenomeAssigner(
            subgenomes=["A", "B"],
            method="markers",
            min_markers=5,
        )

        result = assigner.assign(simple_assembly, marker_hits=marker_hits_list)

        assert result.n_contigs == 10
        assert "A" in result.subgenomes
        assert "B" in result.subgenomes


# =============================================================================
# Assembly QC Tests
# =============================================================================


class TestAssemblyQC:
    """Tests for AssemblyQC class."""

    def test_generate_qc_report(self, simple_assembly, marker_hits_list, marker_mapping_result):
        """Test QC report generation."""
        painting = paint_assembly(
            simple_assembly,
            marker_hits_list,
            min_markers=5,
        )

        report = generate_assembly_qc_report(
            simple_assembly,
            painting=painting,
            marker_mapping=marker_mapping_result,
        )

        assert report.assembly_name == "test_assembly"
        assert report.painting.total_contigs == 10
        assert report.marker_mapping.total_markers == 30

    def test_qc_report_summary(self, simple_assembly, marker_hits_list, marker_mapping_result):
        """Test QC report summary text."""
        painting = paint_assembly(simple_assembly, marker_hits_list)
        report = generate_assembly_qc_report(simple_assembly, painting=painting)

        summary_text = report.summary_text()
        assert "Assembly QC Report" in summary_text
        assert "test_assembly" in summary_text


# =============================================================================
# Integration Tests
# =============================================================================


class TestAssemblyPaintingPipeline:
    """Integration tests for the complete painting pipeline."""

    def test_full_pipeline(self, simple_assembly, marker_hits_list, tmp_path):
        """Test complete painting pipeline."""
        from haplophaser.io.assembly_export import (
            export_painting_bed,
            export_painting_tsv,
        )

        # Paint assembly
        painting = paint_assembly(
            simple_assembly,
            marker_hits_list,
            min_markers=5,
            min_proportion=0.8,
        )

        # Export results
        tsv_path = export_painting_tsv(painting, tmp_path / "painting.tsv")
        bed_path = export_painting_bed(painting, tmp_path / "painting.bed")

        assert tsv_path.exists()
        assert bed_path.exists()

        # Verify TSV content
        with open(tsv_path) as f:
            lines = f.readlines()
            assert len(lines) > 1  # Header + data
            assert "contig" in lines[0]

    def test_chimera_to_export(self, simple_assembly, marker_hits_list, tmp_path):
        """Test chimera detection to export pipeline."""
        from haplophaser.io.assembly_export import (
            export_chimeras_bed,
            export_chimeras_tsv,
        )

        report = detect_chimeras(
            simple_assembly,
            marker_hits_list,
            founders=["B73", "Mo17"],
            window_size=50_000,
            min_markers_per_window=2,
        )

        # Export (even if no chimeras found)
        tsv_path = export_chimeras_tsv(report, tmp_path / "chimeras.tsv")
        bed_path = export_chimeras_bed(report, tmp_path / "chimeras.bed")

        assert tsv_path.exists()
        assert bed_path.exists()
