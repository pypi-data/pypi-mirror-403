"""
AGP format I/O for scaffold orderings.

Handles reading and writing AGP (A Golden Path) format files
for representing scaffold structure and pseudomolecule assembly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from haplophaser.scaffold.ordering import ScaffoldOrdering

if TYPE_CHECKING:
    from haplophaser.io.assembly import Assembly

logger = logging.getLogger(__name__)


@dataclass
class AGPRecord:
    """A single record in an AGP file.

    AGP format represents scaffolds as sequences of contigs and gaps.

    Attributes:
        object_name: Scaffold/chromosome name.
        object_start: Start position in object (1-based).
        object_end: End position in object (1-based, inclusive).
        part_number: Component number within object.
        component_type: 'W' (WGS), 'D' (draft), 'N' (gap), 'U' (unknown gap).
        component_id: Contig/scaffold name (for W/D) or gap length (for N/U).
        component_start: Start in component (1-based, for W/D).
        component_end: End in component (1-based, inclusive, for W/D).
        orientation: '+', '-', '?', '0', or 'na'.
        gap_length: Gap length in bp (for N/U).
        gap_type: Gap type (for N/U): 'scaffold', 'contig', etc.
        linkage: 'yes' or 'no' (for gaps).
        linkage_evidence: Evidence for linkage.
    """

    object_name: str
    object_start: int
    object_end: int
    part_number: int
    component_type: str
    component_id: str | None = None
    component_start: int | None = None
    component_end: int | None = None
    orientation: str = "+"
    gap_length: int | None = None
    gap_type: str | None = None
    linkage: str | None = None
    linkage_evidence: str | None = None

    @property
    def is_gap(self) -> bool:
        """Return True if this is a gap record."""
        return self.component_type in ("N", "U")

    @property
    def length(self) -> int:
        """Return length of this component."""
        return self.object_end - self.object_start + 1

    def to_line(self) -> str:
        """Convert to AGP format line.

        Returns
        -------
        str
            Tab-separated AGP line.
        """
        if self.is_gap:
            fields = [
                self.object_name,
                str(self.object_start),
                str(self.object_end),
                str(self.part_number),
                self.component_type,
                str(self.gap_length or 100),
                self.gap_type or "scaffold",
                self.linkage or "yes",
                self.linkage_evidence or "map",
            ]
        else:
            fields = [
                self.object_name,
                str(self.object_start),
                str(self.object_end),
                str(self.part_number),
                self.component_type,
                self.component_id or "",
                str(self.component_start or 1),
                str(self.component_end or 1),
                self.orientation,
            ]
        return "\t".join(fields)


@dataclass
class AGP:
    """AGP file representation.

    Attributes:
        records: List of AGP records.
        version: AGP format version.
        comment_lines: Header comment lines.
    """

    records: list[AGPRecord] = field(default_factory=list)
    version: str = "2.1"
    comment_lines: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path | str) -> AGP:
        """Load AGP from file.

        Parameters
        ----------
        path : Path | str
            Path to AGP file.

        Returns
        -------
        AGP
            Loaded AGP.
        """
        path = Path(path)
        logger.info(f"Loading AGP from {path}")

        records = []
        comments = []

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("#"):
                    comments.append(line)
                    continue

                fields = line.split("\t")
                if len(fields) < 5:
                    continue

                record = cls._parse_record(fields)
                if record:
                    records.append(record)

        logger.info(f"Loaded {len(records)} records from AGP")
        return cls(records=records, comment_lines=comments)

    @staticmethod
    def _parse_record(fields: list[str]) -> AGPRecord | None:
        """Parse a single AGP record from fields.

        Parameters
        ----------
        fields : list[str]
            Tab-separated fields.

        Returns
        -------
        AGPRecord | None
            Parsed record or None.
        """
        try:
            object_name = fields[0]
            object_start = int(fields[1])
            object_end = int(fields[2])
            part_number = int(fields[3])
            component_type = fields[4]

            if component_type in ("N", "U"):
                # Gap record
                gap_length = int(fields[5]) if len(fields) > 5 else 100
                gap_type = fields[6] if len(fields) > 6 else "scaffold"
                linkage = fields[7] if len(fields) > 7 else "yes"
                linkage_evidence = fields[8] if len(fields) > 8 else "map"

                return AGPRecord(
                    object_name=object_name,
                    object_start=object_start,
                    object_end=object_end,
                    part_number=part_number,
                    component_type=component_type,
                    gap_length=gap_length,
                    gap_type=gap_type,
                    linkage=linkage,
                    linkage_evidence=linkage_evidence,
                )
            else:
                # Contig/scaffold record
                component_id = fields[5] if len(fields) > 5 else None
                component_start = int(fields[6]) if len(fields) > 6 else 1
                component_end = int(fields[7]) if len(fields) > 7 else 1
                orientation = fields[8] if len(fields) > 8 else "+"

                return AGPRecord(
                    object_name=object_name,
                    object_start=object_start,
                    object_end=object_end,
                    part_number=part_number,
                    component_type=component_type,
                    component_id=component_id,
                    component_start=component_start,
                    component_end=component_end,
                    orientation=orientation,
                )
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse AGP record: {e}")
            return None

    def to_string(self) -> str:
        """Convert to AGP format string.

        Returns
        -------
        str
            Full AGP file content.
        """
        lines = []

        # Header comments
        lines.append(f"##agp-version\t{self.version}")
        for comment in self.comment_lines:
            if not comment.startswith("##agp-version"):
                lines.append(comment)

        # Records
        for record in self.records:
            lines.append(record.to_line())

        return "\n".join(lines) + "\n"

    def write(self, path: Path | str) -> Path:
        """Write AGP to file.

        Parameters
        ----------
        path : Path | str
            Output path.

        Returns
        -------
        Path
            Written path.
        """
        path = Path(path)
        logger.info(f"Writing AGP to {path}")

        with open(path, "w") as f:
            f.write(self.to_string())

        return path

    def objects(self) -> list[str]:
        """Get list of object (scaffold) names.

        Returns
        -------
        list[str]
            Unique object names.
        """
        seen = set()
        result = []
        for record in self.records:
            if record.object_name not in seen:
                seen.add(record.object_name)
                result.append(record.object_name)
        return result

    def records_for_object(self, object_name: str) -> list[AGPRecord]:
        """Get records for a specific object.

        Parameters
        ----------
        object_name : str
            Object name.

        Returns
        -------
        list[AGPRecord]
            Records for this object, sorted by position.
        """
        records = [r for r in self.records if r.object_name == object_name]
        return sorted(records, key=lambda r: r.object_start)

    def contig_ids(self) -> list[str]:
        """Get list of contig IDs.

        Returns
        -------
        list[str]
            Contig IDs (excluding gaps).
        """
        return [r.component_id for r in self.records if not r.is_gap and r.component_id]


class AGPWriter:
    """Write scaffold orderings to AGP format.

    Parameters
    ----------
    gap_type : str
        Gap type to use (default: 'scaffold').
    linkage_evidence : str
        Linkage evidence to use (default: 'map').
    component_type : str
        Component type for contigs (default: 'W').
    """

    def __init__(
        self,
        gap_type: str = "scaffold",
        linkage_evidence: str = "map",
        component_type: str = "W",
    ) -> None:
        self.gap_type = gap_type
        self.linkage_evidence = linkage_evidence
        self.component_type = component_type

    def write(
        self,
        orderings: dict[str, ScaffoldOrdering] | ScaffoldOrdering,
        path: Path | str,
    ) -> Path:
        """Write orderings to AGP file.

        Parameters
        ----------
        orderings : dict[str, ScaffoldOrdering] | ScaffoldOrdering
            Orderings to write.
        path : Path | str
            Output path.

        Returns
        -------
        Path
            Written path.
        """
        agp = self.to_agp(orderings)
        return agp.write(path)

    def to_agp(
        self, orderings: dict[str, ScaffoldOrdering] | ScaffoldOrdering
    ) -> AGP:
        """Convert orderings to AGP object.

        Parameters
        ----------
        orderings : dict[str, ScaffoldOrdering] | ScaffoldOrdering
            Orderings to convert.

        Returns
        -------
        AGP
            AGP object.
        """
        if isinstance(orderings, ScaffoldOrdering):
            orderings = {orderings.chromosome: orderings}

        records = []
        comments = [
            "# Generated by phaser scaffold ordering",
            f"# Gap type: {self.gap_type}",
            f"# Linkage evidence: {self.linkage_evidence}",
        ]

        for chrom in sorted(orderings.keys()):
            ordering = orderings[chrom]
            chrom_records = self._ordering_to_records(ordering)
            records.extend(chrom_records)

        return AGP(records=records, comment_lines=comments)

    def _ordering_to_records(self, ordering: ScaffoldOrdering) -> list[AGPRecord]:
        """Convert a single ordering to AGP records.

        Parameters
        ----------
        ordering : ScaffoldOrdering
            Ordering to convert.

        Returns
        -------
        list[AGPRecord]
            AGP records.
        """
        records = []
        part_number = 0
        current_pos = 1  # AGP uses 1-based positions

        for i, oc in enumerate(ordering.ordered_contigs):
            # Add gap before contig (except for first)
            if i > 0 and oc.gap_before > 0:
                part_number += 1
                gap_end = current_pos + oc.gap_before - 1

                records.append(AGPRecord(
                    object_name=ordering.chromosome,
                    object_start=current_pos,
                    object_end=gap_end,
                    part_number=part_number,
                    component_type="N",
                    gap_length=oc.gap_before,
                    gap_type=self.gap_type,
                    linkage="yes",
                    linkage_evidence=self.linkage_evidence,
                ))
                current_pos = gap_end + 1

            # Add contig
            part_number += 1
            contig_length = oc.end - oc.start
            contig_end = current_pos + contig_length - 1

            records.append(AGPRecord(
                object_name=ordering.chromosome,
                object_start=current_pos,
                object_end=contig_end,
                part_number=part_number,
                component_type=self.component_type,
                component_id=oc.contig,
                component_start=1,
                component_end=contig_length,
                orientation=oc.orientation,
            ))
            current_pos = contig_end + 1

        return records

    def write_pseudomolecules(
        self,
        orderings: dict[str, ScaffoldOrdering],
        assembly: Assembly,
        path: Path | str,
        gap_char: str = "N",
        line_width: int = 60,
    ) -> Path:
        """Write pseudomolecule FASTA.

        Parameters
        ----------
        orderings : dict[str, ScaffoldOrdering]
            Orderings.
        assembly : Assembly
            Source assembly with sequences.
        path : Path | str
            Output path.
        gap_char : str
            Character for gaps.
        line_width : int
            FASTA line width.

        Returns
        -------
        Path
            Written path.
        """
        path = Path(path)
        logger.info(f"Writing pseudomolecules to {path}")

        with open(path, "w") as f:
            for chrom in sorted(orderings.keys()):
                ordering = orderings[chrom]
                header, sequence = ordering.to_fasta(assembly, gap_char)

                f.write(f"{header}\n")
                for i in range(0, len(sequence), line_width):
                    f.write(sequence[i:i + line_width] + "\n")

        return path


def write_agp(
    orderings: dict[str, ScaffoldOrdering] | ScaffoldOrdering,
    path: Path | str,
    gap_type: str = "scaffold",
    linkage_evidence: str = "map",
) -> Path:
    """Convenience function to write AGP.

    Parameters
    ----------
    orderings : dict[str, ScaffoldOrdering] | ScaffoldOrdering
        Orderings to write.
    path : Path | str
        Output path.
    gap_type : str
        Gap type.
    linkage_evidence : str
        Linkage evidence.

    Returns
    -------
    Path
        Written path.
    """
    writer = AGPWriter(gap_type=gap_type, linkage_evidence=linkage_evidence)
    return writer.write(orderings, path)


def compare_agp(
    agp1: AGP,
    agp2: AGP,
) -> dict:
    """Compare two AGP files.

    Parameters
    ----------
    agp1 : AGP
        First AGP.
    agp2 : AGP
        Second AGP.

    Returns
    -------
    dict
        Comparison results.
    """
    objects1 = set(agp1.objects())
    objects2 = set(agp2.objects())

    shared_objects = objects1 & objects2
    only_in_1 = objects1 - objects2
    only_in_2 = objects2 - objects1

    # Compare contig orders in shared objects
    order_concordance = {}
    for obj in shared_objects:
        contigs1 = [r.component_id for r in agp1.records_for_object(obj) if not r.is_gap]
        contigs2 = [r.component_id for r in agp2.records_for_object(obj) if not r.is_gap]

        shared_contigs = set(contigs1) & set(contigs2)

        if len(shared_contigs) >= 2:
            # Get order indices
            order1 = {c: i for i, c in enumerate(contigs1) if c in shared_contigs}
            order2 = {c: i for i, c in enumerate(contigs2) if c in shared_contigs}

            # Calculate rank correlation
            from scipy import stats
            ranks1 = [order1[c] for c in sorted(shared_contigs)]
            ranks2 = [order2[c] for c in sorted(shared_contigs)]

            try:
                corr, _ = stats.spearmanr(ranks1, ranks2)
                order_concordance[obj] = corr
            except Exception:
                order_concordance[obj] = 0.0
        else:
            order_concordance[obj] = None

    return {
        "n_objects_1": len(objects1),
        "n_objects_2": len(objects2),
        "shared_objects": list(shared_objects),
        "only_in_1": list(only_in_1),
        "only_in_2": list(only_in_2),
        "order_concordance": order_concordance,
        "mean_concordance": (
            sum(v for v in order_concordance.values() if v is not None)
            / max(1, sum(1 for v in order_concordance.values() if v is not None))
        ),
    }


def export_ordering_tsv(
    orderings: dict[str, ScaffoldOrdering],
    path: Path | str,
) -> Path:
    """Export detailed ordering information to TSV.

    Parameters
    ----------
    orderings : dict[str, ScaffoldOrdering]
        Orderings.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Written path.
    """
    path = Path(path)
    logger.info(f"Exporting ordering to {path}")

    columns = [
        "chromosome",
        "contig",
        "start",
        "end",
        "length",
        "orientation",
        "gap_before",
        "confidence",
        "evidence",
        "genetic_start",
        "genetic_end",
    ]

    with open(path, "w") as f:
        f.write("\t".join(columns) + "\n")

        for chrom in sorted(orderings.keys()):
            ordering = orderings[chrom]
            for oc in ordering.ordered_contigs:
                row = [
                    chrom,
                    oc.contig,
                    str(oc.start),
                    str(oc.end),
                    str(oc.length),
                    oc.orientation,
                    str(oc.gap_before),
                    f"{oc.confidence:.3f}",
                    oc.evidence,
                    f"{oc.genetic_start:.3f}" if oc.genetic_start is not None else "",
                    f"{oc.genetic_end:.3f}" if oc.genetic_end is not None else "",
                ]
                f.write("\t".join(row) + "\n")

    return path
