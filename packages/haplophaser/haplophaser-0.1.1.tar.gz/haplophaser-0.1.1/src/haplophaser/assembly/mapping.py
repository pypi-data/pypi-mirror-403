"""
Marker mapping to assembly coordinates.

Maps diagnostic markers to assembly contigs using minimap2, BLAST,
or exact sequence matching. Also supports marker hits from VCF files
called against the assembly.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.io.assembly import Assembly
    from haplophaser.markers.diagnostic import DiagnosticMarkerSet

logger = logging.getLogger(__name__)


class MappingMethod(str, Enum):
    """Method for mapping markers to assembly."""

    MINIMAP2 = "minimap2"
    BLAST = "blast"
    EXACT = "exact"
    VCF = "vcf"


@dataclass
class MarkerHit:
    """A marker hit location in the assembly.

    Parameters
    ----------
    marker_id : str
        Original marker identifier.
    contig : str
        Contig/scaffold name where marker maps.
    position : int
        0-based position in contig.
    strand : str
        Strand: '+' or '-'.
    identity : float
        Alignment identity (0-1).
    founder_alleles : dict[str, str]
        Which allele indicates which founder.
    observed_allele : str | None
        Allele observed in the assembly at this position.
    mapping_quality : int
        Mapping quality score.
    n_hits : int
        Total number of hits for this marker (1 = unique).
    is_unique : bool
        True if marker maps uniquely.
    cigar : str | None
        CIGAR string from alignment.
    ref_allele : str
        Reference allele from original marker.
    alt_allele : str
        Alternate allele from original marker.
    marker_chrom : str | None
        Original chromosome from marker definition.
    marker_pos : int | None
        Original position from marker definition (0-based).
    """

    marker_id: str
    contig: str
    position: int
    strand: str
    identity: float
    founder_alleles: dict[str, str]
    observed_allele: str | None = None
    mapping_quality: int = 60
    n_hits: int = 1
    is_unique: bool = True
    cigar: str | None = None
    ref_allele: str = ""
    alt_allele: str = ""
    marker_chrom: str | None = None
    marker_pos: int | None = None

    @property
    def position_1based(self) -> int:
        """Return 1-based position."""
        return self.position + 1

    def inferred_founder(self) -> str | None:
        """Infer founder based on observed allele.

        Returns
        -------
        str | None
            Founder name if observed allele matches a founder, None otherwise.
        """
        if self.observed_allele is None:
            return None
        for founder, allele in self.founder_alleles.items():
            if allele == self.observed_allele:
                return founder
        return None

    def to_bed_fields(self) -> tuple[str, int, int, str, int, str]:
        """Convert to BED6 format fields.

        Returns
        -------
        tuple
            (chrom, start, end, name, score, strand)
        """
        name = f"{self.marker_id}|{self.inferred_founder() or 'unknown'}"
        score = int(self.identity * 1000)
        return (self.contig, self.position, self.position + 1, name, score, self.strand)


@dataclass
class MarkerMappingResult:
    """Results of mapping markers to an assembly.

    Parameters
    ----------
    assembly_name : str
        Name of target assembly.
    total_markers : int
        Total markers attempted.
    mapped_unique : int
        Markers with unique mapping.
    mapped_multiple : int
        Markers with multiple mappings.
    unmapped : int
        Markers that didn't map.
    hits : list[MarkerHit]
        List of marker hits.
    multihit_markers : set[str]
        Marker IDs with multiple hits.
    unmapped_markers : set[str]
        Marker IDs that didn't map.
    method : MappingMethod
        Method used for mapping.
    parameters : dict
        Mapping parameters used.
    """

    assembly_name: str
    total_markers: int
    mapped_unique: int
    mapped_multiple: int
    unmapped: int
    hits: list[MarkerHit] = field(default_factory=list)
    multihit_markers: set[str] = field(default_factory=set)
    unmapped_markers: set[str] = field(default_factory=set)
    method: MappingMethod = MappingMethod.MINIMAP2
    parameters: dict = field(default_factory=dict)

    @property
    def mapping_rate(self) -> float:
        """Return fraction of markers that mapped."""
        if self.total_markers == 0:
            return 0.0
        return (self.mapped_unique + self.mapped_multiple) / self.total_markers

    @property
    def unique_mapping_rate(self) -> float:
        """Return fraction of markers that mapped uniquely."""
        if self.total_markers == 0:
            return 0.0
        return self.mapped_unique / self.total_markers

    def hits_by_contig(self, contig: str) -> list[MarkerHit]:
        """Get hits for a specific contig.

        Parameters
        ----------
        contig : str
            Contig name.

        Returns
        -------
        list[MarkerHit]
            Hits on the specified contig.
        """
        return [h for h in self.hits if h.contig == contig]

    def unique_hits(self) -> list[MarkerHit]:
        """Get only uniquely mapped hits.

        Returns
        -------
        list[MarkerHit]
            Hits with unique mapping.
        """
        return [h for h in self.hits if h.is_unique]

    def contig_coverage(self) -> dict[str, int]:
        """Count marker hits per contig.

        Returns
        -------
        dict[str, int]
            Mapping of contig name to hit count.
        """
        counts: dict[str, int] = {}
        for hit in self.hits:
            counts[hit.contig] = counts.get(hit.contig, 0) + 1
        return counts

    def summary(self) -> dict:
        """Generate mapping summary.

        Returns
        -------
        dict
            Summary statistics.
        """
        return {
            "assembly": self.assembly_name,
            "total_markers": self.total_markers,
            "mapped_unique": self.mapped_unique,
            "mapped_multiple": self.mapped_multiple,
            "unmapped": self.unmapped,
            "mapping_rate": self.mapping_rate,
            "unique_mapping_rate": self.unique_mapping_rate,
            "method": self.method.value,
            "n_contigs_with_hits": len(self.contig_coverage()),
        }


class MarkerMapper:
    """Map diagnostic markers to assembly coordinates.

    Parameters
    ----------
    method : str
        Mapping method: 'minimap2', 'blast', 'exact', or 'vcf'.
    preset : str
        Minimap2 preset for mapping.
    min_identity : float
        Minimum alignment identity (0-1).
    max_hits : int
        Maximum hits per marker (0 = unlimited).
    flank_size : int
        Size of flanking sequence to use for mapping.
    minimap2_path : str
        Path to minimap2 executable.
    """

    def __init__(
        self,
        method: str = "minimap2",
        preset: str = "sr",
        min_identity: float = 0.95,
        max_hits: int = 1,
        flank_size: int = 50,
        minimap2_path: str = "minimap2",
    ) -> None:
        self.method = MappingMethod(method)
        self.preset = preset
        self.min_identity = min_identity
        self.max_hits = max_hits
        self.flank_size = flank_size
        self.minimap2_path = minimap2_path

    def map(
        self,
        markers: DiagnosticMarkerSet,
        assembly: Assembly,
        marker_sequences: Path | str | None = None,
        reference_fasta: Path | str | None = None,
        assembly_fasta: Path | str | None = None,
    ) -> MarkerMappingResult:
        """Map markers to assembly.

        Parameters
        ----------
        markers : DiagnosticMarkerSet
            Diagnostic markers to map.
        assembly : Assembly
            Target assembly.
        marker_sequences : Path | str | None
            FASTA file with marker flank sequences.
        reference_fasta : Path | str | None
            Reference FASTA for extracting marker flanks.
        assembly_fasta : Path | str | None
            Assembly FASTA for mapping.

        Returns
        -------
        MarkerMappingResult
            Mapping results.
        """
        if self.method == MappingMethod.MINIMAP2:
            return self._map_minimap2(
                markers, assembly, marker_sequences, reference_fasta, assembly_fasta
            )
        elif self.method == MappingMethod.EXACT:
            return self._map_exact(markers, assembly, assembly_fasta)
        else:
            raise NotImplementedError(f"Mapping method {self.method} not implemented")

    def from_vcf(
        self,
        vcf_path: Path | str,
        markers: DiagnosticMarkerSet,
        assembly: Assembly,
    ) -> MarkerMappingResult:
        """Create marker hits from VCF called against assembly.

        Parameters
        ----------
        vcf_path : Path | str
            VCF file with variants called against assembly.
        markers : DiagnosticMarkerSet
            Diagnostic markers to match.
        assembly : Assembly
            Target assembly.

        Returns
        -------
        MarkerMappingResult
            Mapping results.
        """
        from haplophaser.io.vcf import iter_variants

        logger.info(f"Loading marker hits from VCF: {vcf_path}")

        # Build marker lookup by position
        marker_lookup: dict[tuple[str, int], list] = {}
        for marker in markers:
            key = (marker.chrom, marker.pos)
            if key not in marker_lookup:
                marker_lookup[key] = []
            marker_lookup[key].append(marker)

        hits: list[MarkerHit] = []
        hit_marker_ids: set[str] = set()
        hit_counts: dict[str, int] = {}

        for variant in iter_variants(vcf_path):
            key = (variant.chrom, variant.pos)
            if key in marker_lookup:
                for marker in marker_lookup[key]:
                    # Get observed allele from assembly (assuming haploid/homozygous)
                    # For VCF against assembly, REF is what's in assembly
                    observed = variant.ref

                    hit = MarkerHit(
                        marker_id=marker.variant_id,
                        contig=variant.chrom,
                        position=variant.pos,
                        strand="+",
                        identity=1.0,
                        founder_alleles=marker.founder_alleles,
                        observed_allele=observed,
                        ref_allele=marker.ref,
                        alt_allele=marker.alt,
                        marker_chrom=marker.chrom,
                        marker_pos=marker.pos,
                    )
                    hits.append(hit)
                    hit_marker_ids.add(marker.variant_id)
                    hit_counts[marker.variant_id] = hit_counts.get(marker.variant_id, 0) + 1

        # Identify multi-hit and unique markers
        multihit_markers = {mid for mid, count in hit_counts.items() if count > 1}
        for hit in hits:
            hit.n_hits = hit_counts[hit.marker_id]
            hit.is_unique = hit.n_hits == 1

        # Identify unmapped markers
        all_marker_ids = {m.variant_id for m in markers}
        unmapped_markers = all_marker_ids - hit_marker_ids

        result = MarkerMappingResult(
            assembly_name=assembly.name,
            total_markers=len(markers),
            mapped_unique=len(hit_marker_ids - multihit_markers),
            mapped_multiple=len(multihit_markers),
            unmapped=len(unmapped_markers),
            hits=hits,
            multihit_markers=multihit_markers,
            unmapped_markers=unmapped_markers,
            method=MappingMethod.VCF,
            parameters={"vcf_path": str(vcf_path)},
        )

        logger.info(
            f"Loaded {len(hits)} marker hits from VCF "
            f"({result.mapped_unique} unique, {result.mapped_multiple} multi-hit, "
            f"{result.unmapped} unmapped)"
        )

        return result

    def _map_minimap2(
        self,
        markers: DiagnosticMarkerSet,
        assembly: Assembly,
        marker_sequences: Path | str | None,
        reference_fasta: Path | str | None,
        assembly_fasta: Path | str | None,
    ) -> MarkerMappingResult:
        """Map markers using minimap2."""
        if assembly_fasta is None:
            raise ValueError("assembly_fasta required for minimap2 mapping")

        assembly_fasta = Path(assembly_fasta)

        # Create marker sequences FASTA if not provided
        if marker_sequences is None:
            if reference_fasta is None:
                raise ValueError(
                    "Either marker_sequences or reference_fasta required"
                )
            marker_sequences = self._extract_marker_flanks(markers, reference_fasta)
            cleanup_marker_seqs = True
        else:
            marker_sequences = Path(marker_sequences)
            cleanup_marker_seqs = False

        logger.info(f"Mapping markers to assembly using minimap2 (preset={self.preset})")

        # Run minimap2
        with tempfile.NamedTemporaryFile(mode="w", suffix=".paf", delete=False) as paf_file:
            paf_path = paf_file.name

        cmd = [
            self.minimap2_path,
            "-x", self.preset,
            "-c",  # Output CIGAR
            "--secondary=yes" if self.max_hits != 1 else "--secondary=no",
            "-o", paf_path,
            str(assembly_fasta),
            str(marker_sequences),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"minimap2 failed: {result.stderr}")
            raise RuntimeError(f"minimap2 failed: {result.stderr}")

        # Parse PAF output
        hits = self._parse_paf(paf_path, markers)

        # Cleanup
        Path(paf_path).unlink()
        if cleanup_marker_seqs:
            Path(marker_sequences).unlink()

        # Build result
        hit_counts: dict[str, int] = {}
        for hit in hits:
            hit_counts[hit.marker_id] = hit_counts.get(hit.marker_id, 0) + 1

        multihit_markers = {mid for mid, count in hit_counts.items() if count > 1}
        hit_marker_ids = set(hit_counts.keys())
        all_marker_ids = {m.variant_id for m in markers}
        unmapped_markers = all_marker_ids - hit_marker_ids

        # Update hit metadata
        for hit in hits:
            hit.n_hits = hit_counts[hit.marker_id]
            hit.is_unique = hit.n_hits == 1

        # Filter by max_hits
        if self.max_hits > 0:
            filtered_hits = []
            seen: dict[str, int] = {}
            for hit in hits:
                if seen.get(hit.marker_id, 0) < self.max_hits:
                    filtered_hits.append(hit)
                    seen[hit.marker_id] = seen.get(hit.marker_id, 0) + 1
            hits = filtered_hits

        result = MarkerMappingResult(
            assembly_name=assembly.name,
            total_markers=len(markers),
            mapped_unique=len(hit_marker_ids - multihit_markers),
            mapped_multiple=len(multihit_markers),
            unmapped=len(unmapped_markers),
            hits=hits,
            multihit_markers=multihit_markers,
            unmapped_markers=unmapped_markers,
            method=MappingMethod.MINIMAP2,
            parameters={
                "preset": self.preset,
                "min_identity": self.min_identity,
                "max_hits": self.max_hits,
            },
        )

        logger.info(
            f"Mapped {len(hits)} marker hits "
            f"({result.mapped_unique} unique, {result.mapped_multiple} multi-hit, "
            f"{result.unmapped} unmapped)"
        )

        return result

    def _parse_paf(
        self,
        paf_path: str,
        markers: DiagnosticMarkerSet,
    ) -> list[MarkerHit]:
        """Parse PAF alignment file.

        Parameters
        ----------
        paf_path : str
            Path to PAF file.
        markers : DiagnosticMarkerSet
            Markers for looking up founder alleles.

        Returns
        -------
        list[MarkerHit]
            Parsed marker hits.
        """
        # Build marker lookup
        marker_lookup = {m.variant_id: m for m in markers}

        hits: list[MarkerHit] = []

        with open(paf_path) as f:
            for line in f:
                fields = line.strip().split("\t")
                if len(fields) < 12:
                    continue

                query_name = fields[0]  # Marker ID
                int(fields[1])
                target_name = fields[5]  # Contig
                int(fields[6])
                target_start = int(fields[7])  # 0-based
                target_end = int(fields[8])
                strand = fields[4]
                matches = int(fields[9])
                block_len = int(fields[10])
                mapq = int(fields[11])

                # Calculate identity
                identity = matches / block_len if block_len > 0 else 0.0

                # Filter by identity
                if identity < self.min_identity:
                    continue

                # Get CIGAR if present
                cigar = None
                for tag in fields[12:]:
                    if tag.startswith("cg:Z:"):
                        cigar = tag[5:]
                        break

                # Look up marker
                marker = marker_lookup.get(query_name)
                founder_alleles = marker.founder_alleles if marker else {}

                # Calculate position (center of alignment on target)
                position = target_start + (target_end - target_start) // 2

                hit = MarkerHit(
                    marker_id=query_name,
                    contig=target_name,
                    position=position,
                    strand=strand,
                    identity=identity,
                    founder_alleles=founder_alleles,
                    mapping_quality=mapq,
                    cigar=cigar,
                    ref_allele=marker.ref if marker else "",
                    alt_allele=marker.alt if marker else "",
                    marker_chrom=marker.chrom if marker else None,
                    marker_pos=marker.pos if marker else None,
                )
                hits.append(hit)

        return hits

    def _map_exact(
        self,
        markers: DiagnosticMarkerSet,
        assembly: Assembly,
        assembly_fasta: Path | str | None,
    ) -> MarkerMappingResult:
        """Map markers using exact sequence matching."""
        from haplophaser.io.assembly import iter_fasta

        if assembly_fasta is None:
            raise ValueError("assembly_fasta required for exact mapping")

        logger.info("Mapping markers using exact sequence matching")

        hits: list[MarkerHit] = []
        hit_counts: dict[str, int] = {}

        # Build search patterns from marker context
        # This requires markers to have sequence context
        marker_patterns: dict[str, tuple[str, str, str]] = {}
        for marker in markers:
            # Pattern: [ref|alt] at position
            marker_patterns[marker.variant_id] = (marker.ref, marker.alt, marker.variant_id)

        # Scan assembly sequences
        for contig_name, sequence in iter_fasta(assembly_fasta):
            sequence = sequence.upper()

            for marker in markers:
                # Simple exact match - find ref or alt in sequence
                # This is a simplified approach; real implementation would use
                # flanking sequences for context
                ref_positions = self._find_all(sequence, marker.ref)
                alt_positions = self._find_all(sequence, marker.alt)

                for pos in ref_positions:
                    hit = MarkerHit(
                        marker_id=marker.variant_id,
                        contig=contig_name,
                        position=pos,
                        strand="+",
                        identity=1.0,
                        founder_alleles=marker.founder_alleles,
                        observed_allele=marker.ref,
                        ref_allele=marker.ref,
                        alt_allele=marker.alt,
                        marker_chrom=marker.chrom,
                        marker_pos=marker.pos,
                    )
                    hits.append(hit)
                    hit_counts[marker.variant_id] = hit_counts.get(marker.variant_id, 0) + 1

                for pos in alt_positions:
                    hit = MarkerHit(
                        marker_id=marker.variant_id,
                        contig=contig_name,
                        position=pos,
                        strand="+",
                        identity=1.0,
                        founder_alleles=marker.founder_alleles,
                        observed_allele=marker.alt,
                        ref_allele=marker.ref,
                        alt_allele=marker.alt,
                        marker_chrom=marker.chrom,
                        marker_pos=marker.pos,
                    )
                    hits.append(hit)
                    hit_counts[marker.variant_id] = hit_counts.get(marker.variant_id, 0) + 1

        # Finalize results
        multihit_markers = {mid for mid, count in hit_counts.items() if count > 1}
        hit_marker_ids = set(hit_counts.keys())
        all_marker_ids = {m.variant_id for m in markers}
        unmapped_markers = all_marker_ids - hit_marker_ids

        for hit in hits:
            hit.n_hits = hit_counts.get(hit.marker_id, 1)
            hit.is_unique = hit.n_hits == 1

        return MarkerMappingResult(
            assembly_name=assembly.name,
            total_markers=len(markers),
            mapped_unique=len(hit_marker_ids - multihit_markers),
            mapped_multiple=len(multihit_markers),
            unmapped=len(unmapped_markers),
            hits=hits,
            multihit_markers=multihit_markers,
            unmapped_markers=unmapped_markers,
            method=MappingMethod.EXACT,
            parameters={"min_identity": self.min_identity},
        )

    def _find_all(self, sequence: str, pattern: str) -> list[int]:
        """Find all occurrences of pattern in sequence.

        Parameters
        ----------
        sequence : str
            Sequence to search.
        pattern : str
            Pattern to find.

        Returns
        -------
        list[int]
            0-based positions of all matches.
        """
        positions = []
        start = 0
        while True:
            pos = sequence.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions

    def _extract_marker_flanks(
        self,
        markers: DiagnosticMarkerSet,
        reference_fasta: Path | str,
    ) -> Path:
        """Extract flanking sequences around markers.

        Parameters
        ----------
        markers : DiagnosticMarkerSet
            Markers to extract flanks for.
        reference_fasta : Path | str
            Reference FASTA to extract from.

        Returns
        -------
        Path
            Path to temporary FASTA with marker flanks.
        """
        from haplophaser.io.assembly import iter_fasta

        reference_fasta = Path(reference_fasta)
        logger.info(f"Extracting marker flanks from {reference_fasta}")

        # Load reference sequences by chromosome
        ref_seqs: dict[str, str] = {}
        for name, seq in iter_fasta(reference_fasta):
            ref_seqs[name] = seq

        # Extract flanks
        flanks: dict[str, str] = {}
        for marker in markers:
            if marker.chrom not in ref_seqs:
                logger.warning(f"Chromosome {marker.chrom} not in reference")
                continue

            seq = ref_seqs[marker.chrom]
            start = max(0, marker.pos - self.flank_size)
            end = min(len(seq), marker.pos + len(marker.ref) + self.flank_size)

            flank_seq = seq[start:end]
            flanks[marker.variant_id] = flank_seq

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fa", delete=False
        ) as tmp:
            for marker_id, flank_seq in flanks.items():
                tmp.write(f">{marker_id}\n{flank_seq}\n")
            return Path(tmp.name)


def load_marker_hits(path: Path | str) -> list[MarkerHit]:
    """Load marker hits from TSV file.

    Parameters
    ----------
    path : Path | str
        Path to marker hits TSV file.

    Returns
    -------
    list[MarkerHit]
        Loaded marker hits.
    """
    path = Path(path)
    logger.info(f"Loading marker hits from {path}")

    hits: list[MarkerHit] = []
    header: dict[str, int] | None = None

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")

            if header is None:
                header = {col: i for i, col in enumerate(fields)}
                continue

            # Parse required fields
            marker_id = fields[header["marker_id"]]
            contig = fields[header["contig"]]
            position = int(fields[header["position"]])
            strand = fields[header.get("strand", 0)] if "strand" in header else "+"
            identity = float(fields[header["identity"]]) if "identity" in header else 1.0

            # Parse optional fields
            observed_allele = (
                fields[header["observed_allele"]]
                if "observed_allele" in header and fields[header["observed_allele"]]
                else None
            )

            # Parse founder alleles (format: founder1:allele1;founder2:allele2)
            founder_alleles: dict[str, str] = {}
            if "founder_alleles" in header and fields[header["founder_alleles"]]:
                for pair in fields[header["founder_alleles"]].split(";"):
                    if ":" in pair:
                        founder, allele = pair.split(":", 1)
                        founder_alleles[founder] = allele

            hit = MarkerHit(
                marker_id=marker_id,
                contig=contig,
                position=position,
                strand=strand,
                identity=identity,
                founder_alleles=founder_alleles,
                observed_allele=observed_allele,
                mapping_quality=int(fields[header.get("mapping_quality", 60)]) if "mapping_quality" in header else 60,
                n_hits=int(fields[header.get("n_hits", 1)]) if "n_hits" in header else 1,
                is_unique=fields[header.get("is_unique", "true")].lower() == "true" if "is_unique" in header else True,
                ref_allele=fields[header.get("ref_allele", "")] if "ref_allele" in header else "",
                alt_allele=fields[header.get("alt_allele", "")] if "alt_allele" in header else "",
            )
            hits.append(hit)

    logger.info(f"Loaded {len(hits)} marker hits")
    return hits


def export_marker_hits_tsv(
    hits: list[MarkerHit] | MarkerMappingResult,
    path: Path | str,
) -> Path:
    """Export marker hits to TSV file.

    Parameters
    ----------
    hits : list[MarkerHit] | MarkerMappingResult
        Marker hits to export.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting marker hits to {path}")

    if isinstance(hits, MarkerMappingResult):
        hits = hits.hits

    columns = [
        "marker_id",
        "contig",
        "position",
        "strand",
        "identity",
        "observed_allele",
        "inferred_founder",
        "founder_alleles",
        "ref_allele",
        "alt_allele",
        "mapping_quality",
        "n_hits",
        "is_unique",
        "marker_chrom",
        "marker_pos",
    ]

    with open(path, "w") as f:
        f.write("\t".join(columns) + "\n")

        for hit in hits:
            founder_alleles_str = ";".join(
                f"{k}:{v}" for k, v in hit.founder_alleles.items()
            )
            row = [
                hit.marker_id,
                hit.contig,
                str(hit.position),
                hit.strand,
                f"{hit.identity:.4f}",
                hit.observed_allele or "",
                hit.inferred_founder() or "",
                founder_alleles_str,
                hit.ref_allele,
                hit.alt_allele,
                str(hit.mapping_quality),
                str(hit.n_hits),
                str(hit.is_unique).lower(),
                hit.marker_chrom or "",
                str(hit.marker_pos) if hit.marker_pos is not None else "",
            ]
            f.write("\t".join(row) + "\n")

    return path


def export_marker_hits_bed(
    hits: list[MarkerHit] | MarkerMappingResult,
    path: Path | str,
    track_name: str = "marker_hits",
) -> Path:
    """Export marker hits to BED file.

    Parameters
    ----------
    hits : list[MarkerHit] | MarkerMappingResult
        Marker hits to export.
    path : Path | str
        Output path.
    track_name : str
        BED track name.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting marker hits to BED: {path}")

    if isinstance(hits, MarkerMappingResult):
        hits = hits.hits

    with open(path, "w") as f:
        f.write(f'track name="{track_name}" description="Marker hits on assembly"\n')

        for hit in hits:
            chrom, start, end, name, score, strand = hit.to_bed_fields()
            f.write(f"{chrom}\t{start}\t{end}\t{name}\t{score}\t{strand}\n")

    return path
