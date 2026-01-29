"""Genotype extraction at diagnostic marker positions.

This module provides functionality to extract derived sample genotypes
at diagnostic marker positions for proportion estimation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet

logger = logging.getLogger(__name__)


@dataclass
class MarkerGenotype:
    """Genotype at a single marker position.

    Attributes:
        variant_id: Marker variant ID
        chrom: Chromosome
        pos: Position (0-based)
        ref: Reference allele
        alt: Alternate allele
        genotype: List of allele indices (e.g., [0, 1] for het)
        allele_dosage: Dict mapping alleles to counts
        is_missing: Whether genotype is missing
        quality: Genotype quality (GQ) if available
        depth: Read depth (DP) if available
    """

    variant_id: str
    chrom: str
    pos: int
    ref: str
    alt: str
    genotype: list[int]
    allele_dosage: dict[str, int] = field(default_factory=dict)
    is_missing: bool = False
    quality: int | None = None
    depth: int | None = None

    @property
    def is_homozygous(self) -> bool:
        """Check if genotype is homozygous."""
        if self.is_missing or not self.genotype:
            return False
        return len(set(self.genotype)) == 1

    @property
    def is_heterozygous(self) -> bool:
        """Check if genotype is heterozygous."""
        if self.is_missing or not self.genotype:
            return False
        return len(set(self.genotype)) > 1

    @property
    def alleles(self) -> list[str]:
        """Get list of alleles present in genotype."""
        if self.is_missing:
            return []
        allele_map = {0: self.ref, 1: self.alt}
        return [allele_map.get(a, ".") for a in self.genotype if a >= 0]

    def get_allele_frequency(self, allele: str) -> float:
        """Get frequency of a specific allele in this genotype.

        Args:
            allele: Allele to check

        Returns:
            Proportion of alleles matching the specified allele
        """
        if self.is_missing or not self.genotype:
            return 0.0

        valid_alleles = [a for a in self.genotype if a >= 0]
        if not valid_alleles:
            return 0.0

        allele_map = {0: self.ref, 1: self.alt}
        count = sum(1 for a in valid_alleles if allele_map.get(a) == allele)
        return count / len(valid_alleles)


@dataclass
class SampleMarkerGenotypes:
    """Collection of marker genotypes for a single sample.

    Attributes:
        sample_name: Name of the sample
        genotypes: Dict mapping variant_id to MarkerGenotype
        founders: List of founder names (from markers)
    """

    sample_name: str
    genotypes: dict[str, MarkerGenotype] = field(default_factory=dict)
    founders: list[str] = field(default_factory=list)

    def add_genotype(self, genotype: MarkerGenotype) -> None:
        """Add a marker genotype."""
        self.genotypes[genotype.variant_id] = genotype

    def get_genotype(self, variant_id: str) -> MarkerGenotype | None:
        """Get genotype for a specific variant."""
        return self.genotypes.get(variant_id)

    @property
    def n_markers(self) -> int:
        """Get total number of markers."""
        return len(self.genotypes)

    @property
    def n_missing(self) -> int:
        """Get number of missing genotypes."""
        return sum(1 for g in self.genotypes.values() if g.is_missing)

    @property
    def missing_rate(self) -> float:
        """Get proportion of missing genotypes."""
        if not self.genotypes:
            return 0.0
        return self.n_missing / len(self.genotypes)

    def get_chromosome_genotypes(self, chrom: str) -> list[MarkerGenotype]:
        """Get genotypes for a specific chromosome, sorted by position."""
        chrom_genos = [g for g in self.genotypes.values() if g.chrom == chrom]
        return sorted(chrom_genos, key=lambda g: g.pos)

    def get_chromosomes(self) -> list[str]:
        """Get list of chromosomes with genotypes."""
        seen = set()
        chroms = []
        for g in self.genotypes.values():
            if g.chrom not in seen:
                seen.add(g.chrom)
                chroms.append(g.chrom)
        return chroms


class MarkerGenotypeExtractor:
    """Extract sample genotypes at diagnostic marker positions.

    This class reads a VCF file and extracts genotypes for specified
    samples at diagnostic marker positions.
    """

    def __init__(
        self,
        min_gq: int | None = None,
        min_dp: int | None = None,
    ) -> None:
        """Initialize the extractor.

        Args:
            min_gq: Minimum genotype quality (set lower quality to missing)
            min_dp: Minimum read depth (set lower depth to missing)
        """
        self.min_gq = min_gq
        self.min_dp = min_dp

    def extract(
        self,
        vcf_path: str | Path,
        markers: DiagnosticMarkerSet,
        samples: list[str] | None = None,
    ) -> dict[str, SampleMarkerGenotypes]:
        """Extract genotypes at marker positions.

        Args:
            vcf_path: Path to VCF file with derived samples
            markers: Diagnostic marker set defining positions
            samples: List of sample names to extract (None = all)

        Returns:
            Dict mapping sample names to their marker genotypes
        """
        from cyvcf2 import VCF

        vcf_path = Path(vcf_path)
        logger.info(f"Extracting genotypes from {vcf_path}")

        # Build marker position lookup
        marker_lookup = self._build_marker_lookup(markers)
        logger.debug(f"Built lookup for {len(marker_lookup)} markers")

        # Open VCF
        vcf = VCF(str(vcf_path))

        # Determine which samples to extract
        vcf_samples = list(vcf.samples)
        if samples is None:
            samples = vcf_samples
        else:
            # Validate requested samples exist
            missing = set(samples) - set(vcf_samples)
            if missing:
                logger.warning(f"Samples not found in VCF: {missing}")
            samples = [s for s in samples if s in vcf_samples]

        if not samples:
            logger.warning("No samples to extract")
            return {}

        logger.info(f"Extracting genotypes for {len(samples)} samples")

        # Initialize result containers
        results = {
            name: SampleMarkerGenotypes(
                sample_name=name,
                founders=markers.founders,
            )
            for name in samples
        }

        # Get sample indices
        sample_indices = {s: vcf_samples.index(s) for s in samples}

        # Extract genotypes at marker positions
        n_extracted = 0
        for variant in vcf:
            chrom = variant.CHROM
            pos = variant.POS - 1  # Convert to 0-based
            ref = variant.REF
            alts = variant.ALT

            # Skip multiallelic for now (markers should be biallelic)
            if len(alts) != 1:
                continue

            alt = alts[0]

            # Check if this is a marker position
            marker_key = (chrom, pos, ref, alt)
            if marker_key not in marker_lookup:
                continue

            variant_id = marker_lookup[marker_key]
            n_extracted += 1

            # Get quality fields if available
            try:
                gq_values = variant.format("GQ")
            except Exception:
                gq_values = None

            try:
                dp_values = variant.format("DP")
            except Exception:
                dp_values = None

            # Extract genotype for each sample
            for sample_name, sample_idx in sample_indices.items():
                gt = variant.genotypes[sample_idx]
                alleles = gt[:-1]  # Remove phase info

                # Check for missing
                is_missing = any(a < 0 for a in alleles)

                # Get quality metrics
                gq = None
                if gq_values is not None:
                    gq = int(gq_values[sample_idx][0])
                    if gq < 0:
                        gq = None

                dp = None
                if dp_values is not None:
                    dp = int(dp_values[sample_idx][0])
                    if dp < 0:
                        dp = None

                # Apply quality filters
                if not is_missing:
                    if self.min_gq is not None and gq is not None and gq < self.min_gq:
                        is_missing = True
                    if self.min_dp is not None and dp is not None and dp < self.min_dp:
                        is_missing = True

                # Calculate allele dosage
                allele_dosage = {}
                if not is_missing:
                    for a in alleles:
                        allele = ref if a == 0 else alt
                        allele_dosage[allele] = allele_dosage.get(allele, 0) + 1

                # Create genotype object
                marker_geno = MarkerGenotype(
                    variant_id=variant_id,
                    chrom=chrom,
                    pos=pos,
                    ref=ref,
                    alt=alt,
                    genotype=list(alleles),
                    allele_dosage=allele_dosage,
                    is_missing=is_missing,
                    quality=gq,
                    depth=dp,
                )

                results[sample_name].add_genotype(marker_geno)

        vcf.close()

        logger.info(f"Extracted {n_extracted} marker genotypes")
        return results

    def _build_marker_lookup(
        self, markers: DiagnosticMarkerSet
    ) -> dict[tuple[str, int, str, str], str]:
        """Build lookup dict from marker positions to variant IDs.

        Args:
            markers: Diagnostic marker set

        Returns:
            Dict mapping (chrom, pos, ref, alt) tuples to variant IDs
        """
        lookup = {}
        for marker in markers:
            key = (marker.chrom, marker.pos, marker.ref, marker.alt)
            lookup[key] = marker.variant_id
        return lookup

    def extract_region(
        self,
        vcf_path: str | Path,
        markers: DiagnosticMarkerSet,
        chrom: str,
        start: int,
        end: int,
        samples: list[str] | None = None,
    ) -> dict[str, SampleMarkerGenotypes]:
        """Extract genotypes in a specific region.

        Args:
            vcf_path: Path to VCF file
            markers: Diagnostic marker set
            chrom: Chromosome
            start: Start position (0-based)
            end: End position (exclusive)
            samples: List of sample names (None = all)

        Returns:
            Dict mapping sample names to their marker genotypes in region
        """
        from cyvcf2 import VCF

        vcf_path = Path(vcf_path)

        # Filter markers to region
        region_markers = markers.filter(
            chrom=chrom,
            start=start,
            end=end,
        )

        if not region_markers.markers:
            logger.debug(f"No markers in region {chrom}:{start}-{end}")
            return {}

        marker_lookup = self._build_marker_lookup(region_markers)

        # Open VCF with region query
        vcf = VCF(str(vcf_path))

        # Determine samples
        vcf_samples = list(vcf.samples)
        samples = vcf_samples if samples is None else [s for s in samples if s in vcf_samples]

        if not samples:
            return {}

        results = {
            name: SampleMarkerGenotypes(
                sample_name=name,
                founders=markers.founders,
            )
            for name in samples
        }

        sample_indices = {s: vcf_samples.index(s) for s in samples}

        # Query region (VCF uses 1-based positions)
        region_str = f"{chrom}:{start + 1}-{end}"
        try:
            variants = vcf(region_str)
        except Exception:
            # Fall back to full scan if region query fails
            variants = vcf
            logger.debug(f"Region query failed, using full scan for {region_str}")

        for variant in variants:
            v_chrom = variant.CHROM
            v_pos = variant.POS - 1

            # Skip if outside region (for full scan fallback)
            if v_chrom != chrom or v_pos < start or v_pos >= end:
                if v_chrom == chrom and v_pos >= end:
                    break
                continue

            ref = variant.REF
            alts = variant.ALT

            if len(alts) != 1:
                continue

            alt = alts[0]
            marker_key = (v_chrom, v_pos, ref, alt)

            if marker_key not in marker_lookup:
                continue

            variant_id = marker_lookup[marker_key]

            # Extract genotypes
            for sample_name, sample_idx in sample_indices.items():
                gt = variant.genotypes[sample_idx]
                alleles = gt[:-1]
                is_missing = any(a < 0 for a in alleles)

                allele_dosage = {}
                if not is_missing:
                    for a in alleles:
                        allele = ref if a == 0 else alt
                        allele_dosage[allele] = allele_dosage.get(allele, 0) + 1

                marker_geno = MarkerGenotype(
                    variant_id=variant_id,
                    chrom=v_chrom,
                    pos=v_pos,
                    ref=ref,
                    alt=alt,
                    genotype=list(alleles),
                    allele_dosage=allele_dosage,
                    is_missing=is_missing,
                )

                results[sample_name].add_genotype(marker_geno)

        vcf.close()
        return results
