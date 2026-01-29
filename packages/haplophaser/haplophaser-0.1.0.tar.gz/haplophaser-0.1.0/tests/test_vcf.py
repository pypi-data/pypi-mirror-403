"""Tests for VCF parsing functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.filters import (
    BiallelicFilter,
    FilterChain,
    MAFFilter,
    MaxMissingFilter,
    MinQualityFilter,
    PassFilter,
)
from haplophaser.io.vcf import (
    MultiallelicMode,
    Region,
    VCFReader,
    get_sample_names,
    get_vcf_stats,
    load_regions_from_bed,
    load_vcf,
    read_vcf,
    validate_vcf_samples,
)


@pytest.fixture
def diploid_vcf_path() -> Path:
    """Path to diploid test VCF."""
    return Path(__file__).parent / "fixtures" / "diploid.vcf"


@pytest.fixture
def tetraploid_vcf_path() -> Path:
    """Path to tetraploid test VCF."""
    return Path(__file__).parent / "fixtures" / "tetraploid.vcf"


@pytest.fixture
def regions_bed_path() -> Path:
    """Path to test BED file."""
    return Path(__file__).parent / "fixtures" / "regions.bed"


class TestVCFReader:
    """Tests for VCFReader class."""

    def test_open_vcf(self, diploid_vcf_path: Path) -> None:
        """Test opening a VCF file."""
        with VCFReader(diploid_vcf_path) as reader:
            assert len(reader.sample_names) == 6
            assert "B73" in reader.sample_names
            assert "RIL_003" in reader.sample_names

    def test_sample_subsetting(self, diploid_vcf_path: Path) -> None:
        """Test loading subset of samples."""
        with VCFReader(diploid_vcf_path, samples=["B73", "Mo17"]) as reader:
            assert len(reader.sample_names) == 2
            assert "B73" in reader.sample_names
            assert "Mo17" in reader.sample_names
            assert "W22" not in reader.sample_names

    def test_iterate_variants(self, diploid_vcf_path: Path) -> None:
        """Test iterating over variants."""
        with VCFReader(diploid_vcf_path) as reader:
            variants = list(reader)
            assert len(variants) == 12

            # Check first variant
            first = variants[0]
            assert first.chrom == "chr1"
            assert first.pos == 1000  # 0-based
            assert first.ref == "A"
            assert first.alt == ["T"]

    def test_variant_genotypes(self, diploid_vcf_path: Path) -> None:
        """Test that genotypes are correctly parsed."""
        with VCFReader(diploid_vcf_path) as reader:
            variants = list(reader)
            first = variants[0]

            # B73 is 0/0
            assert first.get_genotype("B73") == [0, 0]
            # Mo17 is 1/1
            assert first.get_genotype("Mo17") == [1, 1]
            # RIL_001 is 0/1
            assert first.get_genotype("RIL_001") == [0, 1]

    def test_missing_genotypes(self, diploid_vcf_path: Path) -> None:
        """Test handling of missing genotypes."""
        with VCFReader(diploid_vcf_path) as reader:
            variants = list(reader)
            # Variant at chr1:25000 has missing genotypes
            var_with_missing = [v for v in variants if v.pos == 24999][0]

            # B73 and RIL_002 have ./. genotypes
            assert var_with_missing.get_genotype("B73") == [-1, -1]
            assert var_with_missing.get_genotype("RIL_002") == [-1, -1]

    def test_format_fields_extracted(self, diploid_vcf_path: Path) -> None:
        """Test that FORMAT fields (DP, GQ, AD) are extracted."""
        with VCFReader(diploid_vcf_path, extract_format_fields=True) as reader:
            variants = list(reader)
            first = variants[0]

            # Check DP extracted
            assert "sample_dp" in first.info
            assert first.info["sample_dp"]["B73"] == 20
            assert first.info["sample_dp"]["Mo17"] == 22

            # Check GQ extracted
            assert "sample_gq" in first.info
            assert first.info["sample_gq"]["B73"] == 99

    def test_stats(self, diploid_vcf_path: Path) -> None:
        """Test that statistics are tracked."""
        with VCFReader(diploid_vcf_path) as reader:
            list(reader)  # Consume iterator
            stats = reader.stats

            assert stats.n_variants == 12
            assert stats.n_samples == 6
            assert "chr1" in stats.chromosomes
            assert "chr2" in stats.chromosomes


class TestVCFReaderTetraploid:
    """Tests for tetraploid VCF reading."""

    def test_tetraploid_genotypes(self, tetraploid_vcf_path: Path) -> None:
        """Test parsing tetraploid genotypes."""
        with VCFReader(tetraploid_vcf_path) as reader:
            variants = list(reader)
            assert len(variants) == 8

            first = variants[0]
            # Durum_A is 0/0/0/0
            gt = first.get_genotype("Durum_A")
            assert gt is not None
            assert len(gt) == 4
            assert gt == [0, 0, 0, 0]

            # Durum_B is 1/1/1/1
            assert first.get_genotype("Durum_B") == [1, 1, 1, 1]

            # Derived_1 is 0/0/1/1
            assert first.get_genotype("Derived_1") == [0, 0, 1, 1]

    def test_tetraploid_allele_counts(self, tetraploid_vcf_path: Path) -> None:
        """Test allele counting in tetraploid."""
        with VCFReader(tetraploid_vcf_path) as reader:
            variants = list(reader)
            first = variants[0]

            # Derived_1 has 0/0/1/1: 2 ref, 2 alt
            counts = first.allele_counts("Derived_1")
            assert counts == {0: 2, 1: 2}

            # Derived_2 has 0/0/0/1: 3 ref, 1 alt
            counts = first.allele_counts("Derived_2")
            assert counts == {0: 3, 1: 1}


class TestMultiallelicHandling:
    """Tests for multiallelic variant handling."""

    def test_multiallelic_keep(self, diploid_vcf_path: Path) -> None:
        """Test keeping multiallelic variants."""
        with VCFReader(diploid_vcf_path, multiallelic=MultiallelicMode.KEEP) as reader:
            variants = list(reader)
            multiallelic = [v for v in variants if len(v.alt) > 1]
            assert len(multiallelic) == 1
            assert multiallelic[0].alt == ["T", "A"]

    def test_multiallelic_skip(self, diploid_vcf_path: Path) -> None:
        """Test skipping multiallelic variants."""
        with VCFReader(diploid_vcf_path, multiallelic=MultiallelicMode.SKIP) as reader:
            variants = list(reader)
            multiallelic = [v for v in variants if len(v.alt) > 1]
            assert len(multiallelic) == 0
            # Should have 11 variants (12 - 1 multiallelic)
            assert len(variants) == 11

    def test_multiallelic_split(self, diploid_vcf_path: Path) -> None:
        """Test splitting multiallelic variants."""
        with VCFReader(diploid_vcf_path, multiallelic=MultiallelicMode.SPLIT) as reader:
            variants = list(reader)
            # Original has 12 variants, 1 multiallelic (3 alleles) -> 11 + 2 = 13
            assert len(variants) == 13

            # All should now be biallelic
            for v in variants:
                assert len(v.alt) <= 1


class TestRegionFiltering:
    """Tests for region-based filtering."""

    def test_load_regions_from_bed(self, regions_bed_path: Path) -> None:
        """Test loading regions from BED file."""
        regions = load_regions_from_bed(regions_bed_path)
        assert len(regions) == 3
        assert regions[0].chrom == "chr1"
        assert regions[0].start == 0
        assert regions[0].end == 10000

    @pytest.mark.skip(reason="Requires bgzipped and indexed VCF (tabix)")
    def test_vcf_with_regions(self, diploid_vcf_path: Path, regions_bed_path: Path) -> None:
        """Test reading VCF with region filtering.

        Note: Region-based filtering requires the VCF to be bgzipped and indexed.
        This test is skipped because the test fixture is a plain VCF.
        """
        regions = load_regions_from_bed(regions_bed_path)

        with VCFReader(diploid_vcf_path, regions=regions) as reader:
            variants = list(reader)

            # Check that variants are in expected regions
            for v in variants:
                in_region = False
                for r in regions:
                    if v.chrom == r.chrom and r.start <= v.pos < r.end:
                        in_region = True
                        break
                assert in_region, f"Variant {v.chrom}:{v.pos} not in any region"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_sample_names(self, diploid_vcf_path: Path) -> None:
        """Test getting sample names."""
        names = get_sample_names(diploid_vcf_path)
        assert len(names) == 6
        assert "B73" in names

    def test_load_vcf(self, diploid_vcf_path: Path) -> None:
        """Test loading all variants into memory."""
        variants = load_vcf(diploid_vcf_path)
        assert len(variants) == 12

    def test_load_vcf_max_variants(self, diploid_vcf_path: Path) -> None:
        """Test loading with variant limit."""
        variants = load_vcf(diploid_vcf_path, max_variants=5)
        assert len(variants) == 5

    def test_read_vcf_iterator(self, diploid_vcf_path: Path) -> None:
        """Test read_vcf generator function."""
        count = 0
        for variant in read_vcf(diploid_vcf_path):
            count += 1
        assert count == 12

    def test_get_vcf_stats(self, diploid_vcf_path: Path) -> None:
        """Test getting VCF statistics."""
        stats = get_vcf_stats(diploid_vcf_path)
        assert stats.n_variants == 12
        assert stats.n_samples == 6

    def test_validate_vcf_samples(self, diploid_vcf_path: Path) -> None:
        """Test sample validation."""
        found, missing = validate_vcf_samples(
            diploid_vcf_path,
            ["B73", "Mo17", "NonExistent"],
        )
        assert "B73" in found
        assert "Mo17" in found
        assert "NonExistent" in missing


class TestVCFWithFilters:
    """Tests for VCF reading with filter chains."""

    def test_biallelic_filter(self, diploid_vcf_path: Path) -> None:
        """Test filtering to biallelic only."""
        filters = FilterChain([BiallelicFilter()])

        variants = load_vcf(diploid_vcf_path, filters=filters)

        for v in variants:
            assert v.n_alleles == 2

    def test_maf_filter(self, diploid_vcf_path: Path) -> None:
        """Test MAF filtering."""
        filters = FilterChain([MAFFilter(min_maf=0.2)])

        variants = load_vcf(diploid_vcf_path, filters=filters)

        # Verify all variants have MAF >= 0.2
        for v in variants:
            allele_counts = {}
            total = 0
            for gt in v.genotypes.values():
                for a in gt:
                    if a >= 0:
                        allele_counts[a] = allele_counts.get(a, 0) + 1
                        total += 1
            if total > 0 and len(allele_counts) >= 2:
                min_count = min(allele_counts.values())
                maf = min_count / total
                assert maf >= 0.2

    def test_max_missing_filter(self, diploid_vcf_path: Path) -> None:
        """Test maximum missing rate filter."""
        filters = FilterChain([MaxMissingFilter(max_missing=0.1)])

        variants = load_vcf(diploid_vcf_path, filters=filters)

        # Verify no variant has >10% missing
        for v in variants:
            n_missing = sum(1 for gt in v.genotypes.values() if all(a == -1 for a in gt))
            missing_rate = n_missing / len(v.genotypes)
            assert missing_rate <= 0.1

    def test_quality_filter(self, diploid_vcf_path: Path) -> None:
        """Test quality filter."""
        filters = FilterChain([MinQualityFilter(min_qual=90)])

        variants = load_vcf(diploid_vcf_path, filters=filters)

        for v in variants:
            if v.quality is not None:
                assert v.quality >= 90

    def test_pass_filter(self, diploid_vcf_path: Path) -> None:
        """Test PASS filter status filter."""
        filters = FilterChain([PassFilter()])

        # Without filter
        all_variants = load_vcf(diploid_vcf_path)
        lowqual = [v for v in all_variants if v.filter_status == "LowQual"]
        assert len(lowqual) > 0

        # With filter
        variants = load_vcf(diploid_vcf_path, filters=filters)
        for v in variants:
            assert v.filter_status in ("PASS", ".", "")

    def test_combined_filters(self, diploid_vcf_path: Path) -> None:
        """Test combining multiple filters."""
        filters = FilterChain([
            PassFilter(),
            BiallelicFilter(),
            MAFFilter(min_maf=0.1),
        ])

        variants = load_vcf(diploid_vcf_path, filters=filters)

        # Check filter stats
        stats = filters.stats
        assert stats.input_count > 0
        assert stats.output_count <= stats.input_count


class TestVCFEdgeCases:
    """Tests for edge cases and error handling."""

    def test_missing_file(self) -> None:
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError), VCFReader("/nonexistent/path.vcf") as reader:
            list(reader)

    @pytest.mark.skip(reason="Requires bgzipped and indexed VCF (tabix)")
    def test_empty_region(self, diploid_vcf_path: Path) -> None:
        """Test fetching from region with no variants.

        Note: Region-based filtering requires the VCF to be bgzipped and indexed.
        This test is skipped because the test fixture is a plain VCF.
        """
        regions = [Region(chrom="chr99", start=0, end=1000)]

        with VCFReader(diploid_vcf_path, regions=regions) as reader:
            variants = list(reader)
            assert len(variants) == 0
