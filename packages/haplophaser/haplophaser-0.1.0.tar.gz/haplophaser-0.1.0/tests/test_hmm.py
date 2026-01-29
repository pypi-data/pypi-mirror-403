"""Tests for HMM-based haplotype inference."""

from __future__ import annotations

import numpy as np
import pytest

from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerSet,
    MarkerClassification,
)
from haplophaser.proportion.genotypes import (
    MarkerGenotype,
    SampleMarkerGenotypes,
)
from haplophaser.proportion.hmm import (
    HaplotypeHMM,
    HMMResult,
    HMMResults,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def two_founder_markers() -> DiagnosticMarkerSet:
    """Create markers for two-founder system."""
    markers = []
    for i in range(10):
        markers.append(
            DiagnosticMarker(
                variant_id=f"chr1:{i*1000}:A:T",
                chrom="chr1",
                pos=i * 1000,
                ref="A",
                alt="T",
                founder_alleles={"A": "A", "B": "T"},
                founder_frequencies={
                    "A": {"A": 1.0, "T": 0.0},
                    "B": {"A": 0.0, "T": 1.0},
                },
                confidence=0.95,
                classification=MarkerClassification.FULLY_DIAGNOSTIC,
            )
        )
    return DiagnosticMarkerSet(markers=markers, founders=["A", "B"])


@pytest.fixture
def three_founder_markers() -> DiagnosticMarkerSet:
    """Create markers for three-founder system."""
    markers = []
    for i in range(15):
        markers.append(
            DiagnosticMarker(
                variant_id=f"chr1:{i*1000}:A:T",
                chrom="chr1",
                pos=i * 1000,
                ref="A",
                alt="T",
                founder_alleles={"A": "A", "B": "T", "C": "A"},
                founder_frequencies={
                    "A": {"A": 1.0, "T": 0.0},
                    "B": {"A": 0.0, "T": 1.0},
                    "C": {"A": 0.8, "T": 0.2},
                },
                confidence=0.90,
                classification=MarkerClassification.PARTIALLY_DIAGNOSTIC,
            )
        )
    return DiagnosticMarkerSet(markers=markers, founders=["A", "B", "C"])


@pytest.fixture
def pure_a_genotypes() -> SampleMarkerGenotypes:
    """Create genotypes that are pure founder A."""
    genos = SampleMarkerGenotypes(
        sample_name="Sample_A",
        founders=["A", "B"],
    )
    for i in range(10):
        genos.add_genotype(
            MarkerGenotype(
                variant_id=f"chr1:{i*1000}:A:T",
                chrom="chr1",
                pos=i * 1000,
                ref="A",
                alt="T",
                genotype=[0, 0],
                allele_dosage={"A": 2},
            )
        )
    return genos


@pytest.fixture
def pure_b_genotypes() -> SampleMarkerGenotypes:
    """Create genotypes that are pure founder B."""
    genos = SampleMarkerGenotypes(
        sample_name="Sample_B",
        founders=["A", "B"],
    )
    for i in range(10):
        genos.add_genotype(
            MarkerGenotype(
                variant_id=f"chr1:{i*1000}:A:T",
                chrom="chr1",
                pos=i * 1000,
                ref="A",
                alt="T",
                genotype=[1, 1],
                allele_dosage={"T": 2},
            )
        )
    return genos


@pytest.fixture
def recombinant_genotypes() -> SampleMarkerGenotypes:
    """Create genotypes with a recombination event."""
    genos = SampleMarkerGenotypes(
        sample_name="Sample_Recomb",
        founders=["A", "B"],
    )
    # First half: founder A
    for i in range(5):
        genos.add_genotype(
            MarkerGenotype(
                variant_id=f"chr1:{i*1000}:A:T",
                chrom="chr1",
                pos=i * 1000,
                ref="A",
                alt="T",
                genotype=[0, 0],
                allele_dosage={"A": 2},
            )
        )
    # Second half: founder B
    for i in range(5, 10):
        genos.add_genotype(
            MarkerGenotype(
                variant_id=f"chr1:{i*1000}:A:T",
                chrom="chr1",
                pos=i * 1000,
                ref="A",
                alt="T",
                genotype=[1, 1],
                allele_dosage={"T": 2},
            )
        )
    return genos


# ============================================================================
# Test HaplotypeHMM initialization
# ============================================================================


class TestHaplotypeHMMInit:
    """Tests for HaplotypeHMM initialization."""

    def test_diploid_states(self) -> None:
        """Test state generation for diploid."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        # For 2 founders, diploid: AA, AB, BB = 3 states
        assert len(hmm.states) == 3
        assert "A/A" in hmm.states
        assert "A/B" in hmm.states
        assert "B/B" in hmm.states

    def test_three_founder_states(self) -> None:
        """Test state generation for three founders."""
        hmm = HaplotypeHMM(founders=["A", "B", "C"], ploidy=2)

        # For 3 founders, diploid: AA, AB, AC, BB, BC, CC = 6 states
        assert len(hmm.states) == 6

    def test_transition_matrix_shape(self) -> None:
        """Test transition matrix has correct shape."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        n_states = len(hmm.states)
        assert hmm._transition_matrix.shape == (n_states, n_states)

    def test_transition_matrix_rows_sum_to_one(self) -> None:
        """Test transition matrix rows sum to 1."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        row_sums = hmm._transition_matrix.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, np.ones(len(hmm.states)))


# ============================================================================
# Test HMM inference
# ============================================================================


class TestHaplotypeHMMInference:
    """Tests for HMM inference."""

    def test_pure_founder_a(
        self,
        two_founder_markers: DiagnosticMarkerSet,
        pure_a_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test inference with pure founder A sample."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        results = hmm.fit_predict(
            {"Sample_A": pure_a_genotypes},
            two_founder_markers,
        )

        assert results.n_samples == 1
        result = results.get_result("Sample_A", "chr1")
        assert result is not None

        # Viterbi path should be all A/A
        assert result.viterbi_path is not None
        # Should be mostly state A/A (viterbi_path is list[str])
        from collections import Counter
        state_counts = Counter(result.viterbi_path)
        most_common_state = state_counts.most_common(1)[0][0]
        assert most_common_state == "A/A"

    def test_pure_founder_b(
        self,
        two_founder_markers: DiagnosticMarkerSet,
        pure_b_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test inference with pure founder B sample."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        results = hmm.fit_predict(
            {"Sample_B": pure_b_genotypes},
            two_founder_markers,
        )

        result = results.get_result("Sample_B", "chr1")
        assert result is not None

        # Viterbi path should be all B/B (viterbi_path is list[str])
        from collections import Counter
        state_counts = Counter(result.viterbi_path)
        most_common_state = state_counts.most_common(1)[0][0]
        assert most_common_state == "B/B"

    def test_recombinant(
        self,
        two_founder_markers: DiagnosticMarkerSet,
        recombinant_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test inference with recombinant sample."""
        hmm = HaplotypeHMM(
            founders=["A", "B"],
            ploidy=2,
            recombination_rate=1e-4,  # Higher rate to detect recombination
        )

        results = hmm.fit_predict(
            {"Sample_Recomb": recombinant_genotypes},
            two_founder_markers,
        )

        result = results.get_result("Sample_Recomb", "chr1")
        assert result is not None

        # Should detect transition from A/A to B/B (viterbi_path is list[str])
        viterbi = result.viterbi_path
        # Check that we see both states
        unique_states = set(viterbi)
        assert len(unique_states) >= 2

    def test_smoothed_proportions(
        self,
        two_founder_markers: DiagnosticMarkerSet,
        pure_a_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test smoothed proportion output."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        results = hmm.fit_predict(
            {"Sample_A": pure_a_genotypes},
            two_founder_markers,
        )

        result = results.get_result("Sample_A", "chr1")
        assert result is not None

        # Smoothed proportions should favor A
        for props in result.smoothed_proportions:
            assert props.get("A", 0) > 0.5

    def test_posteriors(
        self,
        two_founder_markers: DiagnosticMarkerSet,
        pure_a_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test posterior probability output."""
        hmm = HaplotypeHMM(founders=["A", "B"], ploidy=2)

        results = hmm.fit_predict(
            {"Sample_A": pure_a_genotypes},
            two_founder_markers,
        )

        result = results.get_result("Sample_A", "chr1")
        assert result is not None

        # Posteriors should sum to 1 at each position
        row_sums = result.posteriors.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, np.ones(len(result.positions)))

    def test_baum_welch(
        self,
        two_founder_markers: DiagnosticMarkerSet,
        pure_a_genotypes: SampleMarkerGenotypes,
        pure_b_genotypes: SampleMarkerGenotypes,
    ) -> None:
        """Test Baum-Welch parameter estimation."""
        hmm = HaplotypeHMM(
            founders=["A", "B"],
            ploidy=2,
            recombination_rate=1e-8,
        )

        # Run Baum-Welch with multiple samples
        result = hmm.baum_welch(
            {"Sample_A": pure_a_genotypes, "Sample_B": pure_b_genotypes},
            two_founder_markers,
            max_iterations=10,
        )

        # Check result structure
        assert "recombination_rate" in result
        assert "genotyping_error" in result
        assert "log_likelihoods" in result
        assert "converged" in result
        assert "n_iterations" in result

        # Check that log-likelihoods are recorded
        assert len(result["log_likelihoods"]) > 0

        # Check that parameters are reasonable
        assert result["recombination_rate"] > 0
        assert result["n_iterations"] > 0


# ============================================================================
# Test HMMResults
# ============================================================================


class TestHMMResults:
    """Tests for HMMResults container."""

    def test_add_result(self) -> None:
        """Test adding results."""
        results = HMMResults(
            founders=["A", "B"],
            states=["A/A", "A/B", "B/B"],
        )

        result = HMMResult(
            sample="Sample1",
            chrom="chr1",
            markers=["m1", "m2", "m3"],
            positions=[1000, 2000, 3000],
            posteriors=np.ones((3, 3)) / 3,
            viterbi_path=["A/A", "A/A", "A/B"],
            smoothed_proportions=[
                {"A": 0.9, "B": 0.1},
                {"A": 0.8, "B": 0.2},
                {"A": 0.5, "B": 0.5},
            ],
            states=["A/A", "A/B", "B/B"],
        )

        results.add_result(result)

        assert results.n_samples == 1
        assert results.n_results == 1
        assert "Sample1" in results.samples

    def test_get_result(self) -> None:
        """Test retrieving results."""
        results = HMMResults(
            founders=["A", "B"],
            states=["A/A", "A/B", "B/B"],
        )

        result = HMMResult(
            sample="Sample1",
            chrom="chr1",
            markers=["m1", "m2", "m3"],
            positions=[1000, 2000, 3000],
            posteriors=np.ones((3, 3)) / 3,
            viterbi_path=["A/A", "A/A", "A/B"],
            smoothed_proportions=[
                {"A": 0.9, "B": 0.1},
                {"A": 0.8, "B": 0.2},
                {"A": 0.5, "B": 0.5},
            ],
            states=["A/A", "A/B", "B/B"],
        )

        results.add_result(result)

        retrieved = results.get_result("Sample1", "chr1")
        assert retrieved is not None
        assert retrieved.sample == "Sample1"

        missing = results.get_result("Missing", "chr1")
        assert missing is None


# ============================================================================
# Test HMMResult methods
# ============================================================================


class TestHMMResult:
    """Tests for HMMResult class."""

    def test_get_posterior_at(self) -> None:
        """Test getting posterior at position."""
        result = HMMResult(
            sample="Sample1",
            chrom="chr1",
            markers=["m1", "m2", "m3"],
            positions=[1000, 2000, 3000],
            posteriors=np.array([
                [0.9, 0.1, 0.0],
                [0.5, 0.3, 0.2],
                [0.1, 0.2, 0.7],
            ]),
            viterbi_path=["A/A", "A/A", "B/B"],
            smoothed_proportions=[
                {"A": 0.9, "B": 0.1},
                {"A": 0.6, "B": 0.4},
                {"A": 0.2, "B": 0.8},
            ],
            states=["A/A", "A/B", "B/B"],
            founders=["A", "B"],
        )

        # Exact position (returns smoothed proportions)
        post = result.get_posterior_at(2000)
        assert post is not None
        assert post["A"] == pytest.approx(0.6, abs=0.1)

        # Interpolated position
        post = result.get_posterior_at(1500)
        assert post is not None
        assert "A" in post
        assert "B" in post

    def test_viterbi_segments(self) -> None:
        """Test Viterbi path segmentation."""
        result = HMMResult(
            sample="Sample1",
            chrom="chr1",
            markers=["m1", "m2", "m3", "m4", "m5"],
            positions=[1000, 2000, 3000, 4000, 5000],
            posteriors=np.ones((5, 3)) / 3,
            viterbi_path=["A/A", "A/A", "A/B", "A/B", "B/B"],
            smoothed_proportions=[{"A": 0.5, "B": 0.5}] * 5,
            states=["A/A", "A/B", "B/B"],
            founders=["A", "B"],
        )

        segments = result.get_viterbi_segments()

        # Should have 3 segments
        assert len(segments) == 3
        assert segments[0]["state"] == "A/A"
        assert segments[1]["state"] == "A/B"
        assert segments[2]["state"] == "B/B"
