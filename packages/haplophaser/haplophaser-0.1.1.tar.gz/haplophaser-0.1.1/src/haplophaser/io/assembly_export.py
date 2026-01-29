"""
Export functions for assembly painting results.

Exports painting results, chimera reports, and subgenome assignments
in various formats (TSV, BED, FASTA, AGP).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.assembly.chimera import ChimeraReport
    from haplophaser.assembly.paint import AssemblyPainting
    from haplophaser.assembly.qc import AssemblyQCReport
    from haplophaser.assembly.subgenome import SubgenomeAssignmentResult
    from haplophaser.io.assembly import Assembly

logger = logging.getLogger(__name__)


# =============================================================================
# Painting Exports
# =============================================================================


def export_painting_tsv(
    painting: AssemblyPainting,
    path: Path | str,
) -> Path:
    """Export contig painting results to TSV.

    Parameters
    ----------
    painting : AssemblyPainting
        Painting results.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting painting to TSV: {path}")

    columns = [
        "contig",
        "length",
        "n_markers",
        "assigned_founder",
        "confidence",
        "is_chimeric",
        "marker_density",
    ]

    # Add founder proportion columns
    for founder in painting.founders:
        columns.append(f"{founder}_proportion")
        columns.append(f"{founder}_count")

    with open(path, "w") as f:
        f.write("\t".join(columns) + "\n")

        for contig_name in sorted(painting.contigs.keys()):
            cp = painting.contigs[contig_name]

            row = [
                contig_name,
                str(cp.length),
                str(cp.n_markers),
                cp.assigned_founder or "unassigned",
                f"{cp.confidence:.4f}",
                str(cp.is_chimeric).lower(),
                f"{cp.marker_density:.2f}",
            ]

            for founder in painting.founders:
                row.append(f"{cp.founder_proportions.get(founder, 0.0):.4f}")
                row.append(str(cp.founder_counts.get(founder, 0)))

            f.write("\t".join(row) + "\n")

    return path


def export_painting_bed(
    painting: AssemblyPainting,
    path: Path | str,
    track_name: str = "haplotype_painting",
    color_by_founder: dict[str, str] | None = None,
) -> Path:
    """Export painting as BED file with colors by founder.

    Parameters
    ----------
    painting : AssemblyPainting
        Painting results.
    path : Path | str
        Output path.
    track_name : str
        BED track name.
    color_by_founder : dict[str, str] | None
        RGB colors per founder (e.g., {'B73': '255,0,0', 'Mo17': '0,0,255'}).

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting painting to BED: {path}")

    # Default colors if not provided
    if color_by_founder is None:
        default_colors = [
            "255,0,0",      # Red
            "0,0,255",      # Blue
            "0,255,0",      # Green
            "255,165,0",    # Orange
            "128,0,128",    # Purple
            "0,128,128",    # Teal
            "255,192,203",  # Pink
            "165,42,42",    # Brown
        ]
        color_by_founder = {
            f: default_colors[i % len(default_colors)]
            for i, f in enumerate(painting.founders)
        }
    color_by_founder["unassigned"] = "128,128,128"  # Gray for unassigned

    with open(path, "w") as f:
        # Write track line
        f.write(
            f'track name="{track_name}" '
            f'description="Contig haplotype assignments" '
            f'itemRgb="On"\n'
        )

        for contig_name in sorted(painting.contigs.keys()):
            cp = painting.contigs[contig_name]

            founder = cp.assigned_founder or "unassigned"
            color = color_by_founder.get(founder, "128,128,128")
            score = int(cp.confidence * 1000)

            # BED9 format with color
            f.write(
                f"{contig_name}\t0\t{cp.length}\t"
                f"{founder}\t{score}\t.\t"
                f"0\t{cp.length}\t{color}\n"
            )

    return path


def export_painting_json(
    painting: AssemblyPainting,
    path: Path | str,
) -> Path:
    """Export painting results to JSON.

    Parameters
    ----------
    painting : AssemblyPainting
        Painting results.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting painting to JSON: {path}")

    data = {
        "assembly": painting.assembly,
        "founders": painting.founders,
        "method": painting.method,
        "parameters": painting.parameters,
        "summary": painting.summary(),
        "contigs": {
            name: cp.to_dict()
            for name, cp in painting.contigs.items()
        },
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return path


# =============================================================================
# Chimera Exports
# =============================================================================


def export_chimeras_tsv(
    chimeras: ChimeraReport,
    path: Path | str,
) -> Path:
    """Export chimera detection results to TSV.

    Parameters
    ----------
    chimeras : ChimeraReport
        Chimera detection results.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting chimeras to TSV: {path}")

    columns = [
        "contig",
        "switch_position",
        "ci_lower",
        "ci_upper",
        "left_founder",
        "right_founder",
        "left_confidence",
        "right_confidence",
        "n_markers_left",
        "n_markers_right",
        "left_proportion",
        "right_proportion",
    ]

    with open(path, "w") as f:
        f.write("\t".join(columns) + "\n")

        for switch in sorted(chimeras.switches, key=lambda s: (s.contig, s.switch_position)):
            row = [
                switch.contig,
                str(switch.switch_position),
                str(switch.switch_position_ci[0]),
                str(switch.switch_position_ci[1]),
                switch.left_founder,
                switch.right_founder,
                f"{switch.left_confidence:.4f}",
                f"{switch.right_confidence:.4f}",
                str(switch.n_markers_left),
                str(switch.n_markers_right),
                f"{switch.left_proportion:.4f}",
                f"{switch.right_proportion:.4f}",
            ]
            f.write("\t".join(row) + "\n")

    return path


def export_chimeras_bed(
    chimeras: ChimeraReport,
    path: Path | str,
    track_name: str = "chimera_breakpoints",
) -> Path:
    """Export chimera breakpoints as BED file.

    Parameters
    ----------
    chimeras : ChimeraReport
        Chimera detection results.
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
    logger.info(f"Exporting chimera breakpoints to BED: {path}")

    with open(path, "w") as f:
        f.write(
            f'track name="{track_name}" '
            f'description="Chimera breakpoint regions"\n'
        )

        for switch in sorted(chimeras.switches, key=lambda s: (s.contig, s.switch_position)):
            f.write(switch.to_bed_breakpoint() + "\n")

    return path


# =============================================================================
# Subgenome Assignment Exports
# =============================================================================


def export_subgenome_assignments_tsv(
    assignments: SubgenomeAssignmentResult,
    path: Path | str,
) -> Path:
    """Export subgenome assignments to TSV.

    Parameters
    ----------
    assignments : SubgenomeAssignmentResult
        Assignment results.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting subgenome assignments to TSV: {path}")

    columns = [
        "contig",
        "length",
        "subgenome",
        "confidence",
        "evidence",
        "n_genes",
    ]

    # Add per-subgenome support columns
    for sg in assignments.subgenomes:
        columns.append(f"{sg}_marker_count")
        columns.append(f"{sg}_ortholog_count")

    with open(path, "w") as f:
        f.write("\t".join(columns) + "\n")

        for contig_name in sorted(assignments.assignments.keys()):
            a = assignments.assignments[contig_name]

            row = [
                contig_name,
                str(a.length),
                a.subgenome or "unassigned",
                f"{a.confidence:.4f}",
                a.evidence.value,
                str(a.n_genes),
            ]

            for sg in assignments.subgenomes:
                marker_count = a.marker_support.get(sg, 0) if a.marker_support else 0
                ortholog_count = a.ortholog_support.get(sg, 0) if a.ortholog_support else 0
                row.append(str(marker_count))
                row.append(str(ortholog_count))

            f.write("\t".join(row) + "\n")

    return path


# =============================================================================
# FASTA Split Exports
# =============================================================================


def export_haplotype_fastas(
    assembly: Assembly,
    painting: AssemblyPainting,
    output_dir: Path | str,
    compress: bool = False,
    assembly_fasta: Path | str | None = None,
) -> dict[str, Path]:
    """Split assembly FASTA by haplotype assignment.

    Parameters
    ----------
    assembly : Assembly
        Assembly object.
    painting : AssemblyPainting
        Painting results.
    output_dir : Path | str
        Output directory.
    compress : bool
        Gzip compress output files.
    assembly_fasta : Path | str | None
        Original assembly FASTA (required if sequences not loaded).

    Returns
    -------
    dict[str, Path]
        Mapping of founder name to output FASTA path.
    """
    from haplophaser.io.assembly import iter_fasta, write_fasta

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Splitting assembly by haplotype into {output_dir}")

    # Group contigs by assignment
    by_founder: dict[str, list[str]] = {}
    for founder in painting.founders:
        by_founder[founder] = painting.by_founder(founder)
    by_founder["unassigned"] = painting.unassigned()
    by_founder["chimeric"] = painting.chimeric_contigs()

    # Get sequences
    sequences: dict[str, str] = {}
    if assembly_fasta:
        for name, seq in iter_fasta(assembly_fasta):
            sequences[name] = seq
    else:
        for name, contig in assembly.contigs.items():
            if contig.sequence:
                sequences[name] = contig.sequence
            else:
                logger.warning(f"No sequence for contig {name}, skipping")

    # Write output files
    output_paths: dict[str, Path] = {}
    ext = ".fasta.gz" if compress else ".fasta"

    for group, contig_names in by_founder.items():
        if not contig_names:
            continue

        group_seqs = [
            (name, sequences[name])
            for name in contig_names
            if name in sequences
        ]

        if not group_seqs:
            continue

        output_path = output_dir / f"{group}{ext}"
        write_fasta(group_seqs, output_path, compress=compress)
        output_paths[group] = output_path
        logger.info(f"Wrote {len(group_seqs)} contigs to {output_path}")

    return output_paths


# =============================================================================
# AGP Exports
# =============================================================================


def export_painted_agp(
    painting: AssemblyPainting,
    original_agp: Path | str,
    output_path: Path | str,
) -> Path:
    """Export AGP with haplotype annotations in comments.

    Parameters
    ----------
    painting : AssemblyPainting
        Painting results.
    original_agp : Path | str
        Original AGP file.
    output_path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    original_agp = Path(original_agp)
    output_path = Path(output_path)

    logger.info(f"Exporting painted AGP to {output_path}")

    with open(original_agp) as f_in, open(output_path, "w") as f_out:
        # Write header comment with painting info
        f_out.write("# Haplotype-annotated AGP generated by Haplophaser\n")
        f_out.write(f"# Assembly: {painting.assembly}\n")
        f_out.write(f"# Founders: {', '.join(painting.founders)}\n")
        f_out.write("#\n")

        for line in f_in:
            line = line.rstrip()

            if line.startswith("#"):
                f_out.write(line + "\n")
                continue

            if not line.strip():
                f_out.write("\n")
                continue

            fields = line.split("\t")
            fields[0]
            component_type = fields[4]

            # Add annotation comment for contigs
            if component_type not in ("N", "U") and len(fields) > 5:
                contig = fields[5]
                cp = painting.get_contig(contig)

                if cp:
                    annotation = f"# {contig}: "
                    if cp.is_assigned:
                        annotation += f"founder={cp.assigned_founder}, conf={cp.confidence:.2f}"
                    else:
                        annotation += "unassigned"
                    if cp.is_chimeric:
                        annotation += ", CHIMERIC"

                    f_out.write(line + "\n")
                    f_out.write(annotation + "\n")
                else:
                    f_out.write(line + "\n")
            else:
                f_out.write(line + "\n")

    return output_path


# =============================================================================
# QC Report Exports
# =============================================================================


def export_qc_report_txt(
    qc_report: AssemblyQCReport,
    path: Path | str,
) -> Path:
    """Export QC report as text file.

    Parameters
    ----------
    qc_report : AssemblyQCReport
        QC report.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting QC report to {path}")

    with open(path, "w") as f:
        f.write(qc_report.summary_text())

    return path


def export_qc_report_json(
    qc_report: AssemblyQCReport,
    path: Path | str,
) -> Path:
    """Export QC report as JSON.

    Parameters
    ----------
    qc_report : AssemblyQCReport
        QC report.
    path : Path | str
        Output path.

    Returns
    -------
    Path
        Path to written file.
    """
    path = Path(path)
    logger.info(f"Exporting QC report to JSON: {path}")

    with open(path, "w") as f:
        json.dump(qc_report.to_dict(), f, indent=2)

    return path


# =============================================================================
# Batch Export
# =============================================================================


def export_all_painting_formats(
    painting: AssemblyPainting,
    output_prefix: Path | str,
    chimeras: ChimeraReport | None = None,
    qc_report: AssemblyQCReport | None = None,
    formats: list[str] | None = None,
) -> dict[str, Path]:
    """Export painting results in multiple formats.

    Parameters
    ----------
    painting : AssemblyPainting
        Painting results.
    output_prefix : Path | str
        Output file prefix.
    chimeras : ChimeraReport | None
        Chimera detection results.
    qc_report : AssemblyQCReport | None
        QC report.
    formats : list[str] | None
        Formats to export. Default: ['tsv', 'bed', 'json'].

    Returns
    -------
    dict[str, Path]
        Mapping of format name to output path.
    """
    output_prefix = Path(output_prefix)

    if formats is None:
        formats = ["tsv", "bed", "json"]

    outputs: dict[str, Path] = {}

    if "tsv" in formats:
        outputs["painting_tsv"] = export_painting_tsv(
            painting, f"{output_prefix}_assignments.tsv"
        )

    if "bed" in formats:
        outputs["painting_bed"] = export_painting_bed(
            painting, f"{output_prefix}_haplotypes.bed"
        )

    if "json" in formats:
        outputs["painting_json"] = export_painting_json(
            painting, f"{output_prefix}_painting.json"
        )

    if chimeras and chimeras.switches:
        if "tsv" in formats:
            outputs["chimeras_tsv"] = export_chimeras_tsv(
                chimeras, f"{output_prefix}_chimeras.tsv"
            )
        if "bed" in formats:
            outputs["chimeras_bed"] = export_chimeras_bed(
                chimeras, f"{output_prefix}_chimeras.bed"
            )

    if qc_report:
        outputs["qc_txt"] = export_qc_report_txt(
            qc_report, f"{output_prefix}_qc_report.txt"
        )
        if "json" in formats:
            outputs["qc_json"] = export_qc_report_json(
                qc_report, f"{output_prefix}_qc_report.json"
            )

    return outputs
