"""
Synteny file parsing utilities.

Parses output from various synteny detection tools:
- SyRI (Structural Rearrangement Identifier)
- MCScanX
- GENESPACE
- minimap2/PAF format
- Custom TSV format

All coordinates are converted to 0-based, half-open intervals.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SyntenyFormat(str, Enum):
    """Supported synteny file formats."""

    SYRI = "syri"
    MCSCANX = "mcscanx"
    GENESPACE = "genespace"
    PAF = "paf"
    TSV = "tsv"
    AUTO = "auto"


@dataclass
class SyntenyBlock:
    """A block of synteny between query and reference.

    All coordinates are 0-based, half-open.

    Parameters
    ----------
    query_chrom : str
        Query chromosome/contig.
    query_start : int
        Query start (0-based).
    query_end : int
        Query end (exclusive).
    ref_chrom : str
        Reference chromosome.
    ref_start : int
        Reference start (0-based).
    ref_end : int
        Reference end (exclusive).
    orientation : str
        '+' for same strand, '-' for inverted.
    n_anchors : int
        Number of anchor genes/markers.
    identity : float
        Sequence identity (0-1).
    block_id : str, optional
        Block identifier.
    block_type : str, optional
        Block type (e.g., 'SYNAL' for syntenic alignment).
    """

    query_chrom: str
    query_start: int
    query_end: int
    ref_chrom: str
    ref_start: int
    ref_end: int
    orientation: str = "+"
    n_anchors: int = 0
    identity: float = 0.0
    block_id: str | None = None
    block_type: str | None = None

    @property
    def query_length(self) -> int:
        """Return query region length."""
        return self.query_end - self.query_start

    @property
    def ref_length(self) -> int:
        """Return reference region length."""
        return self.ref_end - self.ref_start

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_chrom": self.query_chrom,
            "query_start": self.query_start,
            "query_end": self.query_end,
            "ref_chrom": self.ref_chrom,
            "ref_start": self.ref_start,
            "ref_end": self.ref_end,
            "orientation": self.orientation,
            "n_anchors": self.n_anchors,
            "identity": self.identity,
            "block_id": self.block_id,
            "block_type": self.block_type,
        }


def detect_synteny_format(path: Path | str) -> SyntenyFormat:
    """Detect synteny file format from content.

    Parameters
    ----------
    path : Path or str
        Path to synteny file.

    Returns
    -------
    SyntenyFormat
        Detected format.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    # Check by extension first
    if suffix == ".paf":
        return SyntenyFormat.PAF

    # Read first few lines to detect format
    with open(path) as f:
        lines = []
        for i, line in enumerate(f):
            if i >= 20:
                break
            lines.append(line.strip())

    # Check for SyRI format (has specific column headers or type annotations)
    if any("SYNAL" in line or "SYNTR" in line or "INV" in line for line in lines):
        return SyntenyFormat.SYRI

    # Check for MCScanX format (starts with ## header and Alignment blocks)
    if any(line.startswith("## Alignment") for line in lines):
        return SyntenyFormat.MCSCANX

    # Check for GENESPACE format (specific column headers)
    if lines and any(
        "og" in lines[0].lower() and "chr" in lines[0].lower()
        for _ in [1]
    ):
        return SyntenyFormat.GENESPACE

    # Check for PAF format (12+ tab-separated fields, specific pattern)
    if lines:
        first_data = lines[0].split("\t")
        if len(first_data) >= 12:
            try:
                # PAF has specific numeric fields at positions 1,2,3,6,7,8
                int(first_data[1])
                int(first_data[2])
                int(first_data[3])
                return SyntenyFormat.PAF
            except (ValueError, IndexError):
                pass

    # Default to TSV
    return SyntenyFormat.TSV


def load_synteny(
    path: Path | str,
    format: SyntenyFormat | str = SyntenyFormat.AUTO,
    min_length: int = 0,
    min_anchors: int = 0,
    min_identity: float = 0.0,
) -> list[SyntenyBlock]:
    """Load synteny blocks from file.

    Parameters
    ----------
    path : Path or str
        Path to synteny file.
    format : SyntenyFormat or str
        File format (auto-detected if not specified).
    min_length : int
        Minimum block length to include.
    min_anchors : int
        Minimum anchor count to include.
    min_identity : float
        Minimum identity to include.

    Returns
    -------
    list[SyntenyBlock]
        Parsed synteny blocks.

    Examples
    --------
    >>> blocks = load_synteny("synteny.paf", min_length=10000)
    >>> print(f"Loaded {len(blocks)} synteny blocks")
    """
    path = Path(path)

    if isinstance(format, str):
        format = SyntenyFormat(format)

    if format == SyntenyFormat.AUTO:
        format = detect_synteny_format(path)
        logger.info(f"Detected synteny format: {format.value}")

    # Parse based on format
    if format == SyntenyFormat.PAF:
        blocks = list(_parse_paf(path))
    elif format == SyntenyFormat.SYRI:
        blocks = list(_parse_syri(path))
    elif format == SyntenyFormat.MCSCANX:
        blocks = list(_parse_mcscanx(path))
    elif format == SyntenyFormat.GENESPACE:
        blocks = list(_parse_genespace(path))
    else:
        blocks = list(_parse_tsv(path))

    # Apply filters
    filtered = []
    for block in blocks:
        if block.query_length < min_length and block.ref_length < min_length:
            continue
        if block.n_anchors < min_anchors:
            continue
        if block.identity < min_identity:
            continue
        filtered.append(block)

    logger.info(f"Loaded {len(filtered)} synteny blocks from {path}")
    return filtered


def _parse_paf(path: Path) -> Iterator[SyntenyBlock]:
    """Parse PAF (minimap2) format.

    PAF format columns:
    0: query name
    1: query length
    2: query start (0-based)
    3: query end (exclusive)
    4: strand (+/-)
    5: target name
    6: target length
    7: target start (0-based)
    8: target end (exclusive)
    9: number of matching bases
    10: alignment block length
    11: mapping quality

    Parameters
    ----------
    path : Path
        Path to PAF file.

    Yields
    ------
    SyntenyBlock
        Parsed blocks.
    """
    block_id = 0
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) < 12:
                continue

            try:
                query_chrom = fields[0]
                query_start = int(fields[2])
                query_end = int(fields[3])
                strand = fields[4]
                ref_chrom = fields[5]
                ref_start = int(fields[7])
                ref_end = int(fields[8])
                n_matches = int(fields[9])
                block_len = int(fields[10])

                # Calculate identity
                identity = n_matches / block_len if block_len > 0 else 0.0

                block_id += 1
                yield SyntenyBlock(
                    query_chrom=query_chrom,
                    query_start=query_start,
                    query_end=query_end,
                    ref_chrom=ref_chrom,
                    ref_start=ref_start,
                    ref_end=ref_end,
                    orientation=strand,
                    n_anchors=0,
                    identity=identity,
                    block_id=f"PAF_{block_id}",
                    block_type="alignment",
                )
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse PAF line: {e}")
                continue


def _parse_syri(path: Path) -> Iterator[SyntenyBlock]:
    """Parse SyRI output format.

    SyRI output has columns:
    ref_chrom, ref_start, ref_end, seq, seq_strand,
    query_chrom, query_start, query_end, seq, seq_strand,
    type, parent_type, annotation

    Parameters
    ----------
    path : Path
        Path to SyRI output file.

    Yields
    ------
    SyntenyBlock
        Parsed syntenic blocks.
    """
    block_id = 0
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) < 11:
                continue

            # Only process syntenic alignments
            block_type = fields[10] if len(fields) > 10 else ""
            if block_type not in ("SYNAL", "SYN", "SYNTR"):
                continue

            try:
                ref_chrom = fields[0]
                ref_start = int(fields[1]) - 1  # Convert to 0-based
                ref_end = int(fields[2])
                query_chrom = fields[5]
                query_start = int(fields[6]) - 1  # Convert to 0-based
                query_end = int(fields[7])

                # Determine orientation from strand info
                ref_strand = fields[4] if len(fields) > 4 else "+"
                query_strand = fields[9] if len(fields) > 9 else "+"
                orientation = "+" if ref_strand == query_strand else "-"

                block_id += 1
                yield SyntenyBlock(
                    query_chrom=query_chrom,
                    query_start=query_start,
                    query_end=query_end,
                    ref_chrom=ref_chrom,
                    ref_start=ref_start,
                    ref_end=ref_end,
                    orientation=orientation,
                    n_anchors=0,
                    identity=0.0,
                    block_id=f"SyRI_{block_id}",
                    block_type=block_type,
                )
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse SyRI line: {e}")
                continue


def _parse_mcscanx(path: Path) -> Iterator[SyntenyBlock]:
    """Parse MCScanX collinearity format.

    MCScanX format has alignment blocks like:
    ## Alignment 0: score=1234.0 e_value=0 N=50 ...
    0- 0: gene1 gene2  0

    Parameters
    ----------
    path : Path
        Path to MCScanX collinearity file.

    Yields
    ------
    SyntenyBlock
        Parsed syntenic blocks (summarized from gene pairs).
    """
    current_block_id: str | None = None
    current_genes: list[tuple[str, str]] = []
    block_info: dict[str, Any] = {}

    with open(path) as f:
        for line in f:
            line = line.strip()

            # Block header
            if line.startswith("## Alignment"):
                # Yield previous block if exists
                if current_block_id and current_genes:
                    yield _mcscanx_genes_to_block(
                        current_block_id, current_genes, block_info
                    )

                # Parse new block header
                parts = line.split()
                current_block_id = parts[2].rstrip(":") if len(parts) > 2 else None
                current_genes = []
                block_info = {"n_genes": 0}

                # Extract N (number of genes) if present
                for part in parts:
                    if part.startswith("N="):
                        with contextlib.suppress(ValueError):
                            block_info["n_genes"] = int(part[2:])

            # Gene pair line
            elif current_block_id and "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    gene1 = parts[0].split()[-1] if parts[0] else ""
                    gene2 = parts[1].strip()
                    if gene1 and gene2:
                        current_genes.append((gene1, gene2))

        # Yield last block
        if current_block_id and current_genes:
            yield _mcscanx_genes_to_block(current_block_id, current_genes, block_info)


def _mcscanx_genes_to_block(
    block_id: str,
    genes: list[tuple[str, str]],
    info: dict[str, Any],
) -> SyntenyBlock:
    """Convert MCScanX gene pairs to a SyntenyBlock.

    Note: This requires gene coordinate information to be accurate.
    Without it, we use placeholder coordinates.

    Parameters
    ----------
    block_id : str
        Block identifier.
    genes : list[tuple[str, str]]
        Gene pairs in block.
    info : dict
        Block info from header.

    Returns
    -------
    SyntenyBlock
        Summarized block.
    """
    # Extract chromosome from first genes (assuming format like chr1g00010)
    query_chrom = "unknown"
    ref_chrom = "unknown"

    if genes:
        # Try to extract chromosome from gene names
        gene1, gene2 = genes[0]
        # Common patterns: chr1g00010, Zm00001d001234, etc.
        for prefix in ("chr", "Chr", "scaffold"):
            if prefix in gene1:
                idx = gene1.find(prefix)
                end_idx = idx
                for i, c in enumerate(gene1[idx:]):
                    if c.isdigit():
                        end_idx = idx + i
                        break
                # Find end of chromosome name
                for i, c in enumerate(gene1[end_idx:]):
                    if not c.isdigit():
                        query_chrom = gene1[idx : end_idx + i]
                        break
                else:
                    query_chrom = gene1[idx:]
                break

    return SyntenyBlock(
        query_chrom=query_chrom,
        query_start=0,
        query_end=0,
        ref_chrom=ref_chrom,
        ref_start=0,
        ref_end=0,
        orientation="+",
        n_anchors=len(genes),
        identity=0.0,
        block_id=f"MCScanX_{block_id}",
        block_type="collinear",
    )


def _parse_genespace(path: Path) -> Iterator[SyntenyBlock]:
    """Parse GENESPACE synteny output.

    GENESPACE produces TSV files with columns like:
    og, chr1, start1, end1, chr2, start2, end2, ...

    Parameters
    ----------
    path : Path
        Path to GENESPACE output file.

    Yields
    ------
    SyntenyBlock
        Parsed blocks.
    """
    block_id = 0
    header: list[str] = []

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            fields = line.split("\t")

            # First line is header
            if not header:
                header = [h.lower() for h in fields]
                continue

            try:
                row = dict(zip(header, fields, strict=False))

                # Look for expected columns
                query_chrom = row.get("chr2", row.get("qchr", ""))
                ref_chrom = row.get("chr1", row.get("rchr", ""))

                query_start = int(row.get("start2", row.get("qstart", 0)))
                query_end = int(row.get("end2", row.get("qend", 0)))
                ref_start = int(row.get("start1", row.get("rstart", 0)))
                ref_end = int(row.get("end1", row.get("rend", 0)))

                # Convert to 0-based if positions look 1-based
                if query_start >= 1:
                    query_start -= 1
                if ref_start >= 1:
                    ref_start -= 1

                strand = row.get("strand", row.get("orient", "+"))

                block_id += 1
                yield SyntenyBlock(
                    query_chrom=query_chrom,
                    query_start=query_start,
                    query_end=query_end,
                    ref_chrom=ref_chrom,
                    ref_start=ref_start,
                    ref_end=ref_end,
                    orientation=strand,
                    n_anchors=1,
                    identity=0.0,
                    block_id=f"GS_{block_id}",
                    block_type="orthogroup",
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse GENESPACE line: {e}")
                continue


def _parse_tsv(path: Path) -> Iterator[SyntenyBlock]:
    """Parse generic TSV synteny format.

    Expected columns (header required):
    query_chrom, query_start, query_end, ref_chrom, ref_start, ref_end

    Optional: orientation, n_anchors, identity, block_id

    Parameters
    ----------
    path : Path
        Path to TSV file.

    Yields
    ------
    SyntenyBlock
        Parsed blocks.
    """
    block_count = 0
    header: list[str] = []

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")

            # First non-comment line is header
            if not header:
                header = [h.lower().replace(" ", "_") for h in fields]
                continue

            try:
                row = dict(zip(header, fields, strict=False))

                query_chrom = row.get("query_chrom", row.get("qchrom", row.get("chr1", "")))
                ref_chrom = row.get("ref_chrom", row.get("rchrom", row.get("chr2", "")))

                query_start = int(row.get("query_start", row.get("qstart", row.get("start1", 0))))
                query_end = int(row.get("query_end", row.get("qend", row.get("end1", 0))))
                ref_start = int(row.get("ref_start", row.get("rstart", row.get("start2", 0))))
                ref_end = int(row.get("ref_end", row.get("rend", row.get("end2", 0))))

                orientation = row.get("orientation", row.get("strand", row.get("orient", "+")))
                n_anchors = int(row.get("n_anchors", row.get("anchors", row.get("n_genes", 0))))
                identity = float(row.get("identity", row.get("pident", 0)))
                block_id = row.get("block_id", row.get("id"))

                # Normalize identity to 0-1 range if percentage
                if identity > 1:
                    identity /= 100.0

                block_count += 1
                yield SyntenyBlock(
                    query_chrom=query_chrom,
                    query_start=query_start,
                    query_end=query_end,
                    ref_chrom=ref_chrom,
                    ref_start=ref_start,
                    ref_end=ref_end,
                    orientation=orientation,
                    n_anchors=n_anchors,
                    identity=identity,
                    block_id=block_id or f"TSV_{block_count}",
                    block_type="syntenic",
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse TSV line: {e}")
                continue


def load_reference_assignments(
    path: Path | str,
) -> dict[str, list[tuple[int, int, str]]]:
    """Load known subgenome assignments from BED file.

    Parameters
    ----------
    path : Path or str
        Path to BED file with subgenome assignments.
        Expected columns: chrom, start, end, subgenome

    Returns
    -------
    dict[str, list[tuple[int, int, str]]]
        Mapping of chromosome to list of (start, end, subgenome) tuples.

    Examples
    --------
    >>> assignments = load_reference_assignments("B73_subgenomes.bed")
    >>> for start, end, sg in assignments["chr1"]:
    ...     print(f"{start}-{end}: {sg}")
    """
    path = Path(path)
    assignments: dict[str, list[tuple[int, int, str]]] = {}

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("track"):
                continue

            fields = line.split("\t")
            if len(fields) < 4:
                continue

            chrom = fields[0]
            start = int(fields[1])
            end = int(fields[2])
            subgenome = fields[3]

            if chrom not in assignments:
                assignments[chrom] = []
            assignments[chrom].append((start, end, subgenome))

    # Sort by position
    for chrom in assignments:
        assignments[chrom].sort(key=lambda x: x[0])

    total_regions = sum(len(v) for v in assignments.values())
    logger.info(f"Loaded {total_regions} subgenome assignments from {path}")

    return assignments


def write_synteny_blocks(
    blocks: list[SyntenyBlock],
    path: Path | str,
    format: str = "tsv",
) -> None:
    """Write synteny blocks to file.

    Parameters
    ----------
    blocks : list[SyntenyBlock]
        Blocks to write.
    path : Path or str
        Output path.
    format : str
        Output format: 'tsv' or 'bed'.
    """
    path = Path(path)

    with open(path, "w") as f:
        if format == "bed":
            # BED format (query coordinates)
            for block in blocks:
                name = f"{block.ref_chrom}:{block.ref_start}-{block.ref_end}"
                score = int(block.identity * 1000)
                f.write(
                    f"{block.query_chrom}\t{block.query_start}\t{block.query_end}\t"
                    f"{name}\t{score}\t{block.orientation}\n"
                )
        else:
            # TSV format
            header = [
                "query_chrom", "query_start", "query_end",
                "ref_chrom", "ref_start", "ref_end",
                "orientation", "n_anchors", "identity", "block_id",
            ]
            f.write("\t".join(header) + "\n")

            for block in blocks:
                row = [
                    block.query_chrom,
                    str(block.query_start),
                    str(block.query_end),
                    block.ref_chrom,
                    str(block.ref_start),
                    str(block.ref_end),
                    block.orientation,
                    str(block.n_anchors),
                    f"{block.identity:.4f}",
                    block.block_id or "",
                ]
                f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {len(blocks)} synteny blocks to {path}")
