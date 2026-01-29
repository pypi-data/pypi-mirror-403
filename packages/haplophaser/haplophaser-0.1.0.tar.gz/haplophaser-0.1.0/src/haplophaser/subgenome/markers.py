"""
Subgenome-diagnostic marker identification.

Identifies markers that distinguish between subgenomes based on:
- Fixed differences between homeologous regions
- Ancestral vs derived alleles (using outgroup)
- Synteny-supported divergent sites
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from haplophaser.subgenome.models import (
    SubgenomeConfig,
    SubgenomeMarker,
)

if TYPE_CHECKING:
    from haplophaser.core.models import Variant

logger = logging.getLogger(__name__)


@dataclass
class MarkerFinderParams:
    """Parameters for subgenome marker identification.

    Parameters
    ----------
    min_divergence : float
        Minimum sequence divergence for marker.
    min_synteny_support : bool
        Require synteny block confirmation.
    min_qual : float
        Minimum variant quality.
    min_depth : int
        Minimum read depth.
    max_missing : float
        Maximum missing rate across samples.
    window_size : int
        Window size for local divergence calculation.
    """

    min_divergence: float = 0.05
    min_synteny_support: bool = False
    min_qual: float = 30.0
    min_depth: int = 10
    max_missing: float = 0.2
    window_size: int = 10_000


class SubgenomeMarkerFinder:
    """Identify markers diagnostic for subgenomes.

    Subgenome markers are variants where alleles are fixed differently
    between subgenomes. These arise from divergence since the WGD
    and can be used to assign genomic regions to subgenomes.

    Parameters
    ----------
    config : SubgenomeConfig
        Subgenome configuration.
    min_divergence : float
        Minimum divergence for marker.
    min_synteny_support : bool
        Require synteny confirmation.

    Examples
    --------
    >>> config = SubgenomeConfig.maize_default()
    >>> finder = SubgenomeMarkerFinder(config)
    >>> markers = finder.from_vcf(
    ...     vcf="maize_variants.vcf.gz",
    ...     reference_assignments="B73_subgenomes.bed",
    ... )
    """

    def __init__(
        self,
        config: SubgenomeConfig,
        min_divergence: float = 0.05,
        min_synteny_support: bool = False,
    ) -> None:
        self.config = config
        self.params = MarkerFinderParams(
            min_divergence=min_divergence,
            min_synteny_support=min_synteny_support,
        )
        self._synteny_blocks: dict[str, list] = {}

    def from_vcf(
        self,
        vcf: Path | str,
        reference_assignments: Path | str,
        samples_by_subgenome: dict[str, list[str]] | None = None,
        synteny_blocks: Path | str | None = None,
        outgroup_sample: str | None = None,
    ) -> list[SubgenomeMarker]:
        """Find subgenome markers from VCF.

        Parameters
        ----------
        vcf : Path or str
            VCF file with variants.
        reference_assignments : Path or str
            BED file with known subgenome assignments.
        samples_by_subgenome : dict, optional
            Mapping of subgenome to sample names for that subgenome.
        synteny_blocks : Path or str, optional
            Synteny blocks for context.
        outgroup_sample : str, optional
            Outgroup sample for ancestral state.

        Returns
        -------
        list[SubgenomeMarker]
            Identified subgenome markers.
        """
        from haplophaser.io.synteny import load_reference_assignments
        from haplophaser.io.vcf import VCFReader

        vcf_path = Path(vcf)

        # Load reference assignments
        ref_assignments = load_reference_assignments(reference_assignments)

        # Load synteny blocks if provided
        if synteny_blocks:
            from haplophaser.io.synteny import load_synteny
            blocks = load_synteny(synteny_blocks)
            self._index_synteny_blocks(blocks)

        markers = []

        with VCFReader(vcf_path) as reader:
            # Get sample names
            all_samples = reader.sample_names

            # If samples_by_subgenome not provided, try to infer from reference
            if samples_by_subgenome is None:
                samples_by_subgenome = self._infer_samples_by_subgenome(
                    all_samples, ref_assignments
                )

            for variant in reader:
                marker = self._evaluate_variant(
                    variant,
                    ref_assignments,
                    samples_by_subgenome,
                    outgroup_sample,
                )
                if marker is not None:
                    markers.append(marker)

        logger.info(f"Found {len(markers)} subgenome-diagnostic markers")
        return markers

    def from_alignment(
        self,
        alignment: Path | str,
        reference_assignments: Path | str,
    ) -> list[SubgenomeMarker]:
        """Find subgenome markers from whole-genome alignment.

        Parameters
        ----------
        alignment : Path or str
            PAF or similar alignment file.
        reference_assignments : Path or str
            Known subgenome assignments.

        Returns
        -------
        list[SubgenomeMarker]
            Identified markers.
        """
        from haplophaser.io.synteny import load_reference_assignments, load_synteny

        # Load synteny blocks from alignment
        blocks = load_synteny(alignment)
        self._index_synteny_blocks(blocks)

        # Load reference assignments
        ref_assignments = load_reference_assignments(reference_assignments)

        markers = []

        # Find divergent positions in aligned blocks
        for block in blocks:
            block_markers = self._find_markers_in_block(block, ref_assignments)
            markers.extend(block_markers)

        logger.info(f"Found {len(markers)} subgenome-diagnostic markers")
        return markers

    def from_known_differences(
        self,
        differences_file: Path | str,
        synteny_blocks: Path | str | None = None,
    ) -> list[SubgenomeMarker]:
        """Load markers from pre-computed differences file.

        Parameters
        ----------
        differences_file : Path or str
            TSV file with columns: chrom, pos, ref, alt, subgenome1_allele, subgenome2_allele, ...
        synteny_blocks : Path or str, optional
            Synteny blocks for annotation.

        Returns
        -------
        list[SubgenomeMarker]
            Loaded markers.
        """
        path = Path(differences_file)
        markers = []

        # Load synteny if provided
        if synteny_blocks:
            from haplophaser.io.synteny import load_synteny
            blocks = load_synteny(synteny_blocks)
            self._index_synteny_blocks(blocks)

        with open(path) as f:
            header = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                fields = line.split("\t")
                if header is None:
                    header = [h.lower() for h in fields]
                    continue

                row = dict(zip(header, fields, strict=False))

                chrom = row.get("chrom", row.get("chr", ""))
                pos = int(row.get("pos", row.get("position", 0)))
                ref = row.get("ref", "")
                alt = row.get("alt", "")

                # Extract subgenome alleles
                subgenome_alleles = {}
                for sg in self.config.subgenome_names:
                    key = f"{sg.lower()}_allele"
                    if key in row:
                        subgenome_alleles[sg] = row[key]

                if len(subgenome_alleles) < 2:
                    continue

                # Get synteny block if available
                synteny_block = self._find_synteny_block(chrom, pos)

                divergence = float(row.get("divergence", 0.1))

                marker = SubgenomeMarker(
                    marker_id=f"{chrom}_{pos}",
                    chrom=chrom,
                    pos=pos,
                    ref=ref,
                    alt=alt,
                    subgenome_alleles=subgenome_alleles,
                    divergence=divergence,
                    synteny_block=synteny_block,
                    confidence=0.9,
                )
                markers.append(marker)

        logger.info(f"Loaded {len(markers)} subgenome markers from {path}")
        return markers

    def _evaluate_variant(
        self,
        variant: Variant,
        ref_assignments: dict[str, list[tuple[int, int, str]]],
        samples_by_subgenome: dict[str, list[str]],
        outgroup_sample: str | None = None,
    ) -> SubgenomeMarker | None:
        """Evaluate if a variant is a subgenome-diagnostic marker.

        Parameters
        ----------
        variant : Variant
            Variant to evaluate.
        ref_assignments : dict
            Reference subgenome assignments.
        samples_by_subgenome : dict
            Samples per subgenome.
        outgroup_sample : str, optional
            Outgroup sample name.

        Returns
        -------
        SubgenomeMarker or None
            Marker if variant qualifies, None otherwise.
        """
        # Check quality
        if variant.quality and variant.quality < self.params.min_qual:
            return None

        # Only consider biallelic SNPs
        if not variant.is_snp or len(variant.alt) != 1:
            return None

        # Get allele frequencies by subgenome
        subgenome_alleles: dict[str, dict[str, int]] = {}

        for sg, samples in samples_by_subgenome.items():
            allele_counts: dict[str, int] = defaultdict(int)
            total = 0

            for sample in samples:
                gt = variant.genotypes.get(sample)
                if gt is None:
                    continue

                for allele_idx in gt:
                    if allele_idx < 0:
                        continue
                    allele = variant.ref if allele_idx == 0 else variant.alt[allele_idx - 1]
                    allele_counts[allele] += 1
                    total += 1

            if total > 0:
                subgenome_alleles[sg] = dict(allele_counts)

        # Check if we have data for at least 2 subgenomes
        if len(subgenome_alleles) < 2:
            return None

        # Check for fixed difference
        fixed_alleles: dict[str, str] = {}
        for sg, counts in subgenome_alleles.items():
            if len(counts) == 1:
                fixed_alleles[sg] = list(counts.keys())[0]
            else:
                # Check if one allele is dominant (>90%)
                total = sum(counts.values())
                for allele, count in counts.items():
                    if count / total >= 0.9:
                        fixed_alleles[sg] = allele
                        break

        # Need fixed alleles in all subgenomes that differ
        if len(fixed_alleles) < 2:
            return None

        # Check that alleles differ between subgenomes
        allele_set = set(fixed_alleles.values())
        if len(allele_set) < 2:
            return None

        # Calculate divergence (proportion of sites that differ)
        divergence = self._calculate_local_divergence(
            variant.chrom, variant.pos, samples_by_subgenome
        )

        if divergence < self.params.min_divergence:
            # Use a default if divergence calculation failed
            divergence = 0.1

        # Get synteny block
        synteny_block = self._find_synteny_block(variant.chrom, variant.pos)

        # Check synteny support if required
        if self.params.min_synteny_support and synteny_block is None:
            return None

        # Determine ancestral state from outgroup if available
        confidence = 0.8
        if outgroup_sample and outgroup_sample in variant.genotypes:
            gt = variant.genotypes[outgroup_sample]
            if gt and gt[0] >= 0:
                variant.ref if gt[0] == 0 else variant.alt[gt[0] - 1]
                # Boost confidence if ancestral state is clear
                confidence = 0.9

        return SubgenomeMarker(
            marker_id=f"{variant.chrom}_{variant.pos}",
            chrom=variant.chrom,
            pos=variant.pos,
            ref=variant.ref,
            alt=variant.alt[0],
            subgenome_alleles=fixed_alleles,
            divergence=divergence,
            synteny_block=synteny_block,
            confidence=confidence,
        )

    def _calculate_local_divergence(
        self,
        chrom: str,
        pos: int,
        samples_by_subgenome: dict[str, list[str]],
    ) -> float:
        """Calculate local sequence divergence between subgenomes.

        Parameters
        ----------
        chrom : str
            Chromosome.
        pos : int
            Position.
        samples_by_subgenome : dict
            Samples per subgenome.

        Returns
        -------
        float
            Local divergence estimate.
        """
        # This would require looking at surrounding variants
        # For now, return a placeholder
        return 0.1

    def _index_synteny_blocks(self, blocks: list) -> None:
        """Index synteny blocks by chromosome for quick lookup.

        Parameters
        ----------
        blocks : list
            Synteny blocks to index.
        """
        self._synteny_blocks = defaultdict(list)
        for block in blocks:
            self._synteny_blocks[block.query_chrom].append(block)

        # Sort by position
        for chrom in self._synteny_blocks:
            self._synteny_blocks[chrom].sort(key=lambda x: x.query_start)

    def _find_synteny_block(self, chrom: str, pos: int) -> str | None:
        """Find synteny block containing a position.

        Parameters
        ----------
        chrom : str
            Chromosome.
        pos : int
            Position.

        Returns
        -------
        str or None
            Block ID if found.
        """
        blocks = self._synteny_blocks.get(chrom, [])
        for block in blocks:
            if block.query_start <= pos < block.query_end:
                return block.block_id
        return None

    def _find_markers_in_block(
        self,
        block,
        ref_assignments: dict[str, list[tuple[int, int, str]]],
    ) -> list[SubgenomeMarker]:
        """Find markers within a synteny block.

        This is a placeholder for alignment-based marker discovery.

        Parameters
        ----------
        block : SyntenyBlock
            Synteny block.
        ref_assignments : dict
            Reference assignments.

        Returns
        -------
        list[SubgenomeMarker]
            Markers found in block.
        """
        # Would need sequence alignment to find actual variants
        return []

    def _infer_samples_by_subgenome(
        self,
        all_samples: list[str],
        ref_assignments: dict[str, list[tuple[int, int, str]]],
    ) -> dict[str, list[str]]:
        """Infer sample-to-subgenome mapping from names.

        Parameters
        ----------
        all_samples : list[str]
            All sample names.
        ref_assignments : dict
            Reference assignments.

        Returns
        -------
        dict[str, list[str]]
            Samples per subgenome.
        """
        result: dict[str, list[str]] = {sg: [] for sg in self.config.subgenome_names}

        for sample in all_samples:
            sample_lower = sample.lower()
            for sg in self.config.subgenome_names:
                if sg.lower() in sample_lower:
                    result[sg].append(sample)
                    break

        return result


def write_markers(
    markers: list[SubgenomeMarker],
    output: Path | str,
    format: str = "tsv",
) -> None:
    """Write subgenome markers to file.

    Parameters
    ----------
    markers : list[SubgenomeMarker]
        Markers to write.
    output : Path or str
        Output file path.
    format : str
        Output format ('tsv' or 'bed').
    """
    output = Path(output)

    with open(output, "w") as f:
        if format == "bed":
            for m in markers:
                name = f"{m.ref}>{m.alt}|{','.join(f'{k}:{v}' for k, v in m.subgenome_alleles.items())}"
                score = int(m.confidence * 1000)
                f.write(f"{m.chrom}\t{m.pos}\t{m.pos + 1}\t{name}\t{score}\t.\n")
        else:
            # TSV format
            sg_names = sorted({
                sg for m in markers for sg in m.subgenome_alleles
            })
            header = ["marker_id", "chrom", "pos", "ref", "alt"]
            header.extend([f"{sg}_allele" for sg in sg_names])
            header.extend(["divergence", "synteny_block", "confidence"])
            f.write("\t".join(header) + "\n")

            for m in markers:
                row = [
                    m.marker_id,
                    m.chrom,
                    str(m.pos),
                    m.ref,
                    m.alt,
                ]
                for sg in sg_names:
                    row.append(m.subgenome_alleles.get(sg, "."))
                row.extend([
                    f"{m.divergence:.4f}",
                    m.synteny_block or ".",
                    f"{m.confidence:.3f}",
                ])
                f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {len(markers)} markers to {output}")


def load_markers(path: Path | str) -> list[SubgenomeMarker]:
    """Load subgenome markers from TSV file.

    Parameters
    ----------
    path : Path or str
        Path to markers file.

    Returns
    -------
    list[SubgenomeMarker]
        Loaded markers.
    """
    path = Path(path)
    markers = []

    with open(path) as f:
        header = None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")
            if header is None:
                header = fields
                continue

            row = dict(zip(header, fields, strict=False))

            # Extract subgenome alleles
            subgenome_alleles = {}
            for key in row:
                if key.endswith("_allele") and row[key] != ".":
                    sg = key.replace("_allele", "")
                    subgenome_alleles[sg] = row[key]

            marker = SubgenomeMarker(
                marker_id=row.get("marker_id", ""),
                chrom=row.get("chrom", ""),
                pos=int(row.get("pos", 0)),
                ref=row.get("ref", ""),
                alt=row.get("alt", ""),
                subgenome_alleles=subgenome_alleles,
                divergence=float(row.get("divergence", 0)),
                synteny_block=row.get("synteny_block") if row.get("synteny_block") != "." else None,
                confidence=float(row.get("confidence", 1.0)),
            )
            markers.append(marker)

    logger.info(f"Loaded {len(markers)} markers from {path}")
    return markers
