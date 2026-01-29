"""
Assembly file I/O for Phaser.

Handles reading assembly files (FASTA, FAI, AGP) and provides
Assembly and Contig dataclasses for assembly-centric analysis.
"""

from __future__ import annotations

import gzip
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.assembly.mapping import MarkerHit

logger = logging.getLogger(__name__)


@dataclass
class Contig:
    """A contig or scaffold in an assembly.

    Parameters
    ----------
    name : str
        Contig identifier.
    length : int
        Contig length in base pairs.
    sequence : str | None
        Sequence data, loaded on demand.
    haplotype : str | None
        Assigned founder haplotype.
    subgenome : str | None
        Assigned subgenome (for allopolyploids).
    confidence : float | None
        Assignment confidence (0-1).
    markers : list[MarkerHit] | None
        Marker hits on this contig.
    """

    name: str
    length: int
    sequence: str | None = None
    haplotype: str | None = None
    subgenome: str | None = None
    confidence: float | None = None
    markers: list[MarkerHit] | None = None

    @property
    def has_sequence(self) -> bool:
        """Return True if sequence data is loaded."""
        return self.sequence is not None

    @property
    def gc_content(self) -> float | None:
        """Calculate GC content if sequence is available."""
        if self.sequence is None:
            return None
        seq = self.sequence.upper()
        gc = seq.count("G") + seq.count("C")
        total = len(seq) - seq.count("N")
        return gc / total if total > 0 else 0.0

    @property
    def n_count(self) -> int | None:
        """Count N bases if sequence is available."""
        if self.sequence is None:
            return None
        return self.sequence.upper().count("N")


@dataclass
class ScaffoldComponent:
    """A component of a scaffold as defined in AGP format.

    Parameters
    ----------
    scaffold : str
        Parent scaffold name.
    scaffold_start : int
        Start position in scaffold (0-based).
    scaffold_end : int
        End position in scaffold (0-based, exclusive).
    component_num : int
        Component number within scaffold.
    component_type : str
        Type: 'W' (WGS contig), 'D' (draft), 'N' (gap), 'U' (gap unknown).
    component_id : str | None
        Component identifier (contig name for non-gap).
    component_start : int | None
        Start in component (0-based).
    component_end : int | None
        End in component (0-based, exclusive).
    orientation : str
        Orientation: '+', '-', or '?' for unknown.
    gap_length : int | None
        Gap length if component_type in ('N', 'U').
    gap_type : str | None
        Gap type (scaffold, contig, etc.).
    linkage : bool | None
        Whether gap is linked.
    linkage_evidence : str | None
        Evidence for linkage.
    """

    scaffold: str
    scaffold_start: int
    scaffold_end: int
    component_num: int
    component_type: str
    component_id: str | None = None
    component_start: int | None = None
    component_end: int | None = None
    orientation: str = "+"
    gap_length: int | None = None
    gap_type: str | None = None
    linkage: bool | None = None
    linkage_evidence: str | None = None

    @property
    def is_gap(self) -> bool:
        """Return True if this component is a gap."""
        return self.component_type in ("N", "U")

    @property
    def length(self) -> int:
        """Return component length."""
        return self.scaffold_end - self.scaffold_start


@dataclass
class Scaffold:
    """A scaffold composed of contigs and gaps.

    Parameters
    ----------
    name : str
        Scaffold identifier.
    length : int
        Total scaffold length.
    components : list[ScaffoldComponent]
        Ordered list of scaffold components.
    """

    name: str
    length: int
    components: list[ScaffoldComponent] = field(default_factory=list)

    @property
    def n_contigs(self) -> int:
        """Return number of contig components."""
        return sum(1 for c in self.components if not c.is_gap)

    @property
    def n_gaps(self) -> int:
        """Return number of gap components."""
        return sum(1 for c in self.components if c.is_gap)

    @property
    def total_gap_length(self) -> int:
        """Return total gap length."""
        return sum(c.length for c in self.components if c.is_gap)

    @property
    def contig_ids(self) -> list[str]:
        """Return list of contig IDs in order."""
        return [c.component_id for c in self.components if not c.is_gap and c.component_id]


@dataclass
class Assembly:
    """An assembly consisting of contigs/scaffolds.

    Parameters
    ----------
    name : str
        Assembly identifier.
    contigs : dict[str, Contig]
        Mapping of contig names to Contig objects.
    scaffolds : dict[str, Scaffold] | None
        Mapping of scaffold names to Scaffold objects (if AGP provided).
    """

    name: str
    contigs: dict[str, Contig] = field(default_factory=dict)
    scaffolds: dict[str, Scaffold] | None = None

    @property
    def total_size(self) -> int:
        """Return total assembly size in base pairs."""
        return sum(c.length for c in self.contigs.values())

    @property
    def n50(self) -> int:
        """Calculate N50 of the assembly."""
        lengths = sorted([c.length for c in self.contigs.values()], reverse=True)
        if not lengths:
            return 0
        total = sum(lengths)
        cumsum = 0
        for length in lengths:
            cumsum += length
            if cumsum >= total / 2:
                return length
        return lengths[-1]

    @property
    def n_contigs(self) -> int:
        """Return number of contigs."""
        return len(self.contigs)

    @property
    def n_scaffolds(self) -> int:
        """Return number of scaffolds."""
        return len(self.scaffolds) if self.scaffolds else 0

    @property
    def longest_contig(self) -> int:
        """Return length of longest contig."""
        if not self.contigs:
            return 0
        return max(c.length for c in self.contigs.values())

    @property
    def shortest_contig(self) -> int:
        """Return length of shortest contig."""
        if not self.contigs:
            return 0
        return min(c.length for c in self.contigs.values())

    def get_contig(self, name: str) -> Contig | None:
        """Get contig by name.

        Parameters
        ----------
        name : str
            Contig name.

        Returns
        -------
        Contig | None
            Contig if found, None otherwise.
        """
        return self.contigs.get(name)

    def get_scaffold(self, name: str) -> Scaffold | None:
        """Get scaffold by name.

        Parameters
        ----------
        name : str
            Scaffold name.

        Returns
        -------
        Scaffold | None
            Scaffold if found, None otherwise.
        """
        if self.scaffolds is None:
            return None
        return self.scaffolds.get(name)

    def contig_names(self) -> list[str]:
        """Return sorted list of contig names."""
        return sorted(self.contigs.keys())

    def scaffold_names(self) -> list[str]:
        """Return sorted list of scaffold names."""
        if self.scaffolds is None:
            return []
        return sorted(self.scaffolds.keys())

    def contigs_by_length(self, descending: bool = True) -> list[Contig]:
        """Return contigs sorted by length.

        Parameters
        ----------
        descending : bool
            Sort largest first if True.

        Returns
        -------
        list[Contig]
            Sorted list of contigs.
        """
        return sorted(self.contigs.values(), key=lambda c: c.length, reverse=descending)

    def length_distribution(
        self,
        bins: list[int] | None = None,
    ) -> dict[str, int]:
        """Calculate contig length distribution.

        Parameters
        ----------
        bins : list[int] | None
            Bin boundaries. Default: [0, 1000, 10000, 100000, 1000000, inf]

        Returns
        -------
        dict[str, int]
            Counts per bin.
        """
        if bins is None:
            bins = [0, 1_000, 10_000, 100_000, 1_000_000]

        result: dict[str, int] = {}
        for i in range(len(bins)):
            low = bins[i]
            high = bins[i + 1] if i + 1 < len(bins) else float("inf")
            label = f"{low}-{high}" if high != float("inf") else f">{low}"
            count = sum(1 for c in self.contigs.values() if low <= c.length < high)
            result[label] = count

        return result

    def summary(self) -> dict:
        """Generate assembly summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        lengths = [c.length for c in self.contigs.values()]
        if not lengths:
            return {
                "name": self.name,
                "n_contigs": 0,
                "total_size": 0,
                "n50": 0,
                "n90": 0,
                "longest": 0,
                "shortest": 0,
                "mean_length": 0,
            }

        lengths_sorted = sorted(lengths, reverse=True)
        total = sum(lengths)

        # Calculate N90
        cumsum = 0
        n90 = 0
        for length in lengths_sorted:
            cumsum += length
            if cumsum >= total * 0.9:
                n90 = length
                break

        return {
            "name": self.name,
            "n_contigs": len(lengths),
            "total_size": total,
            "n50": self.n50,
            "n90": n90,
            "longest": max(lengths),
            "shortest": min(lengths),
            "mean_length": total / len(lengths),
            "n_scaffolds": self.n_scaffolds,
        }

    @classmethod
    def from_fasta(
        cls,
        path: Path | str,
        name: str | None = None,
        load_sequences: bool = False,
    ) -> Assembly:
        """Load assembly from FASTA file.

        Parameters
        ----------
        path : Path | str
            Path to FASTA file (can be gzipped).
        name : str | None
            Assembly name. Defaults to filename stem.
        load_sequences : bool
            Whether to load full sequences into memory.

        Returns
        -------
        Assembly
            Loaded assembly.
        """
        path = Path(path)
        if name is None:
            name = path.stem.replace(".fa", "").replace(".fasta", "")

        logger.info(f"Loading assembly from FASTA: {path}")

        contigs: dict[str, Contig] = {}
        current_name: str | None = None
        current_seq: list[str] = []

        # Handle gzipped files
        opener = gzip.open if path.suffix == ".gz" else open
        mode = "rt" if path.suffix == ".gz" else "r"

        with opener(path, mode) as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    # Save previous contig
                    if current_name is not None:
                        seq = "".join(current_seq) if load_sequences else None
                        length = sum(len(s) for s in current_seq)
                        contigs[current_name] = Contig(
                            name=current_name,
                            length=length,
                            sequence=seq,
                        )

                    # Start new contig
                    current_name = line[1:].split()[0]
                    current_seq = []
                else:
                    current_seq.append(line)

            # Save last contig
            if current_name is not None:
                seq = "".join(current_seq) if load_sequences else None
                length = sum(len(s) for s in current_seq)
                contigs[current_name] = Contig(
                    name=current_name,
                    length=length,
                    sequence=seq,
                )

        logger.info(f"Loaded {len(contigs)} contigs, total {sum(c.length for c in contigs.values()):,} bp")

        return cls(name=name, contigs=contigs)

    @classmethod
    def from_fai(cls, path: Path | str, name: str | None = None) -> Assembly:
        """Load assembly from FAI index file.

        Faster than parsing FASTA when only sizes are needed.

        Parameters
        ----------
        path : Path | str
            Path to .fai index file.
        name : str | None
            Assembly name. Defaults to filename stem.

        Returns
        -------
        Assembly
            Loaded assembly (sequences not loaded).
        """
        path = Path(path)
        if name is None:
            name = path.stem.replace(".fai", "").replace(".fa", "").replace(".fasta", "")

        logger.info(f"Loading assembly from FAI index: {path}")

        contigs: dict[str, Contig] = {}

        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                fields = line.strip().split("\t")
                contig_name = fields[0]
                length = int(fields[1])
                contigs[contig_name] = Contig(name=contig_name, length=length)

        logger.info(f"Loaded {len(contigs)} contigs from index")

        return cls(name=name, contigs=contigs)

    @classmethod
    def from_agp(
        cls,
        agp_path: Path | str,
        fai_path: Path | str | None = None,
        name: str | None = None,
    ) -> Assembly:
        """Load assembly from AGP file with optional FAI for contig sizes.

        Parameters
        ----------
        agp_path : Path | str
            Path to AGP file defining scaffold structure.
        fai_path : Path | str | None
            Path to FAI file for contig sizes. If None, sizes from AGP.
        name : str | None
            Assembly name. Defaults to AGP filename stem.

        Returns
        -------
        Assembly
            Loaded assembly with scaffold structure.
        """
        agp_path = Path(agp_path)
        if name is None:
            name = agp_path.stem.replace(".agp", "")

        logger.info(f"Loading assembly from AGP: {agp_path}")

        # Load contig sizes from FAI if provided
        contig_sizes: dict[str, int] = {}
        if fai_path:
            fai_path = Path(fai_path)
            with open(fai_path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    fields = line.strip().split("\t")
                    contig_sizes[fields[0]] = int(fields[1])

        # Parse AGP file
        scaffolds: dict[str, list[ScaffoldComponent]] = {}
        scaffold_lengths: dict[str, int] = {}
        contig_names_in_agp: set[str] = set()

        with open(agp_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                fields = line.split("\t")
                scaffold_name = fields[0]
                # AGP uses 1-based coordinates, convert to 0-based
                scaffold_start = int(fields[1]) - 1
                scaffold_end = int(fields[2])
                component_num = int(fields[3])
                component_type = fields[4]

                component = ScaffoldComponent(
                    scaffold=scaffold_name,
                    scaffold_start=scaffold_start,
                    scaffold_end=scaffold_end,
                    component_num=component_num,
                    component_type=component_type,
                )

                if component_type in ("N", "U"):
                    # Gap
                    component.gap_length = int(fields[5])
                    component.gap_type = fields[6] if len(fields) > 6 else None
                    if len(fields) > 7:
                        component.linkage = fields[7].lower() == "yes"
                    if len(fields) > 8:
                        component.linkage_evidence = fields[8]
                else:
                    # Contig
                    component.component_id = fields[5]
                    # AGP uses 1-based coordinates
                    component.component_start = int(fields[6]) - 1
                    component.component_end = int(fields[7])
                    component.orientation = fields[8] if len(fields) > 8 else "+"
                    contig_names_in_agp.add(fields[5])

                if scaffold_name not in scaffolds:
                    scaffolds[scaffold_name] = []
                scaffolds[scaffold_name].append(component)

                # Track scaffold length
                if scaffold_name not in scaffold_lengths:
                    scaffold_lengths[scaffold_name] = 0
                scaffold_lengths[scaffold_name] = max(
                    scaffold_lengths[scaffold_name], scaffold_end
                )

        # Build contigs dict
        contigs: dict[str, Contig] = {}
        for contig_name in contig_names_in_agp:
            if contig_name in contig_sizes:
                length = contig_sizes[contig_name]
            else:
                # Get length from AGP (component_end - component_start)
                length = 0
                for scaffold_comps in scaffolds.values():
                    for comp in scaffold_comps:
                        if comp.component_id == contig_name:
                            comp_length = (comp.component_end or 0) - (comp.component_start or 0)
                            length = max(length, comp_length)
            contigs[contig_name] = Contig(name=contig_name, length=length)

        # Build scaffolds dict
        scaffold_objs: dict[str, Scaffold] = {}
        for scaffold_name, components in scaffolds.items():
            scaffold_objs[scaffold_name] = Scaffold(
                name=scaffold_name,
                length=scaffold_lengths[scaffold_name],
                components=sorted(components, key=lambda c: c.scaffold_start),
            )

        logger.info(
            f"Loaded {len(contigs)} contigs in {len(scaffold_objs)} scaffolds from AGP"
        )

        return cls(name=name, contigs=contigs, scaffolds=scaffold_objs)


def iter_fasta(path: Path | str) -> Iterator[tuple[str, str]]:
    """Iterate over sequences in a FASTA file.

    Yields (name, sequence) tuples without loading entire file.

    Parameters
    ----------
    path : Path | str
        Path to FASTA file (can be gzipped).

    Yields
    ------
    tuple[str, str]
        (sequence_name, sequence) pairs.
    """
    path = Path(path)

    opener = gzip.open if path.suffix == ".gz" else open
    mode = "rt" if path.suffix == ".gz" else "r"

    with opener(path, mode) as f:
        current_name: str | None = None
        current_seq: list[str] = []

        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if current_name is not None:
                    yield current_name, "".join(current_seq)
                current_name = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)

        if current_name is not None:
            yield current_name, "".join(current_seq)


def get_contig_sequence(
    fasta_path: Path | str,
    contig_name: str,
) -> str | None:
    """Extract sequence for a single contig from FASTA.

    Parameters
    ----------
    fasta_path : Path | str
        Path to FASTA file.
    contig_name : str
        Name of contig to extract.

    Returns
    -------
    str | None
        Sequence if found, None otherwise.
    """
    for name, seq in iter_fasta(fasta_path):
        if name == contig_name:
            return seq
    return None


def extract_region(
    fasta_path: Path | str,
    contig: str,
    start: int,
    end: int,
) -> str | None:
    """Extract a region from a FASTA file.

    Parameters
    ----------
    fasta_path : Path | str
        Path to FASTA file.
    contig : str
        Contig name.
    start : int
        0-based start position.
    end : int
        0-based end position (exclusive).

    Returns
    -------
    str | None
        Sequence region if found, None otherwise.
    """
    seq = get_contig_sequence(fasta_path, contig)
    if seq is None:
        return None
    return seq[start:end]


def write_fasta(
    sequences: dict[str, str] | list[tuple[str, str]],
    path: Path | str,
    line_width: int = 60,
    compress: bool = False,
) -> Path:
    """Write sequences to FASTA file.

    Parameters
    ----------
    sequences : dict[str, str] | list[tuple[str, str]]
        Sequences as dict or list of (name, seq) tuples.
    path : Path | str
        Output path.
    line_width : int
        Bases per line.
    compress : bool
        Gzip compress output.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    if compress and path.suffix != ".gz":
        path = Path(str(path) + ".gz")

    logger.info(f"Writing FASTA to {path}")

    opener = gzip.open if compress or path.suffix == ".gz" else open
    mode = "wt" if compress or path.suffix == ".gz" else "w"

    if isinstance(sequences, dict):
        sequences = list(sequences.items())

    with opener(path, mode) as f:
        for name, seq in sequences:
            f.write(f">{name}\n")
            for i in range(0, len(seq), line_width):
                f.write(seq[i : i + line_width] + "\n")

    return path


def write_fai(assembly: Assembly, path: Path | str) -> Path:
    """Write FAI index file for assembly.

    Parameters
    ----------
    assembly : Assembly
        Assembly to index.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Writing FAI index to {path}")

    # FAI format: name, length, offset, bases_per_line, bytes_per_line
    # We write simplified version with just name and length (offset = 0)
    with open(path, "w") as f:
        for name in sorted(assembly.contigs.keys()):
            contig = assembly.contigs[name]
            # Write placeholder values for offset and line info
            f.write(f"{name}\t{contig.length}\t0\t60\t61\n")

    return path


def parse_gfa_segments(path: Path | str) -> dict[str, int]:
    """Parse GFA file to extract segment names and lengths.

    Parameters
    ----------
    path : Path | str
        Path to GFA file.

    Returns
    -------
    dict[str, int]
        Mapping of segment names to lengths.
    """
    path = Path(path)
    logger.info(f"Parsing GFA segments from {path}")

    segments: dict[str, int] = {}

    opener = gzip.open if path.suffix == ".gz" else open
    mode = "rt" if path.suffix == ".gz" else "r"

    with opener(path, mode) as f:
        for line in f:
            if line.startswith("S\t"):
                # Segment line: S <name> <sequence> [tags]
                fields = line.strip().split("\t")
                name = fields[1]
                seq = fields[2]
                if seq == "*":
                    # Sequence not included, look for LN tag
                    for tag in fields[3:]:
                        if tag.startswith("LN:i:"):
                            segments[name] = int(tag[5:])
                            break
                else:
                    segments[name] = len(seq)

    logger.info(f"Found {len(segments)} segments in GFA")
    return segments
