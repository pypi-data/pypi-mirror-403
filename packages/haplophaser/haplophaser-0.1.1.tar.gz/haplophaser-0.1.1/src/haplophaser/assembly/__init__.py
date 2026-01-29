"""Assembly haplotype painting module for Haplophaser."""

from haplophaser.assembly.chimera import (
    ChimeraDetector,
    ChimeraReport,
    ChimericRegion,
    detect_chimeras,
)
from haplophaser.assembly.mapping import (
    MappingMethod,
    MarkerHit,
    MarkerMapper,
    MarkerMappingResult,
    export_marker_hits_bed,
    export_marker_hits_tsv,
    load_marker_hits,
)
from haplophaser.assembly.paint import (
    AssemblyPainting,
    ContigPainter,
    ContigPainting,
    paint_assembly,
)
from haplophaser.assembly.qc import (
    AssemblyQC,
    AssemblyQCReport,
    generate_assembly_qc_report,
)
from haplophaser.assembly.subgenome import (
    SubgenomeAssigner,
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    assign_subgenomes,
)

__all__ = [
    # Chimera detection
    "ChimeraDetector",
    "ChimericRegion",
    "ChimeraReport",
    "detect_chimeras",
    # Marker mapping
    "MarkerHit",
    "MarkerMapper",
    "MarkerMappingResult",
    "MappingMethod",
    "export_marker_hits_bed",
    "export_marker_hits_tsv",
    "load_marker_hits",
    # Contig painting
    "AssemblyPainting",
    "ContigPainter",
    "ContigPainting",
    "paint_assembly",
    # Assembly QC
    "AssemblyQC",
    "AssemblyQCReport",
    "generate_assembly_qc_report",
    # Subgenome assignment
    "SubgenomeAssigner",
    "SubgenomeAssignment",
    "SubgenomeAssignmentResult",
    "assign_subgenomes",
]
