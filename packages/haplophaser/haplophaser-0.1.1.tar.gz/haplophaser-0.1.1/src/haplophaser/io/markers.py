"""
Marker export functions.

This module provides functions to export diagnostic markers in various
formats: BED for genome browser visualization, VCF for downstream tools,
and TSV with full annotation for analysis.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from haplophaser.markers.diagnostic import (
    DiagnosticMarker,
    DiagnosticMarkerSet,
)
from haplophaser.markers.quality import MarkerQualityAssessment

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def export_markers_bed(
    markers: DiagnosticMarkerSet | list[DiagnosticMarker],
    path: Path | str,
    track_name: str = "diagnostic_markers",
    include_classification: bool = True,
) -> None:
    """Export markers to BED format.

    BED format is suitable for visualization in genome browsers like
    IGV or the UCSC Genome Browser.

    Parameters
    ----------
    markers : DiagnosticMarkerSet or list[DiagnosticMarker]
        Markers to export.
    path : Path or str
        Output file path.
    track_name : str
        Track name for BED header.
    include_classification : bool
        Include marker classification in name field.
    """
    path = Path(path)
    marker_list = markers.markers if isinstance(markers, DiagnosticMarkerSet) else markers

    with open(path, "w") as f:
        # Write track line
        f.write(f'track name="{track_name}" description="Diagnostic markers"\n')

        # Sort by chromosome and position
        sorted_markers = sorted(marker_list, key=lambda m: (m.chrom, m.pos))

        for marker in sorted_markers:
            # BED is 0-based, half-open
            chrom = marker.chrom
            start = marker.pos
            end = marker.pos + 1  # SNP is 1bp

            if include_classification:
                name = f"{marker.ref}>{marker.alt}|{marker.classification.value}"
            else:
                name = f"{marker.ref}>{marker.alt}"

            # Score based on confidence (0-1000)
            score = int(marker.confidence * 1000)

            strand = "."

            f.write(f"{chrom}\t{start}\t{end}\t{name}\t{score}\t{strand}\n")

    logger.info(f"Exported {len(marker_list)} markers to BED: {path}")


def export_markers_vcf(
    markers: DiagnosticMarkerSet | list[DiagnosticMarker],
    path: Path | str,
    reference: str | None = None,
    founders: list[str] | None = None,
) -> None:
    """Export markers to VCF format.

    VCF format is suitable for use with standard bioinformatics tools.

    Parameters
    ----------
    markers : DiagnosticMarkerSet or list[DiagnosticMarker]
        Markers to export.
    path : Path or str
        Output file path.
    reference : str, optional
        Reference genome name for header.
    founders : list[str], optional
        Founder names for header.
    """
    path = Path(path)
    marker_list = markers.markers if isinstance(markers, DiagnosticMarkerSet) else markers

    if isinstance(markers, DiagnosticMarkerSet):
        founders = founders or markers.founders

    with open(path, "w") as f:
        # Write VCF header
        f.write("##fileformat=VCFv4.2\n")
        f.write(f"##fileDate={datetime.now().strftime('%Y%m%d')}\n")
        f.write("##source=phaser_diagnostic_markers\n")

        if reference:
            f.write(f"##reference={reference}\n")

        # INFO field definitions
        f.write('##INFO=<ID=CLASSIFICATION,Number=1,Type=String,Description="Marker classification">\n')
        f.write('##INFO=<ID=CONFIDENCE,Number=1,Type=Float,Description="Marker confidence score">\n')
        f.write('##INFO=<ID=FOUNDER_ALLELES,Number=.,Type=String,Description="Founder=allele assignments">\n')

        if founders:
            for founder in founders:
                f.write(f'##INFO=<ID=AF_{founder},Number=A,Type=Float,Description="Alt allele frequency in {founder}">\n')

        # Column header
        f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")

        # Sort by chromosome and position
        sorted_markers = sorted(marker_list, key=lambda m: (m.chrom, m.pos))

        for marker in sorted_markers:
            chrom = marker.chrom
            pos = marker.pos + 1  # VCF is 1-based
            variant_id = f"{chrom}_{pos}_{marker.ref}_{marker.alt}"
            ref = marker.ref
            alt = marker.alt
            qual = "."
            filt = "PASS"

            # Build INFO field
            info_parts = [
                f"CLASSIFICATION={marker.classification.value}",
                f"CONFIDENCE={marker.confidence:.3f}",
            ]

            # Founder alleles
            founder_alleles = [
                f"{f}={a}"
                for f, a in marker.founder_alleles.items()
            ]
            if founder_alleles:
                info_parts.append(f"FOUNDER_ALLELES={','.join(founder_alleles)}")

            # Founder frequencies
            for founder, freqs in marker.founder_frequencies.items():
                alt_freq = freqs.get(alt, 0)
                info_parts.append(f"AF_{founder}={alt_freq:.4f}")

            info = ";".join(info_parts)

            f.write(f"{chrom}\t{pos}\t{variant_id}\t{ref}\t{alt}\t{qual}\t{filt}\t{info}\n")

    logger.info(f"Exported {len(marker_list)} markers to VCF: {path}")


def export_markers_tsv(
    markers: DiagnosticMarkerSet | list[DiagnosticMarker],
    path: Path | str,
    include_frequencies: bool = True,
) -> None:
    """Export markers to TSV format with full annotation.

    TSV format includes all marker metadata for detailed analysis.

    Parameters
    ----------
    markers : DiagnosticMarkerSet or list[DiagnosticMarker]
        Markers to export.
    path : Path or str
        Output file path.
    include_frequencies : bool
        Include per-founder frequency columns.
    """
    path = Path(path)
    marker_list = markers.markers if isinstance(markers, DiagnosticMarkerSet) else markers

    if not marker_list:
        logger.warning("No markers to export")
        return

    # Get all founders from first marker
    founders = list(marker_list[0].founder_frequencies.keys()) if marker_list else []

    with open(path, "w") as f:
        # Write header
        headers = [
            "variant_id",
            "chrom",
            "pos_0based",
            "pos_1based",
            "ref",
            "alt",
            "classification",
            "confidence",
            "distinguishes",
        ]

        if include_frequencies:
            for founder in founders:
                headers.append(f"{founder}_ref_freq")
                headers.append(f"{founder}_alt_freq")
                headers.append(f"{founder}_allele")

        f.write("\t".join(headers) + "\n")

        # Sort by chromosome and position
        sorted_markers = sorted(marker_list, key=lambda m: (m.chrom, m.pos))

        for marker in sorted_markers:
            row = [
                marker.variant_id,
                marker.chrom,
                str(marker.pos),
                str(marker.pos + 1),
                marker.ref,
                marker.alt,
                marker.classification.value,
                f"{marker.confidence:.4f}",
                f"{marker.distinguishes[0]}:{marker.distinguishes[1]}" if marker.distinguishes else "",
            ]

            if include_frequencies:
                for founder in founders:
                    freqs = marker.founder_frequencies.get(founder, {})
                    ref_freq = freqs.get(marker.ref, 0)
                    alt_freq = freqs.get(marker.alt, 0)
                    allele = marker.founder_alleles.get(founder, "")

                    row.extend([
                        f"{ref_freq:.4f}",
                        f"{alt_freq:.4f}",
                        allele,
                    ])

            f.write("\t".join(row) + "\n")

    logger.info(f"Exported {len(marker_list)} markers to TSV: {path}")


def export_quality_report(
    assessment: MarkerQualityAssessment,
    path: Path | str,
    format: str = "txt",
) -> None:
    """Export marker quality assessment report.

    Parameters
    ----------
    assessment : MarkerQualityAssessment
        Quality assessment to export.
    path : Path or str
        Output file path.
    format : str
        Output format: 'txt' for text, 'json' for JSON.
    """
    path = Path(path)

    if format == "json":
        data = assessment.to_dict()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    else:
        with open(path, "w") as f:
            f.write(assessment.summary())

    logger.info(f"Exported quality report to: {path}")


def export_gaps_bed(
    assessment: MarkerQualityAssessment,
    path: Path | str,
    track_name: str = "marker_gaps",
) -> None:
    """Export marker gaps to BED format.

    Parameters
    ----------
    assessment : MarkerQualityAssessment
        Quality assessment with gaps.
    path : Path or str
        Output file path.
    track_name : str
        Track name for BED header.
    """
    path = Path(path)
    gaps = assessment.find_gaps()

    with open(path, "w") as f:
        f.write(f'track name="{track_name}" description="Regions lacking diagnostic markers"\n')

        for gap in gaps:
            fields = gap.to_bed_fields()
            f.write("\t".join(str(x) for x in fields) + "\n")

    logger.info(f"Exported {len(gaps)} gaps to BED: {path}")


def export_density_bedgraph(
    assessment: MarkerQualityAssessment,
    path: Path | str,
    track_name: str = "marker_density",
    window_size: int = 1_000_000,
) -> None:
    """Export marker density as BedGraph format.

    Parameters
    ----------
    assessment : MarkerQualityAssessment
        Quality assessment.
    path : Path or str
        Output file path.
    track_name : str
        Track name for header.
    window_size : int
        Window size for density calculation.
    """
    path = Path(path)
    density = assessment.density_by_window(window_size=window_size)

    with open(path, "w") as f:
        f.write(f'track type=bedGraph name="{track_name}" description="Markers per Mb"\n')

        for d in density:
            f.write(f"{d.chrom}\t{d.start}\t{d.end}\t{d.markers_per_mb:.2f}\n")

    logger.info(f"Exported density BedGraph to: {path}")


def export_founder_matrix_tsv(
    assessment: MarkerQualityAssessment,
    path: Path | str,
) -> None:
    """Export founder pair marker counts as matrix.

    Parameters
    ----------
    assessment : MarkerQualityAssessment
        Quality assessment.
    path : Path or str
        Output file path.
    """
    path = Path(path)
    founders = assessment.markers.founders
    matrix = assessment.distinguishability_matrix()

    with open(path, "w") as f:
        # Header row
        f.write("founder\t" + "\t".join(founders) + "\n")

        # Data rows
        for f1 in founders:
            row = [f1]
            for f2 in founders:
                if f1 == f2:
                    row.append("-")
                else:
                    pair = tuple(sorted([f1, f2]))
                    count = matrix.get(pair, 0)
                    row.append(str(count))
            f.write("\t".join(row) + "\n")

    logger.info(f"Exported founder matrix to: {path}")


def export_all_marker_formats(
    markers: DiagnosticMarkerSet,
    output_prefix: str | Path,
    formats: list[str] | None = None,
    assessment: MarkerQualityAssessment | None = None,
) -> dict[str, Path]:
    """Export markers in multiple formats at once.

    Parameters
    ----------
    markers : DiagnosticMarkerSet
        Markers to export.
    output_prefix : str or Path
        Prefix for output files.
    formats : list[str], optional
        Formats to export. Default: ['bed', 'tsv', 'vcf'].
    assessment : MarkerQualityAssessment, optional
        Quality assessment for additional exports.

    Returns
    -------
    dict[str, Path]
        Mapping of format to output file path.
    """
    output_prefix = Path(output_prefix)
    formats = formats or ["bed", "tsv", "vcf"]
    outputs: dict[str, Path] = {}

    for fmt in formats:
        if fmt == "bed":
            path = output_prefix.with_suffix(".bed")
            export_markers_bed(markers, path)
            outputs["bed"] = path

        elif fmt == "tsv":
            path = output_prefix.with_suffix(".tsv")
            export_markers_tsv(markers, path)
            outputs["tsv"] = path

        elif fmt == "vcf":
            path = output_prefix.with_suffix(".vcf")
            export_markers_vcf(markers, path)
            outputs["vcf"] = path

        elif fmt == "summary" and assessment:
            path = Path(str(output_prefix) + "_summary.txt")
            export_quality_report(assessment, path, format="txt")
            outputs["summary"] = path

        elif fmt == "json" and assessment:
            path = Path(str(output_prefix) + "_summary.json")
            export_quality_report(assessment, path, format="json")
            outputs["json"] = path

        elif fmt == "gaps" and assessment:
            path = Path(str(output_prefix) + "_gaps.bed")
            export_gaps_bed(assessment, path)
            outputs["gaps"] = path

        elif fmt == "density" and assessment:
            path = Path(str(output_prefix) + "_density.bedgraph")
            export_density_bedgraph(assessment, path)
            outputs["density"] = path

        elif fmt == "matrix" and assessment:
            path = Path(str(output_prefix) + "_founder_matrix.tsv")
            export_founder_matrix_tsv(assessment, path)
            outputs["matrix"] = path

    return outputs
