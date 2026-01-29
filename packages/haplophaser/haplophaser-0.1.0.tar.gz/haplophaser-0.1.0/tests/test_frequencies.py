"""Tests for allele frequency calculation."""

from __future__ import annotations

import pytest

from haplophaser.core.frequencies import (
    AlleleFrequency,
    AlleleFrequencyCalculator,
    VariantAlleleFrequencies,
    calculate_population_frequencies,
    get_founder_frequencies,
)
from haplophaser.core.models import Population, PopulationRole, Sample, Variant


@pytest.fixture
def test_variant() -> Variant:
    """Create a test variant."""
    return Variant(
        chrom="chr1",
        pos=1000,
        ref="A",
        alt=["T"],
        genotypes={
            "B73_1": [0, 0],
            "B73_2": [0, 0],
            "B73_3": [0, 0],
            "Mo17_1": [1, 1],
            "Mo17_2": [1, 1],
            "Mo17_3": [1, 1],
        },
    )


@pytest.fixture
def test_populations() -> list[Population]:
    """Create test populations."""
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
    ]


class TestAlleleFrequency:
    """Tests for AlleleFrequency dataclass."""

    def test_basic_properties(self) -> None:
        """Test basic properties."""
        af = AlleleFrequency(
            population="B73",
            frequencies={"A": 0.8, "T": 0.2},
            allele_counts={"A": 4, "T": 1},
            total_alleles=5,
            n_samples=3,
            n_missing=0,
        )

        assert af.major_allele == "A"
        assert af.minor_allele == "T"
        assert af.maf == pytest.approx(0.2)
        assert not af.is_fixed

    def test_fixed_allele(self) -> None:
        """Test detection of fixed alleles."""
        af = AlleleFrequency(
            population="B73",
            frequencies={"A": 1.0, "T": 0.0},
            allele_counts={"A": 6, "T": 0},
            total_alleles=6,
            n_samples=3,
            n_missing=0,
        )

        assert af.is_fixed
        assert af.major_allele == "A"

    def test_get_frequency(self) -> None:
        """Test getting frequency of specific allele."""
        af = AlleleFrequency(
            population="B73",
            frequencies={"A": 0.7, "T": 0.3},
            allele_counts={"A": 7, "T": 3},
            total_alleles=10,
            n_samples=5,
            n_missing=0,
        )

        assert af.get_frequency("A") == pytest.approx(0.7)
        assert af.get_frequency("T") == pytest.approx(0.3)
        assert af.get_frequency("G") == pytest.approx(0.0)


class TestVariantAlleleFrequencies:
    """Tests for VariantAlleleFrequencies dataclass."""

    def test_basic_properties(self) -> None:
        """Test basic properties."""
        vaf = VariantAlleleFrequencies(
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
            },
        )

        assert vaf.alleles == ["A", "T"]
        assert vaf.get_frequency("B73", "A") == pytest.approx(1.0)
        assert vaf.get_frequency("Mo17", "T") == pytest.approx(1.0)

    def test_frequency_difference(self) -> None:
        """Test frequency difference calculation."""
        vaf = VariantAlleleFrequencies(
            variant_id="chr1:1000:A:T",
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            population_frequencies={
                "B73": AlleleFrequency(
                    population="B73",
                    frequencies={"A": 0.9, "T": 0.1},
                    allele_counts={"A": 9, "T": 1},
                    total_alleles=10,
                    n_samples=5,
                    n_missing=0,
                ),
                "Mo17": AlleleFrequency(
                    population="Mo17",
                    frequencies={"A": 0.1, "T": 0.9},
                    allele_counts={"A": 1, "T": 9},
                    total_alleles=10,
                    n_samples=5,
                    n_missing=0,
                ),
            },
        )

        diff = vaf.frequency_difference("B73", "Mo17", "A")
        assert diff == pytest.approx(0.8)

        max_diff = vaf.max_freq_diff("A")
        assert max_diff == pytest.approx(0.8)


class TestAlleleFrequencyCalculator:
    """Tests for AlleleFrequencyCalculator."""

    def test_calculate_single_variant(
        self,
        test_variant: Variant,
        test_populations: list[Population],
    ) -> None:
        """Test calculating frequencies for a single variant."""
        calc = AlleleFrequencyCalculator()
        result = calc.calculate_single(test_variant, test_populations)

        assert result is not None
        assert result.chrom == "chr1"
        assert result.pos == 1000

        # B73 should be 100% A
        b73_freq = result.get_population_freq("B73")
        assert b73_freq is not None
        assert b73_freq.get_frequency("A") == pytest.approx(1.0)

        # Mo17 should be 100% T
        mo17_freq = result.get_population_freq("Mo17")
        assert mo17_freq is not None
        assert mo17_freq.get_frequency("T") == pytest.approx(1.0)

    def test_calculate_multiple_variants(
        self,
        test_populations: list[Population],
    ) -> None:
        """Test calculating frequencies for multiple variants."""
        variants = [
            Variant(
                chrom="chr1",
                pos=1000,
                ref="A",
                alt=["T"],
                genotypes={
                    "B73_1": [0, 0],
                    "B73_2": [0, 0],
                    "B73_3": [0, 0],
                    "Mo17_1": [1, 1],
                    "Mo17_2": [1, 1],
                    "Mo17_3": [1, 1],
                },
            ),
            Variant(
                chrom="chr1",
                pos=2000,
                ref="G",
                alt=["C"],
                genotypes={
                    "B73_1": [0, 1],
                    "B73_2": [0, 1],
                    "B73_3": [0, 1],
                    "Mo17_1": [0, 0],
                    "Mo17_2": [0, 0],
                    "Mo17_3": [0, 0],
                },
            ),
        ]

        calc = AlleleFrequencyCalculator()
        result = calc.calculate(variants, test_populations)

        assert len(result) == 2
        assert "chr1:1000:A:T" in result

    def test_handle_missing_genotypes(
        self,
        test_populations: list[Population],
    ) -> None:
        """Test handling of missing genotypes."""
        variant = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "B73_1": [0, 0],
                "B73_2": [-1, -1],  # Missing
                "B73_3": [0, 0],
                "Mo17_1": [1, 1],
                "Mo17_2": [1, 1],
                "Mo17_3": [-1, -1],  # Missing
            },
        )

        calc = AlleleFrequencyCalculator()
        result = calc.calculate_single(variant, test_populations)

        assert result is not None

        b73_freq = result.get_population_freq("B73")
        assert b73_freq is not None
        assert b73_freq.n_samples == 2
        assert b73_freq.n_missing == 1

    def test_polyploid_genotypes(self) -> None:
        """Test handling of polyploid genotypes."""
        populations = [
            Population(
                name="Wheat",
                role=PopulationRole.FOUNDER,
                samples=[
                    Sample(name="CS_1", ploidy=4),
                    Sample(name="CS_2", ploidy=4),
                ],
            ),
        ]

        variant = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "CS_1": [0, 0, 0, 1],  # 3 ref, 1 alt
                "CS_2": [0, 0, 1, 1],  # 2 ref, 2 alt
            },
        )

        calc = AlleleFrequencyCalculator()
        result = calc.calculate_single(variant, populations)

        assert result is not None

        wheat_freq = result.get_population_freq("Wheat")
        assert wheat_freq is not None

        # 5 ref alleles + 3 alt alleles = 8 total
        assert wheat_freq.total_alleles == 8
        assert wheat_freq.get_frequency("A") == pytest.approx(5 / 8)
        assert wheat_freq.get_frequency("T") == pytest.approx(3 / 8)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_calculate_population_frequencies(
        self,
        test_variant: Variant,
        test_populations: list[Population],
    ) -> None:
        """Test calculate_population_frequencies function."""
        result = calculate_population_frequencies([test_variant], test_populations)

        assert len(result) == 1
        assert result.populations == ["B73", "Mo17"]

    def test_get_founder_frequencies(self) -> None:
        """Test filtering to founder populations only."""
        populations = [
            Population(
                name="B73",
                role=PopulationRole.FOUNDER,
                samples=[Sample(name="B73_1", ploidy=2)],
            ),
            Population(
                name="RILs",
                role=PopulationRole.DERIVED,
                samples=[Sample(name="RIL_1", ploidy=2)],
            ),
        ]

        variant = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "B73_1": [0, 0],
                "RIL_1": [0, 1],
            },
        )

        result = get_founder_frequencies([variant], populations)

        assert len(result) == 1
        # Should only have B73, not RILs
        var_freq = list(result)[0]
        assert "B73" in var_freq.population_frequencies
        assert "RILs" not in var_freq.population_frequencies
