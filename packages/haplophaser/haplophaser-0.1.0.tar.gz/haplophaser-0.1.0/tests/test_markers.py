"""Tests for diagnostic marker identification."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.frequencies import (
    AlleleFrequencies,
    AlleleFrequency,
    AlleleFrequencyCalculator,
    VariantAlleleFrequencies,
)
from haplophaser.core.models import Population, PopulationRole, Sample
from haplophaser.io.populations import load_populations
from haplophaser.io.vcf import load_vcf
from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerFinder,
    DiagnosticMarkerSet,
    MarkerClassification,
    find_diagnostic_markers,
)
from haplophaser.markers.multifounder import (
    MultiFounderMarkerFinder,
    MultiFounderStrategy,
    find_pairwise_markers,
)
from haplophaser.markers.quality import (
    MarkerQualityAssessment,
    assess_marker_quality,
)


@pytest.fixture
def founders_vcf_path() -> Path:
    """Path to founders test VCF."""
    return Path(__file__).parent / "fixtures" / "founders_diagnostic.vcf"


@pytest.fixture
def founders_pop_path() -> Path:
    """Path to founders population file."""
    return Path(__file__).parent / "fixtures" / "founders_3way.tsv"


@pytest.fixture
def founder_populations() -> list[Population]:
    """Create test founder populations."""
    return [
        Population(
            name="B73",
            role=PopulationRole.FOUNDER,
            samples=[
                Sample(name="B73_1", ploidy=2),
                Sample(name="B73_2", ploidy=2),
                Sample(name="B73_3", ploidy=2),
            ],
        ),
        Population(
            name="Mo17",
            role=PopulationRole.FOUNDER,
            samples=[
                Sample(name="Mo17_1", ploidy=2),
                Sample(name="Mo17_2", ploidy=2),
                Sample(name="Mo17_3", ploidy=2),
            ],
        ),
        Population(
            name="W22",
            role=PopulationRole.FOUNDER,
            samples=[
                Sample(name="W22_1", ploidy=2),
                Sample(name="W22_2", ploidy=2),
                Sample(name="W22_3", ploidy=2),
            ],
        ),
    ]


@pytest.fixture
def test_frequencies() -> AlleleFrequencies:
    """Create test allele frequencies."""
    freqs = AlleleFrequencies(populations=["B73", "Mo17", "W22"])

    # Fully diagnostic marker: B73=A, Mo17=T
    freqs.add(VariantAlleleFrequencies(
        variant_id="chr1:1000:A:T",
        chrom="chr1",
        pos=1000,
        ref="A",
        alt=["T"],
        population_frequencies={
            "B73": AlleleFrequency(
                population="B73",
                frequencies={"A": 1.0, "T": 0.0},
                allele_counts={"A": 6},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
            "Mo17": AlleleFrequency(
                population="Mo17",
                frequencies={"A": 0.0, "T": 1.0},
                allele_counts={"T": 6},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
            "W22": AlleleFrequency(
                population="W22",
                frequencies={"A": 0.5, "T": 0.5},
                allele_counts={"A": 3, "T": 3},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
        },
    ))

    # Partially diagnostic marker
    freqs.add(VariantAlleleFrequencies(
        variant_id="chr1:2000:G:C",
        chrom="chr1",
        pos=2000,
        ref="G",
        alt=["C"],
        population_frequencies={
            "B73": AlleleFrequency(
                population="B73",
                frequencies={"G": 0.85, "C": 0.15},
                allele_counts={"G": 5, "C": 1},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
            "Mo17": AlleleFrequency(
                population="Mo17",
                frequencies={"G": 0.15, "C": 0.85},
                allele_counts={"G": 1, "C": 5},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
            "W22": AlleleFrequency(
                population="W22",
                frequencies={"G": 0.5, "C": 0.5},
                allele_counts={"G": 3, "C": 3},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
        },
    ))

    # Non-informative marker
    freqs.add(VariantAlleleFrequencies(
        variant_id="chr1:3000:T:C",
        chrom="chr1",
        pos=3000,
        ref="T",
        alt=["C"],
        population_frequencies={
            "B73": AlleleFrequency(
                population="B73",
                frequencies={"T": 0.5, "C": 0.5},
                allele_counts={"T": 3, "C": 3},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
            "Mo17": AlleleFrequency(
                population="Mo17",
                frequencies={"T": 0.5, "C": 0.5},
                allele_counts={"T": 3, "C": 3},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
            "W22": AlleleFrequency(
                population="W22",
                frequencies={"T": 0.5, "C": 0.5},
                allele_counts={"T": 3, "C": 3},
                total_alleles=6,
                n_samples=3,
                n_missing=0,
            ),
        },
    ))

    return freqs


class TestDiagnosticMarker:
    """Tests for DiagnosticMarker dataclass."""

    def test_basic_properties(self) -> None:
        """Test basic marker properties."""
        marker = DiagnosticMarker(
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
        )

        assert marker.pos_1based == 1001
        assert marker.is_fully_diagnostic
        assert marker.is_informative
        assert marker.get_founder_allele("B73") == "A"
        assert marker.get_founder_allele("Mo17") == "T"

    def test_to_bed_fields(self) -> None:
        """Test BED format conversion."""
        marker = DiagnosticMarker(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            founder_alleles={"B73": "A", "Mo17": "T"},
            founder_frequencies={},
            confidence=0.95,
            classification=MarkerClassification.FULLY_DIAGNOSTIC,
        )

        fields = marker.to_bed_fields()

        assert fields[0] == "chr1"
        assert fields[1] == 1000
        assert fields[2] == 1001
        assert "fully_diagnostic" in fields[3]
        assert fields[4] == 950  # 0.95 * 1000


class TestDiagnosticMarkerSet:
    """Tests for DiagnosticMarkerSet."""

    def test_filter_by_classification(self) -> None:
        """Test filtering markers by classification."""
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
                    variant_id="chr1:2000:G:C",
                    chrom="chr1",
                    pos=2000,
                    ref="G",
                    alt="C",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.85,
                    classification=MarkerClassification.PARTIALLY_DIAGNOSTIC,
                ),
            ],
            founders=["B73", "Mo17"],
        )

        assert len(markers) == 2
        assert len(markers.fully_diagnostic) == 1
        assert len(markers.partially_diagnostic) == 1

    def test_density_by_window(self) -> None:
        """Test marker density calculation."""
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id=f"chr1:{pos}:A:T",
                    chrom="chr1",
                    pos=pos,
                    ref="A",
                    alt="T",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                )
                for pos in [100, 200, 300, 1500000, 1600000]
            ],
            founders=["B73", "Mo17"],
        )

        density = markers.density_by_window(window_size=1_000_000)

        # Should have windows at 0-1M (3 markers) and 1M-2M (2 markers)
        assert len(density) >= 2


class TestDiagnosticMarkerFinder:
    """Tests for DiagnosticMarkerFinder."""

    def test_find_fully_diagnostic_markers(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test finding fully diagnostic markers."""
        finder = DiagnosticMarkerFinder(
            min_freq_diff=0.7,
            max_minor_freq=0.1,
            min_samples=2,
        )

        result = finder.find(test_frequencies, founders=["B73", "Mo17"])

        # Should find at least the fully diagnostic marker
        assert len(result) >= 1

        fully_diag = result.fully_diagnostic
        assert len(fully_diag) >= 1
        assert any(m.variant_id == "chr1:1000:A:T" for m in fully_diag)

    def test_find_partial_markers(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test finding partially diagnostic markers."""
        finder = DiagnosticMarkerFinder(
            min_freq_diff=0.5,  # Lower threshold
            max_minor_freq=0.2,
            min_samples=2,
            allow_partial=True,
        )

        result = finder.find(test_frequencies, founders=["B73", "Mo17"])

        # Should include partial markers
        assert len(result) >= 1

    def test_exclude_non_informative(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test that non-informative markers are excluded."""
        finder = DiagnosticMarkerFinder(
            min_freq_diff=0.7,
            min_samples=2,
        )

        result = finder.find(test_frequencies, founders=["B73", "Mo17"])

        # Non-informative marker should not be included
        non_info = [
            m for m in result
            if m.classification == MarkerClassification.NON_INFORMATIVE
        ]
        assert len(non_info) == 0

    def test_find_with_vcf(
        self,
        founders_vcf_path: Path,
        founders_pop_path: Path,
    ) -> None:
        """Test finding markers from VCF file."""
        variants = load_vcf(founders_vcf_path)
        populations = load_populations(founders_pop_path)

        calc = AlleleFrequencyCalculator(min_samples=2)
        frequencies = calc.calculate(variants, populations)

        finder = DiagnosticMarkerFinder(
            min_freq_diff=0.7,
            min_samples=2,
        )

        # Filter to just two founders for pairwise comparison
        founders = ["B73", "Mo17"]
        result = finder.find(frequencies, founders=founders)

        assert len(result) > 0
        assert all(m.is_informative for m in result)


class TestMultiFounderMarkerFinder:
    """Tests for MultiFounderMarkerFinder."""

    def test_pairwise_strategy(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test pairwise marker finding."""
        finder = MultiFounderMarkerFinder(
            founders=["B73", "Mo17", "W22"],
            strategy=MultiFounderStrategy.PAIRWISE,
            min_freq_diff=0.7,
        )

        result = finder.find(test_frequencies)

        # Should find pairwise markers
        assert result.n_pairwise > 0

        # Check coverage
        coverage = result.pairwise_coverage()
        assert ("B73", "Mo17") in coverage or ("Mo17", "B73") in coverage

    def test_unique_strategy(
        self,
        founder_populations: list[Population],
    ) -> None:
        """Test unique marker finding."""
        # Create frequencies where W22 has a unique allele
        freqs = AlleleFrequencies(populations=["B73", "Mo17", "W22"])

        freqs.add(VariantAlleleFrequencies(
            variant_id="chr1:4000:C:G",
            chrom="chr1",
            pos=4000,
            ref="C",
            alt=["G"],
            population_frequencies={
                "B73": AlleleFrequency(
                    population="B73",
                    frequencies={"C": 1.0, "G": 0.0},
                    allele_counts={"C": 6},
                    total_alleles=6,
                    n_samples=3,
                    n_missing=0,
                ),
                "Mo17": AlleleFrequency(
                    population="Mo17",
                    frequencies={"C": 1.0, "G": 0.0},
                    allele_counts={"C": 6},
                    total_alleles=6,
                    n_samples=3,
                    n_missing=0,
                ),
                "W22": AlleleFrequency(
                    population="W22",
                    frequencies={"C": 0.0, "G": 1.0},
                    allele_counts={"G": 6},
                    total_alleles=6,
                    n_samples=3,
                    n_missing=0,
                ),
            },
        ))

        finder = MultiFounderMarkerFinder(
            founders=["B73", "Mo17", "W22"],
            strategy=MultiFounderStrategy.UNIQUE,
            unique_min_diff=0.7,
        )

        result = finder.find(freqs)

        # Should find unique marker for W22
        assert result.n_unique > 0
        w22_markers = result.get_unique_markers("W22")
        assert len(w22_markers) > 0

    def test_get_all_diagnostic_markers(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test converting multi-founder results to DiagnosticMarkerSet."""
        finder = MultiFounderMarkerFinder(
            founders=["B73", "Mo17", "W22"],
            strategy=MultiFounderStrategy.ALL,
            min_freq_diff=0.7,
        )

        result = finder.find(test_frequencies)
        marker_set = result.get_all_diagnostic_markers()

        assert isinstance(marker_set, DiagnosticMarkerSet)
        assert len(marker_set) >= 0


class TestMarkerQualityAssessment:
    """Tests for MarkerQualityAssessment."""

    def test_chromosome_summary(self) -> None:
        """Test chromosome summary statistics."""
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id=f"chr1:{pos}:A:T",
                    chrom="chr1",
                    pos=pos,
                    ref="A",
                    alt="T",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                    distinguishes=("B73", "Mo17"),
                )
                for pos in range(0, 1000000, 100000)
            ],
            founders=["B73", "Mo17"],
        )

        assessment = MarkerQualityAssessment(markers)

        summary = assessment.chromosome_summary("chr1")
        assert summary is not None
        assert summary.n_markers == 10
        assert summary.n_fully_diagnostic == 10

    def test_find_gaps(self) -> None:
        """Test gap detection."""
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id=f"chr1:{pos}:A:T",
                    chrom="chr1",
                    pos=pos,
                    ref="A",
                    alt="T",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                )
                for pos in [0, 100000, 1000000]  # Gap between 100k and 1M
            ],
            founders=["B73", "Mo17"],
        )

        assessment = MarkerQualityAssessment(markers, gap_threshold=500000)

        gaps = assessment.find_gaps()
        assert len(gaps) >= 1

        # Find the large gap
        large_gaps = [g for g in gaps if g.length >= 500000]
        assert len(large_gaps) >= 1

    def test_density_by_window(self) -> None:
        """Test density calculation."""
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id=f"chr1:{pos}:A:T",
                    chrom="chr1",
                    pos=pos,
                    ref="A",
                    alt="T",
                    founder_alleles={},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                )
                for pos in range(0, 100000, 10000)
            ],
            founders=["B73", "Mo17"],
        )

        assessment = MarkerQualityAssessment(markers, window_size=50000)

        density = assessment.density_by_window()
        assert len(density) >= 2

        # First window should have markers
        assert density[0].total_markers > 0

    def test_founder_pair_coverage(self) -> None:
        """Test founder pair coverage calculation."""
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id=f"chr1:{pos}:A:T",
                    chrom="chr1",
                    pos=pos,
                    ref="A",
                    alt="T",
                    founder_alleles={"B73": "A", "Mo17": "T"},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                    distinguishes=("B73", "Mo17"),
                )
                for pos in range(0, 50000, 10000)
            ],
            founders=["B73", "Mo17"],
        )

        assessment = MarkerQualityAssessment(markers)

        coverage = assessment.founder_pair_coverage()
        assert len(coverage) >= 1

        # Check B73 vs Mo17 coverage
        b73_mo17 = [c for c in coverage if "B73" in c.pair and "Mo17" in c.pair]
        assert len(b73_mo17) == 1
        assert b73_mo17[0].n_markers == 5

    def test_summary_report(self) -> None:
        """Test summary report generation."""
        markers = DiagnosticMarkerSet(
            markers=[
                DiagnosticMarker(
                    variant_id="chr1:1000:A:T",
                    chrom="chr1",
                    pos=1000,
                    ref="A",
                    alt="T",
                    founder_alleles={"B73": "A", "Mo17": "T"},
                    founder_frequencies={},
                    confidence=0.95,
                    classification=MarkerClassification.FULLY_DIAGNOSTIC,
                    distinguishes=("B73", "Mo17"),
                ),
            ],
            founders=["B73", "Mo17"],
        )

        assessment = MarkerQualityAssessment(markers)
        summary = assessment.summary()

        assert "Total markers" in summary
        assert "Fully diagnostic" in summary
        assert "B73" in summary or "Mo17" in summary


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_find_diagnostic_markers(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test find_diagnostic_markers convenience function."""
        result = find_diagnostic_markers(
            test_frequencies,
            founders=["B73", "Mo17"],
            min_freq_diff=0.7,
        )

        assert isinstance(result, DiagnosticMarkerSet)
        assert len(result) > 0

    def test_find_pairwise_markers(
        self,
        test_frequencies: AlleleFrequencies,
    ) -> None:
        """Test find_pairwise_markers convenience function."""
        result = find_pairwise_markers(
            test_frequencies,
            founders=["B73", "Mo17", "W22"],
            min_freq_diff=0.7,
        )

        assert result.n_pairwise > 0

    def test_assess_marker_quality(self) -> None:
        """Test assess_marker_quality convenience function."""
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
            ],
            founders=["B73", "Mo17"],
        )

        assessment = assess_marker_quality(markers)

        assert isinstance(assessment, MarkerQualityAssessment)
        assert assessment.total_markers == 1
