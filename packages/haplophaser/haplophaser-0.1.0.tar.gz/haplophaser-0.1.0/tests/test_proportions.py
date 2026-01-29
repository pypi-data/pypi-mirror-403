"""Tests for haplotype proportion estimation."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerSet,
    MarkerClassification,
)
from haplophaser.proportion.blocks import (
    BlockResults,
    HaplotypeBlock,
    HaplotypeBlockCaller,
    SampleBlocks,
)
from haplophaser.proportion.breakpoints import (
    Breakpoint,
    BreakpointFinder,
    BreakpointResults,
    SampleBreakpoints,
)
from haplophaser.proportion.genotypes import (
    MarkerGenotype,
    SampleMarkerGenotypes,
)
from haplophaser.proportion.results import (
    ProportionResults,
    SampleProportions,
    WindowProportion,
)
from haplophaser.proportion.windows import (
    WindowProportionEstimator,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def test_markers() -> DiagnosticMarkerSet:
    """Create test markers for proportion estimation."""
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
            ),
            DiagnosticMarker(
                variant_id="chr1:5000:G:C",
                chrom="chr1",
                pos=5000,
                ref="G",
                alt="C",
                founder_alleles={"B73": "G", "Mo17": "C"},
                founder_frequencies={
                    "B73": {"G": 1.0, "C": 0.0},
                    "Mo17": {"G": 0.0, "C": 1.0},
                },
                confidence=0.92,
                classification=MarkerClassification.FULLY_DIAGNOSTIC,
            ),
            DiagnosticMarker(
                variant_id="chr1:10000:T:A",
                chrom="chr1",
                pos=10000,
                ref="T",
                alt="A",
                founder_alleles={"B73": "T", "Mo17": "A"},
                founder_frequencies={
                    "B73": {"T": 1.0, "A": 0.0},
                    "Mo17": {"T": 0.0, "A": 1.0},
                },
                confidence=0.90,
                classification=MarkerClassification.FULLY_DIAGNOSTIC,
            ),
            DiagnosticMarker(
                variant_id="chr2:2000:C:G",
                chrom="chr2",
                pos=2000,
                ref="C",
                alt="G",
                founder_alleles={"B73": "C", "Mo17": "G"},
                founder_frequencies={
                    "B73": {"C": 1.0, "G": 0.0},
                    "Mo17": {"C": 0.0, "G": 1.0},
                },
                confidence=0.93,
                classification=MarkerClassification.FULLY_DIAGNOSTIC,
            ),
        ],
        founders=["B73", "Mo17"],
    )


@pytest.fixture
def b73_like_genotypes() -> SampleMarkerGenotypes:
    """Create genotypes that look like B73."""
    genos = SampleMarkerGenotypes(
        sample_name="RIL_1",
        founders=["B73", "Mo17"],
    )
    # All homozygous for B73 alleles
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[0, 0],
            allele_dosage={"A": 2},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:5000:G:C",
            chrom="chr1",
            pos=5000,
            ref="G",
            alt="C",
            genotype=[0, 0],
            allele_dosage={"G": 2},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:10000:T:A",
            chrom="chr1",
            pos=10000,
            ref="T",
            alt="A",
            genotype=[0, 0],
            allele_dosage={"T": 2},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr2:2000:C:G",
            chrom="chr2",
            pos=2000,
            ref="C",
            alt="G",
            genotype=[0, 0],
            allele_dosage={"C": 2},
        )
    )
    return genos


@pytest.fixture
def mo17_like_genotypes() -> SampleMarkerGenotypes:
    """Create genotypes that look like Mo17."""
    genos = SampleMarkerGenotypes(
        sample_name="RIL_2",
        founders=["B73", "Mo17"],
    )
    # All homozygous for Mo17 alleles
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[1, 1],
            allele_dosage={"T": 2},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:5000:G:C",
            chrom="chr1",
            pos=5000,
            ref="G",
            alt="C",
            genotype=[1, 1],
            allele_dosage={"C": 2},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:10000:T:A",
            chrom="chr1",
            pos=10000,
            ref="T",
            alt="A",
            genotype=[1, 1],
            allele_dosage={"A": 2},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr2:2000:C:G",
            chrom="chr2",
            pos=2000,
            ref="C",
            alt="G",
            genotype=[1, 1],
            allele_dosage={"G": 2},
        )
    )
    return genos


@pytest.fixture
def het_genotypes() -> SampleMarkerGenotypes:
    """Create heterozygous genotypes (F1-like)."""
    genos = SampleMarkerGenotypes(
        sample_name="F1",
        founders=["B73", "Mo17"],
    )
    # All heterozygous
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[0, 1],
            allele_dosage={"A": 1, "T": 1},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:5000:G:C",
            chrom="chr1",
            pos=5000,
            ref="G",
            alt="C",
            genotype=[0, 1],
            allele_dosage={"G": 1, "C": 1},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr1:10000:T:A",
            chrom="chr1",
            pos=10000,
            ref="T",
            alt="A",
            genotype=[0, 1],
            allele_dosage={"T": 1, "A": 1},
        )
    )
    genos.add_genotype(
        MarkerGenotype(
            variant_id="chr2:2000:C:G",
            chrom="chr2",
            pos=2000,
            ref="C",
            alt="G",
            genotype=[0, 1],
            allele_dosage={"C": 1, "G": 1},
        )
    )
    return genos


# ============================================================================
# Test MarkerGenotype
# ============================================================================


class TestMarkerGenotype:
    """Tests for MarkerGenotype dataclass."""

    def test_homozygous_ref(self) -> None:
        """Test homozygous reference genotype."""
        geno = MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[0, 0],
            allele_dosage={"A": 2},
        )

        assert geno.is_homozygous
        assert not geno.is_heterozygous
        assert geno.alleles == ["A", "A"]
        assert geno.get_allele_frequency("A") == 1.0
        assert geno.get_allele_frequency("T") == 0.0

    def test_homozygous_alt(self) -> None:
        """Test homozygous alternate genotype."""
        geno = MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[1, 1],
            allele_dosage={"T": 2},
        )

        assert geno.is_homozygous
        assert not geno.is_heterozygous
        assert geno.alleles == ["T", "T"]
        assert geno.get_allele_frequency("A") == 0.0
        assert geno.get_allele_frequency("T") == 1.0

    def test_heterozygous(self) -> None:
        """Test heterozygous genotype."""
        geno = MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[0, 1],
            allele_dosage={"A": 1, "T": 1},
        )

        assert not geno.is_homozygous
        assert geno.is_heterozygous
        assert set(geno.alleles) == {"A", "T"}
        assert geno.get_allele_frequency("A") == 0.5
        assert geno.get_allele_frequency("T") == 0.5

    def test_missing(self) -> None:
        """Test missing genotype."""
        geno = MarkerGenotype(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt="T",
            genotype=[-1, -1],
            is_missing=True,
        )

        assert geno.is_missing
        assert not geno.is_homozygous
        assert not geno.is_heterozygous
        assert geno.alleles == []


# ============================================================================
# Test SampleMarkerGenotypes
# ============================================================================


class TestSampleMarkerGenotypes:
    """Tests for SampleMarkerGenotypes dataclass."""

    def test_basic_operations(self, b73_like_genotypes: SampleMarkerGenotypes) -> None:
        """Test basic operations."""
        assert b73_like_genotypes.n_markers == 4
        assert b73_like_genotypes.n_missing == 0
        assert b73_like_genotypes.missing_rate == 0.0

    def test_get_genotype(self, b73_like_genotypes: SampleMarkerGenotypes) -> None:
        """Test getting specific genotype."""
        geno = b73_like_genotypes.get_genotype("chr1:1000:A:T")
        assert geno is not None
        assert geno.chrom == "chr1"
        assert geno.pos == 1000

    def test_chromosome_genotypes(self, b73_like_genotypes: SampleMarkerGenotypes) -> None:
        """Test getting chromosome-specific genotypes."""
        chr1_genos = b73_like_genotypes.get_chromosome_genotypes("chr1")
        assert len(chr1_genos) == 3

        # Should be sorted by position
        positions = [g.pos for g in chr1_genos]
        assert positions == sorted(positions)

    def test_get_chromosomes(self, b73_like_genotypes: SampleMarkerGenotypes) -> None:
        """Test getting list of chromosomes."""
        chroms = b73_like_genotypes.get_chromosomes()
        assert set(chroms) == {"chr1", "chr2"}


# ============================================================================
# Test WindowProportion
# ============================================================================


class TestWindowProportion:
    """Tests for WindowProportion dataclass."""

    def test_basic_properties(self) -> None:
        """Test basic window properties."""
        window = WindowProportion(
            chrom="chr1",
            start=0,
            end=10000,
            proportions={"B73": 0.7, "Mo17": 0.3},
            n_markers=5,
        )

        assert window.midpoint == 5000
        assert window.size == 10000
        assert window.founders == ["B73", "Mo17"]
        assert window.dominant_founder == "B73"
        assert not window.is_mixed

    def test_mixed_ancestry(self) -> None:
        """Test mixed ancestry detection."""
        window = WindowProportion(
            chrom="chr1",
            start=0,
            end=10000,
            proportions={"B73": 0.55, "Mo17": 0.45},
            n_markers=5,
        )

        assert window.is_mixed

    def test_confidence_intervals(self) -> None:
        """Test confidence interval handling."""
        window = WindowProportion(
            chrom="chr1",
            start=0,
            end=10000,
            proportions={"B73": 0.7, "Mo17": 0.3},
            confidence_intervals={"B73": (0.6, 0.8), "Mo17": (0.2, 0.4)},
        )

        ci = window.get_ci("B73")
        assert ci == (0.6, 0.8)


# ============================================================================
# Test SampleProportions
# ============================================================================


class TestSampleProportions:
    """Tests for SampleProportions dataclass."""

    def test_genome_wide_calculation(self) -> None:
        """Test genome-wide proportion calculation."""
        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 1.0, "Mo17": 0.0},
                    n_markers=10,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=10000,
                    end=20000,
                    proportions={"B73": 0.0, "Mo17": 1.0},
                    n_markers=10,
                ),
            ],
        )

        # With equal marker counts, should be 50/50
        assert sample.genome_wide["B73"] == pytest.approx(0.5)
        assert sample.genome_wide["Mo17"] == pytest.approx(0.5)

    def test_weighted_genome_wide(self) -> None:
        """Test weighted genome-wide calculation."""
        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 1.0, "Mo17": 0.0},
                    n_markers=30,  # More markers
                ),
                WindowProportion(
                    chrom="chr1",
                    start=10000,
                    end=20000,
                    proportions={"B73": 0.0, "Mo17": 1.0},
                    n_markers=10,
                ),
            ],
        )

        # Should be weighted by marker count: 30/(30+10) = 0.75 B73
        assert sample.genome_wide["B73"] == pytest.approx(0.75)
        assert sample.genome_wide["Mo17"] == pytest.approx(0.25)


# ============================================================================
# Test WindowProportionEstimator
# ============================================================================


class TestWindowProportionEstimator:
    """Tests for WindowProportionEstimator."""

    def test_frequency_method_pure_b73(
        self,
        test_markers: DiagnosticMarkerSet,
        b73_like_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test frequency method with pure B73 sample."""
        estimator = WindowProportionEstimator(
            window_size=100000,
            step_size=50000,
            min_markers=1,
            method="frequency",
        )

        results = estimator.estimate(
            {"RIL_1": b73_like_genotypes},
            test_markers,
        )

        assert results.n_samples == 1
        sample = results.get_sample("RIL_1")
        assert sample is not None

        # Should be predominantly B73
        assert sample.genome_wide["B73"] > 0.8
        assert sample.genome_wide["Mo17"] < 0.2

    def test_frequency_method_pure_mo17(
        self,
        test_markers: DiagnosticMarkerSet,
        mo17_like_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test frequency method with pure Mo17 sample."""
        estimator = WindowProportionEstimator(
            window_size=100000,
            min_markers=1,
            method="frequency",
        )

        results = estimator.estimate(
            {"RIL_2": mo17_like_genotypes},
            test_markers,
        )

        sample = results.get_sample("RIL_2")
        assert sample is not None

        # Should be predominantly Mo17
        assert sample.genome_wide["Mo17"] > 0.8
        assert sample.genome_wide["B73"] < 0.2

    def test_frequency_method_heterozygous(
        self,
        test_markers: DiagnosticMarkerSet,
        het_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test frequency method with heterozygous sample."""
        estimator = WindowProportionEstimator(
            window_size=100000,
            min_markers=1,
            method="frequency",
        )

        results = estimator.estimate(
            {"F1": het_genotypes},
            test_markers,
        )

        sample = results.get_sample("F1")
        assert sample is not None

        # Should be approximately 50/50
        assert sample.genome_wide["B73"] == pytest.approx(0.5, abs=0.1)
        assert sample.genome_wide["Mo17"] == pytest.approx(0.5, abs=0.1)

    def test_likelihood_method(
        self,
        test_markers: DiagnosticMarkerSet,
        b73_like_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test likelihood estimation method."""
        estimator = WindowProportionEstimator(
            window_size=100000,
            min_markers=1,
            method="likelihood",
        )

        results = estimator.estimate(
            {"RIL_1": b73_like_genotypes},
            test_markers,
        )

        sample = results.get_sample("RIL_1")
        assert sample is not None

        # Should still identify as predominantly B73
        assert sample.genome_wide["B73"] > 0.7

    def test_bayesian_method(
        self,
        test_markers: DiagnosticMarkerSet,
        b73_like_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test Bayesian estimation method."""
        estimator = WindowProportionEstimator(
            window_size=100000,
            min_markers=1,
            method="bayesian",
        )

        results = estimator.estimate(
            {"RIL_1": b73_like_genotypes},
            test_markers,
        )

        sample = results.get_sample("RIL_1")
        assert sample is not None

        # Should still identify as predominantly B73
        assert sample.genome_wide["B73"] > 0.7


# ============================================================================
# Test HaplotypeBlockCaller
# ============================================================================


class TestHaplotypeBlockCaller:
    """Tests for HaplotypeBlockCaller."""

    def test_call_single_block(self) -> None:
        """Test calling a single dominant block."""
        results = ProportionResults(
            founders=["B73", "Mo17"],
            method="frequency",
            window_size=10000,
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.9, "Mo17": 0.1},
                    n_markers=5,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=10000,
                    end=20000,
                    proportions={"B73": 0.85, "Mo17": 0.15},
                    n_markers=5,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=20000,
                    end=30000,
                    proportions={"B73": 0.88, "Mo17": 0.12},
                    n_markers=5,
                ),
            ],
        )
        results.add_sample(sample)

        caller = HaplotypeBlockCaller(min_proportion=0.7)
        blocks = caller.call_blocks(results)

        sample_blocks = blocks.get_sample("RIL_1")
        assert sample_blocks is not None
        assert sample_blocks.n_blocks == 1

        block = sample_blocks.blocks[0]
        assert block.dominant_founder == "B73"
        assert block.start == 0
        assert block.end == 30000
        assert block.n_windows == 3

    def test_call_multiple_blocks(self) -> None:
        """Test calling multiple blocks with founder transition."""
        results = ProportionResults(
            founders=["B73", "Mo17"],
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.9, "Mo17": 0.1},
                    n_markers=5,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=10000,
                    end=20000,
                    proportions={"B73": 0.2, "Mo17": 0.8},
                    n_markers=5,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=20000,
                    end=30000,
                    proportions={"B73": 0.15, "Mo17": 0.85},
                    n_markers=5,
                ),
            ],
        )
        results.add_sample(sample)

        caller = HaplotypeBlockCaller(min_proportion=0.7)
        blocks = caller.call_blocks(results)

        sample_blocks = blocks.get_sample("RIL_1")
        assert sample_blocks is not None
        assert sample_blocks.n_blocks == 2

        # First block should be B73
        assert sample_blocks.blocks[0].dominant_founder == "B73"
        # Second block should be Mo17
        assert sample_blocks.blocks[1].dominant_founder == "Mo17"


# ============================================================================
# Test BreakpointFinder
# ============================================================================


class TestBreakpointFinder:
    """Tests for BreakpointFinder."""

    def test_threshold_method(self) -> None:
        """Test threshold-based breakpoint detection."""
        results = ProportionResults(
            founders=["B73", "Mo17"],
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.9, "Mo17": 0.1},
                    n_markers=5,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=10000,
                    end=20000,
                    proportions={"B73": 0.1, "Mo17": 0.9},
                    n_markers=5,
                ),
            ],
        )
        results.add_sample(sample)

        finder = BreakpointFinder(method="threshold", min_change=0.3)
        bp_results = finder.find_breakpoints(results)

        sample_bps = bp_results.get_sample("RIL_1")
        assert sample_bps is not None
        assert sample_bps.n_breakpoints >= 1

        bp = sample_bps.breakpoints[0]
        assert bp.left_founder == "B73"
        assert bp.right_founder == "Mo17"

    def test_no_breakpoints(self) -> None:
        """Test when no breakpoints should be detected."""
        results = ProportionResults(
            founders=["B73", "Mo17"],
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.9, "Mo17": 0.1},
                    n_markers=5,
                ),
                WindowProportion(
                    chrom="chr1",
                    start=10000,
                    end=20000,
                    proportions={"B73": 0.88, "Mo17": 0.12},
                    n_markers=5,
                ),
            ],
        )
        results.add_sample(sample)

        finder = BreakpointFinder(method="threshold", min_change=0.5)
        bp_results = finder.find_breakpoints(results)

        sample_bps = bp_results.get_sample("RIL_1")
        assert sample_bps is not None
        assert sample_bps.n_breakpoints == 0


# ============================================================================
# Test ProportionResults serialization
# ============================================================================


class TestProportionResultsSerialization:
    """Tests for ProportionResults serialization."""

    def test_to_dict(self) -> None:
        """Test conversion to dict."""
        results = ProportionResults(
            founders=["B73", "Mo17"],
            method="frequency",
            window_size=10000,
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.7, "Mo17": 0.3},
                    n_markers=5,
                ),
            ],
        )
        results.add_sample(sample)

        data = results.to_dict()

        assert data["method"] == "frequency"
        assert data["window_size"] == 10000
        assert "RIL_1" in data["samples"]

    def test_from_dict(self) -> None:
        """Test reconstruction from dict."""
        data = {
            "method": "frequency",
            "window_size": 10000,
            "step_size": 5000,
            "min_markers": 1,
            "founders": ["B73", "Mo17"],
            "samples": {
                "RIL_1": {
                    "sample_name": "RIL_1",
                    "founders": ["B73", "Mo17"],
                    "genome_wide": {"B73": 0.7, "Mo17": 0.3},
                    "windows": [
                        {
                            "chrom": "chr1",
                            "start": 0,
                            "end": 10000,
                            "proportions": {"B73": 0.7, "Mo17": 0.3},
                            "n_markers": 5,
                            "method": "frequency",
                        }
                    ],
                }
            },
        }

        results = ProportionResults.from_dict(data)

        assert results.method == "frequency"
        assert results.n_samples == 1

        sample = results.get_sample("RIL_1")
        assert sample is not None
        assert sample.genome_wide["B73"] == 0.7


# ============================================================================
# Test proportion export functions
# ============================================================================


class TestProportionExport:
    """Tests for proportion export functions."""

    def test_export_proportions_tsv(self, tmp_path: Path) -> None:
        """Test TSV export."""
        from haplophaser.io.proportions import export_proportions_tsv

        results = ProportionResults(
            founders=["B73", "Mo17"],
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.7, "Mo17": 0.3},
                    n_markers=5,
                ),
            ],
        )
        results.add_sample(sample)

        output_path = tmp_path / "proportions.tsv"
        export_proportions_tsv(results, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 2  # Header + 1 window
        assert "B73_proportion" in lines[0]
        assert "Mo17_proportion" in lines[0]

    def test_export_genome_wide_tsv(self, tmp_path: Path) -> None:
        """Test genome-wide TSV export."""
        from haplophaser.io.proportions import export_genome_wide_tsv

        results = ProportionResults(
            founders=["B73", "Mo17"],
        )

        sample = SampleProportions(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            windows=[
                WindowProportion(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    proportions={"B73": 0.7, "Mo17": 0.3},
                    n_markers=5,
                ),
            ],
            genome_wide={"B73": 0.7, "Mo17": 0.3},
        )
        results.add_sample(sample)

        output_path = tmp_path / "genome_wide.tsv"
        export_genome_wide_tsv(results, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "RIL_1" in content
        assert "0.7" in content

    def test_export_blocks_bed(self, tmp_path: Path) -> None:
        """Test blocks BED export."""
        from haplophaser.io.proportions import export_blocks_bed

        blocks = BlockResults(
            founders=["B73", "Mo17"],
        )

        sample_blocks = SampleBlocks(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            blocks=[
                HaplotypeBlock(
                    chrom="chr1",
                    start=0,
                    end=10000,
                    dominant_founder="B73",
                    mean_proportion=0.85,
                    min_proportion=0.8,
                    max_proportion=0.9,
                    n_windows=3,
                ),
            ],
        )
        blocks.add_sample(sample_blocks)

        output_path = tmp_path / "blocks.bed"
        export_blocks_bed(blocks, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "chr1" in content
        assert "B73" in content

    def test_export_breakpoints_tsv(self, tmp_path: Path) -> None:
        """Test breakpoints TSV export."""
        from haplophaser.io.proportions import export_breakpoints_tsv

        bp_results = BreakpointResults(
            founders=["B73", "Mo17"],
        )

        sample_bps = SampleBreakpoints(
            sample_name="RIL_1",
            founders=["B73", "Mo17"],
            breakpoints=[
                Breakpoint(
                    chrom="chr1",
                    position=15000,
                    left_founder="B73",
                    right_founder="Mo17",
                    confidence=0.9,
                ),
            ],
        )
        bp_results.add_sample(sample_bps)

        output_path = tmp_path / "breakpoints.tsv"
        export_breakpoints_tsv(bp_results, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "RIL_1" in content
        assert "B73" in content
        assert "Mo17" in content
