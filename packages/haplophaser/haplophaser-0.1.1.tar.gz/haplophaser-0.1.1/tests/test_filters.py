"""Tests for variant filtering system."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.filters import (
    BiallelicFilter,
    ChromosomeFilter,
    FilterChain,
    InformativeFilter,
    MAFFilter,
    MaxMissingFilter,
    MinDepthFilter,
    MinGQFilter,
    MinQualityFilter,
    PassFilter,
    PolyploidGenotypeFilter,
    RegionFilter,
    SNPFilter,
    create_default_filter_chain,
)
from haplophaser.core.models import Variant


@pytest.fixture
def snp_variant() -> Variant:
    """Create a simple SNP variant."""
    return Variant(
        chrom="chr1",
        pos=1000,
        ref="A",
        alt=["T"],
        genotypes={
            "sample1": [0, 0],
            "sample2": [0, 1],
            "sample3": [1, 1],
        },
        quality=99.0,
        filter_status="PASS",
    )


@pytest.fixture
def low_qual_variant() -> Variant:
    """Create a low quality variant."""
    return Variant(
        chrom="chr1",
        pos=2000,
        ref="G",
        alt=["C"],
        genotypes={
            "sample1": [0, 0],
            "sample2": [0, 1],
            "sample3": [1, 1],
        },
        quality=15.0,
        filter_status="LowQual",
    )


@pytest.fixture
def multiallelic_variant() -> Variant:
    """Create a multiallelic variant."""
    return Variant(
        chrom="chr1",
        pos=3000,
        ref="C",
        alt=["T", "G"],
        genotypes={
            "sample1": [0, 0],
            "sample2": [1, 2],
            "sample3": [2, 2],
        },
        quality=85.0,
        filter_status="PASS",
    )


@pytest.fixture
def variant_with_missing() -> Variant:
    """Create a variant with missing genotypes."""
    return Variant(
        chrom="chr1",
        pos=4000,
        ref="T",
        alt=["A"],
        genotypes={
            "sample1": [0, 0],
            "sample2": [-1, -1],
            "sample3": [-1, -1],
            "sample4": [1, 1],
        },
        quality=90.0,
        filter_status="PASS",
    )


@pytest.fixture
def variant_with_depth() -> Variant:
    """Create a variant with depth information."""
    return Variant(
        chrom="chr1",
        pos=5000,
        ref="A",
        alt=["G"],
        genotypes={
            "sample1": [0, 0],
            "sample2": [0, 1],
            "sample3": [1, 1],
        },
        quality=95.0,
        filter_status="PASS",
        info={
            "DP": 100,
            "sample_dp": {"sample1": 35, "sample2": 30, "sample3": 35},
            "sample_gq": {"sample1": 99, "sample2": 45, "sample3": 99},
        },
    )


class TestMinQualityFilter:
    """Tests for MinQualityFilter."""

    def test_pass_high_quality(self, snp_variant: Variant) -> None:
        """Test that high quality variants pass."""
        f = MinQualityFilter(min_qual=30.0)
        assert f.test(snp_variant) is True

    def test_fail_low_quality(self, low_qual_variant: Variant) -> None:
        """Test that low quality variants fail."""
        f = MinQualityFilter(min_qual=30.0)
        assert f.test(low_qual_variant) is False

    def test_pass_no_quality(self) -> None:
        """Test that variants without quality pass."""
        f = MinQualityFilter(min_qual=30.0)
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={"s1": [0, 1]},
            quality=None,
        )
        assert f.test(var) is True


class TestMinDepthFilter:
    """Tests for MinDepthFilter."""

    def test_pass_sufficient_depth(self, variant_with_depth: Variant) -> None:
        """Test variants with sufficient depth pass."""
        f = MinDepthFilter(min_dp=20)
        assert f.test(variant_with_depth) is True

    def test_fail_low_depth(self, variant_with_depth: Variant) -> None:
        """Test variants with low depth fail."""
        f = MinDepthFilter(min_dp=50)
        assert f.test(variant_with_depth) is False

    def test_pass_no_depth_info(self, snp_variant: Variant) -> None:
        """Test that variants without depth info pass by default."""
        f = MinDepthFilter(min_dp=10)
        assert f.test(snp_variant) is True


class TestMinGQFilter:
    """Tests for MinGQFilter."""

    def test_pass_high_gq(self, variant_with_depth: Variant) -> None:
        """Test variants with high GQ pass."""
        f = MinGQFilter(min_gq=40)
        assert f.test(variant_with_depth) is True

    def test_fail_all_low_gq(self) -> None:
        """Test variants with all low GQ fail when require_all=True."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={"s1": [0, 1], "s2": [1, 1]},
            info={"sample_gq": {"s1": 10, "s2": 15}},
        )
        f = MinGQFilter(min_gq=20, require_all=True)
        assert f.test(var) is False


class TestMaxMissingFilter:
    """Tests for MaxMissingFilter."""

    def test_pass_low_missing(self, snp_variant: Variant) -> None:
        """Test variants with low missing rate pass."""
        f = MaxMissingFilter(max_missing=0.5)
        assert f.test(snp_variant) is True

    def test_fail_high_missing(self, variant_with_missing: Variant) -> None:
        """Test variants with high missing rate fail."""
        f = MaxMissingFilter(max_missing=0.25)
        assert f.test(variant_with_missing) is False

    def test_pass_allowed_missing(self, variant_with_missing: Variant) -> None:
        """Test variants pass when missing rate is within threshold."""
        f = MaxMissingFilter(max_missing=0.5)
        assert f.test(variant_with_missing) is True


class TestMAFFilter:
    """Tests for MAFFilter."""

    def test_pass_high_maf(self, snp_variant: Variant) -> None:
        """Test variants with high MAF pass."""
        f = MAFFilter(min_maf=0.1)
        assert f.test(snp_variant) is True

    def test_fail_low_maf(self) -> None:
        """Test variants with low MAF fail."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "s1": [0, 0],
                "s2": [0, 0],
                "s3": [0, 0],
                "s4": [0, 0],
                "s5": [0, 1],
            },
        )
        f = MAFFilter(min_maf=0.2)
        assert f.test(var) is False


class TestBiallelicFilter:
    """Tests for BiallelicFilter."""

    def test_pass_biallelic(self, snp_variant: Variant) -> None:
        """Test biallelic variants pass."""
        f = BiallelicFilter()
        assert f.test(snp_variant) is True

    def test_fail_multiallelic(self, multiallelic_variant: Variant) -> None:
        """Test multiallelic variants fail."""
        f = BiallelicFilter()
        assert f.test(multiallelic_variant) is False

    def test_monomorphic_excluded(self) -> None:
        """Test monomorphic sites excluded by default."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=[],
            genotypes={"s1": [0, 0]},
        )
        f = BiallelicFilter(include_monomorphic=False)
        assert f.test(var) is False

    def test_monomorphic_included(self) -> None:
        """Test monomorphic sites included when configured."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=[],
            genotypes={"s1": [0, 0]},
        )
        f = BiallelicFilter(include_monomorphic=True)
        assert f.test(var) is True


class TestSNPFilter:
    """Tests for SNPFilter."""

    def test_pass_snp(self, snp_variant: Variant) -> None:
        """Test SNPs pass."""
        f = SNPFilter()
        assert f.test(snp_variant) is True

    def test_fail_indel(self) -> None:
        """Test indels fail."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="AT",
            alt=["A"],
            genotypes={"s1": [0, 1]},
        )
        f = SNPFilter()
        assert f.test(var) is False


class TestPassFilter:
    """Tests for PassFilter."""

    def test_pass_variant(self, snp_variant: Variant) -> None:
        """Test PASS variants pass."""
        f = PassFilter()
        assert f.test(snp_variant) is True

    def test_fail_variant(self, low_qual_variant: Variant) -> None:
        """Test non-PASS variants fail."""
        f = PassFilter()
        assert f.test(low_qual_variant) is False


class TestRegionFilter:
    """Tests for RegionFilter."""

    def test_pass_in_region(self, snp_variant: Variant) -> None:
        """Test variants in region pass."""
        f = RegionFilter([("chr1", 0, 5000)])
        assert f.test(snp_variant) is True

    def test_fail_outside_region(self, snp_variant: Variant) -> None:
        """Test variants outside region fail."""
        f = RegionFilter([("chr1", 5000, 10000)])
        assert f.test(snp_variant) is False

    def test_fail_wrong_chromosome(self, snp_variant: Variant) -> None:
        """Test variants on wrong chromosome fail."""
        f = RegionFilter([("chr2", 0, 10000)])
        assert f.test(snp_variant) is False

    def test_from_bed(self, tmp_path: Path) -> None:
        """Test loading regions from BED file."""
        bed_content = "chr1\t0\t5000\nchr2\t1000\t2000\n"
        bed_file = tmp_path / "test.bed"
        bed_file.write_text(bed_content)

        f = RegionFilter.from_bed(bed_file)
        assert f.test(Variant(chrom="chr1", pos=1000, ref="A", alt=["T"], genotypes={}))
        assert not f.test(Variant(chrom="chr1", pos=6000, ref="A", alt=["T"], genotypes={}))


class TestChromosomeFilter:
    """Tests for ChromosomeFilter."""

    def test_include_chromosome(self, snp_variant: Variant) -> None:
        """Test including specific chromosomes."""
        f = ChromosomeFilter(["chr1"], exclude=False)
        assert f.test(snp_variant) is True

        f2 = ChromosomeFilter(["chr2"], exclude=False)
        assert f2.test(snp_variant) is False

    def test_exclude_chromosome(self, snp_variant: Variant) -> None:
        """Test excluding specific chromosomes."""
        f = ChromosomeFilter(["chr1"], exclude=True)
        assert f.test(snp_variant) is False

        f2 = ChromosomeFilter(["chr2"], exclude=True)
        assert f2.test(snp_variant) is True


class TestInformativeFilter:
    """Tests for InformativeFilter."""

    def test_informative_variant(self) -> None:
        """Test informative variants pass."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "founder1": [0, 0],
                "founder2": [1, 1],
                "derived1": [0, 1],
            },
        )
        f = InformativeFilter(founder_samples=["founder1", "founder2"])
        assert f.test(var) is True

    def test_uninformative_variant(self) -> None:
        """Test uninformative variants fail."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "founder1": [0, 0],
                "founder2": [0, 0],
                "derived1": [0, 1],
            },
        )
        f = InformativeFilter(founder_samples=["founder1", "founder2"])
        assert f.test(var) is False


class TestPolyploidGenotypeFilter:
    """Tests for PolyploidGenotypeFilter."""

    def test_correct_ploidy(self) -> None:
        """Test variants with correct ploidy pass."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "s1": [0, 0, 0, 0],
                "s2": [0, 0, 1, 1],
            },
        )
        f = PolyploidGenotypeFilter(expected_ploidy=4)
        assert f.test(var) is True

    def test_wrong_ploidy_non_strict(self) -> None:
        """Test wrong ploidy passes in non-strict mode."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "s1": [0, 0],  # Diploid in tetraploid context
                "s2": [0, 0, 1, 1],
            },
        )
        f = PolyploidGenotypeFilter(expected_ploidy=4, strict=False)
        assert f.test(var) is True

    def test_wrong_ploidy_strict(self) -> None:
        """Test wrong ploidy fails in strict mode."""
        var = Variant(
            chrom="chr1",
            pos=1000,
            ref="A",
            alt=["T"],
            genotypes={
                "s1": [0, 0],  # Diploid in tetraploid context
                "s2": [0, 0, 1, 1],
            },
        )
        f = PolyploidGenotypeFilter(expected_ploidy=4, strict=True)
        assert f.test(var) is False


class TestFilterChain:
    """Tests for FilterChain."""

    def test_empty_chain(self, snp_variant: Variant) -> None:
        """Test empty filter chain passes all variants."""
        chain = FilterChain([])
        results = list(chain.apply([snp_variant]))
        assert len(results) == 1

    def test_single_filter(self, snp_variant: Variant, low_qual_variant: Variant) -> None:
        """Test chain with single filter."""
        chain = FilterChain([MinQualityFilter(min_qual=30.0)])
        results = list(chain.apply([snp_variant, low_qual_variant]))
        assert len(results) == 1
        assert results[0] == snp_variant

    def test_multiple_filters(self) -> None:
        """Test chain with multiple filters."""
        variants = [
            Variant(chrom="chr1", pos=1000, ref="A", alt=["T"],
                    genotypes={"s1": [0, 0], "s2": [1, 1]}, quality=99.0, filter_status="PASS"),
            Variant(chrom="chr1", pos=2000, ref="G", alt=["C"],
                    genotypes={"s1": [0, 0], "s2": [0, 0]}, quality=99.0, filter_status="PASS"),  # Low MAF
            Variant(chrom="chr1", pos=3000, ref="T", alt=["A", "G"],
                    genotypes={"s1": [0, 1], "s2": [1, 2]}, quality=99.0, filter_status="PASS"),  # Multiallelic
        ]

        chain = FilterChain([
            BiallelicFilter(),
            MAFFilter(min_maf=0.1),
        ])
        results = list(chain.apply(variants))
        assert len(results) == 1

    def test_chain_statistics(self) -> None:
        """Test that chain tracks statistics."""
        variants = [
            Variant(chrom="chr1", pos=i * 1000, ref="A", alt=["T"],
                    genotypes={"s1": [0, 0], "s2": [1, 1]}, quality=99.0 - i * 10)
            for i in range(10)
        ]

        chain = FilterChain([MinQualityFilter(min_qual=50.0)])
        list(chain.apply(variants))

        stats = chain.stats
        assert stats.input_count == 10
        assert stats.output_count < 10

    def test_add_filter(self) -> None:
        """Test adding filters to chain."""
        chain = FilterChain()
        chain.add(BiallelicFilter())
        chain.add(MAFFilter(min_maf=0.1))

        assert len(chain.filters) == 2


class TestCreateDefaultFilterChain:
    """Tests for create_default_filter_chain convenience function."""

    def test_default_parameters(self) -> None:
        """Test creating chain with default parameters."""
        chain = create_default_filter_chain()
        assert len(chain.filters) > 0

    def test_custom_parameters(self) -> None:
        """Test creating chain with custom parameters."""
        chain = create_default_filter_chain(
            min_qual=50.0,
            max_missing=0.1,
            min_maf=0.1,
            biallelic_only=True,
            snps_only=True,
        )
        # Should have: PassFilter, MinQualityFilter, BiallelicFilter, SNPFilter, MaxMissingFilter, MAFFilter
        assert len(chain.filters) >= 5
