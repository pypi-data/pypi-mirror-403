"""Tests for marker export functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.io.markers import (
    export_all_marker_formats,
    export_density_bedgraph,
    export_gaps_bed,
    export_markers_bed,
    export_markers_tsv,
    export_markers_vcf,
    export_quality_report,
)
from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerSet,
    MarkerClassification,
)
from haplophaser.markers.quality import MarkerQualityAssessment


@pytest.fixture
def test_markers() -> DiagnosticMarkerSet:
    """Create test marker set."""
    return DiagnosticMarkerSet(
        markers=[
            DiagnosticMarker(
                variant_id="chr1:1000:A:T",
                chrom="chr1",
                pos=1000,
                ref="A",
                alt="T",
                founder_alleles={"B73": "A", "Mo17": "T"},
                founder_frequencies={
                    "B73": {"A": 1.0, "T": 0.0},
                    "Mo17": {"A": 0.0, "T": 1.0},
                },
                confidence=0.95,
                classification=MarkerClassification.FULLY_DIAGNOSTIC,
                distinguishes=("B73", "Mo17"),
            ),
            DiagnosticMarker(
                variant_id="chr1:2000:G:C",
                chrom="chr1",
                pos=2000,
                ref="G",
                alt="C",
                founder_alleles={"B73": "G", "Mo17": "C"},
                founder_frequencies={
                    "B73": {"G": 0.9, "C": 0.1},
                    "Mo17": {"G": 0.1, "C": 0.9},
                },
                confidence=0.85,
                classification=MarkerClassification.PARTIALLY_DIAGNOSTIC,
                distinguishes=("B73", "Mo17"),
            ),
            DiagnosticMarker(
                variant_id="chr2:5000:T:A",
                chrom="chr2",
                pos=5000,
                ref="T",
                alt="A",
                founder_alleles={"B73": "T", "Mo17": "A"},
                founder_frequencies={
                    "B73": {"T": 1.0, "A": 0.0},
                    "Mo17": {"T": 0.0, "A": 1.0},
                },
                confidence=0.92,
                classification=MarkerClassification.FULLY_DIAGNOSTIC,
                distinguishes=("B73", "Mo17"),
            ),
        ],
        founders=["B73", "Mo17"],
    )


class TestExportMarkersBed:
    """Tests for BED export."""

    def test_basic_export(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test basic BED export."""
        output_path = tmp_path / "markers.bed"
        export_markers_bed(test_markers, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Should have track line + 3 markers
        assert len(lines) == 4
        assert lines[0].startswith("track")

        # Check first marker
        fields = lines[1].split("\t")
        assert fields[0] == "chr1"
        assert fields[1] == "1000"
        assert fields[2] == "1001"

    def test_sorted_output(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test that output is sorted by position."""
        output_path = tmp_path / "markers.bed"
        export_markers_bed(test_markers, output_path)

        content = output_path.read_text()
        lines = content.strip().split("\n")[1:]  # Skip track line

        # Extract positions
        positions = []
        for line in lines:
            fields = line.split("\t")
            positions.append((fields[0], int(fields[1])))

        # Should be sorted
        assert positions == sorted(positions)


class TestExportMarkersVcf:
    """Tests for VCF export."""

    def test_basic_export(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test basic VCF export."""
        output_path = tmp_path / "markers.vcf"
        export_markers_vcf(test_markers, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Should have header lines and data
        header_lines = [l for l in lines if l.startswith("##")]
        assert len(header_lines) > 0

        # Should have column header
        col_header = [l for l in lines if l.startswith("#CHROM")]
        assert len(col_header) == 1

        # Should have 3 variant lines
        data_lines = [l for l in lines if not l.startswith("#")]
        assert len(data_lines) == 3

    def test_vcf_format(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test VCF format correctness."""
        output_path = tmp_path / "markers.vcf"
        export_markers_vcf(test_markers, output_path)

        content = output_path.read_text()
        lines = [l for l in content.strip().split("\n") if not l.startswith("#")]

        for line in lines:
            fields = line.split("\t")
            assert len(fields) == 8  # CHROM POS ID REF ALT QUAL FILTER INFO

            # Check POS is 1-based
            pos = int(fields[1])
            assert pos > 0

            # Check INFO contains expected fields
            info = fields[7]
            assert "CLASSIFICATION=" in info
            assert "CONFIDENCE=" in info


class TestExportMarkersTsv:
    """Tests for TSV export."""

    def test_basic_export(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test basic TSV export."""
        output_path = tmp_path / "markers.tsv"
        export_markers_tsv(test_markers, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Should have header + 3 markers
        assert len(lines) == 4

        # Check header
        header = lines[0].split("\t")
        assert "variant_id" in header
        assert "chrom" in header
        assert "classification" in header

    def test_with_frequencies(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test TSV export with frequency columns."""
        output_path = tmp_path / "markers.tsv"
        export_markers_tsv(test_markers, output_path, include_frequencies=True)

        content = output_path.read_text()
        header = content.split("\n")[0].split("\t")

        # Should have frequency columns for each founder
        assert "B73_ref_freq" in header
        assert "B73_alt_freq" in header
        assert "Mo17_ref_freq" in header

    def test_without_frequencies(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test TSV export without frequency columns."""
        output_path = tmp_path / "markers.tsv"
        export_markers_tsv(test_markers, output_path, include_frequencies=False)

        content = output_path.read_text()
        header = content.split("\n")[0].split("\t")

        # Should not have frequency columns
        assert "B73_ref_freq" not in header


class TestExportQualityReport:
    """Tests for quality report export."""

    def test_text_format(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test text format export."""
        assessment = MarkerQualityAssessment(test_markers)
        output_path = tmp_path / "report.txt"

        export_quality_report(assessment, output_path, format="txt")

        assert output_path.exists()
        content = output_path.read_text()
        assert "Total markers" in content

    def test_json_format(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test JSON format export."""
        import json

        assessment = MarkerQualityAssessment(test_markers)
        output_path = tmp_path / "report.json"

        export_quality_report(assessment, output_path, format="json")

        assert output_path.exists()
        content = output_path.read_text()

        # Should be valid JSON
        data = json.loads(content)
        assert "total_markers" in data
        assert data["total_markers"] == 3


class TestExportGapsBed:
    """Tests for gaps BED export."""

    def test_gaps_export(self, tmp_path: Path) -> None:
        """Test gaps BED export."""
        # Create markers with a gap
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id="chr1:1000:A:T",
                    chrom="chr1",
                    pos=1000,
                    ref="A",
                    alt="T",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                ),
                DiagnosticMarker(
                    variant_id="chr1:1000000:G:C",
                    chrom="chr1",
                    pos=1000000,
                    ref="G",
                    alt="C",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                ),
            ],
            founders=["B73", "Mo17"],
        )

        assessment = MarkerQualityAssessment(markers, gap_threshold=100000)
        output_path = tmp_path / "gaps.bed"

        export_gaps_bed(assessment, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Should have track line and at least one gap
        assert len(lines) >= 2


class TestExportDensityBedgraph:
    """Tests for density BedGraph export."""

    def test_density_export(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test density BedGraph export."""
        assessment = MarkerQualityAssessment(test_markers, window_size=1000000)
        output_path = tmp_path / "density.bedgraph"

        export_density_bedgraph(assessment, output_path, window_size=1000000)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Should have track line and density data
        assert lines[0].startswith("track")
        assert len(lines) > 1


class TestExportAllFormats:
    """Tests for multi-format export."""

    def test_export_all_formats(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test exporting all formats at once."""
        output_prefix = tmp_path / "markers"

        outputs = export_all_marker_formats(
            test_markers,
            output_prefix,
            formats=["bed", "tsv", "vcf"],
        )

        assert "bed" in outputs
        assert "tsv" in outputs
        assert "vcf" in outputs

        assert outputs["bed"].exists()
        assert outputs["tsv"].exists()
        assert outputs["vcf"].exists()

    def test_export_with_assessment(self, tmp_path: Path, test_markers: DiagnosticMarkerSet) -> None:
        """Test exporting with quality assessment."""
        assessment = MarkerQualityAssessment(test_markers)
        output_prefix = tmp_path / "markers"

        outputs = export_all_marker_formats(
            test_markers,
            output_prefix,
            formats=["bed", "summary"],
            assessment=assessment,
        )

        assert "bed" in outputs
        # Summary should be exported separately
