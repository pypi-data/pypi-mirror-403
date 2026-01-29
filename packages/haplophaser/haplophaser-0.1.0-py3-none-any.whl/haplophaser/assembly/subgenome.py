"""
Subgenome assignment for polyploid assemblies.

Assigns contigs/scaffolds to subgenomes in allopolyploid species
using diagnostic markers and/or ortholog phylogenetic placement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from haplophaser.assembly.mapping import MarkerHit, MarkerMappingResult
    from haplophaser.io.assembly import Assembly
    from haplophaser.io.orthofinder import OrthoFinderResults

logger = logging.getLogger(__name__)


class AssignmentMethod(str, Enum):
    """Method for subgenome assignment."""

    MARKERS = "markers"
    ORTHOLOGS = "orthologs"
    COMBINED = "combined"


class EvidenceType(str, Enum):
    """Type of evidence supporting assignment."""

    MARKERS = "markers"
    ORTHOLOGS = "orthologs"
    BOTH = "both"


@dataclass
class SubgenomeAssignment:
    """Subgenome assignment for a single contig.

    Parameters
    ----------
    contig : str
        Contig name.
    length : int
        Contig length.
    subgenome : str | None
        Assigned subgenome (e.g., 'A', 'B').
    confidence : float
        Confidence in assignment (0-1).
    evidence : EvidenceType
        Type of evidence used.
    marker_support : dict[str, int] | None
        Marker counts per subgenome.
    ortholog_support : dict[str, int] | None
        Ortholog counts per subgenome.
    marker_proportions : dict[str, float] | None
        Marker proportions per subgenome.
    ortholog_proportions : dict[str, float] | None
        Ortholog proportions per subgenome.
    n_genes : int
        Number of genes on contig (if available).
    """

    contig: str
    length: int
    subgenome: str | None = None
    confidence: float = 0.0
    evidence: EvidenceType = EvidenceType.MARKERS
    marker_support: dict[str, int] | None = None
    ortholog_support: dict[str, int] | None = None
    marker_proportions: dict[str, float] | None = None
    ortholog_proportions: dict[str, float] | None = None
    n_genes: int = 0

    @property
    def is_assigned(self) -> bool:
        """Return True if contig is assigned to a subgenome."""
        return self.subgenome is not None

    @property
    def has_marker_evidence(self) -> bool:
        """Return True if marker evidence is available."""
        return self.marker_support is not None and sum(self.marker_support.values()) > 0

    @property
    def has_ortholog_evidence(self) -> bool:
        """Return True if ortholog evidence is available."""
        return self.ortholog_support is not None and sum(self.ortholog_support.values()) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "contig": self.contig,
            "length": self.length,
            "subgenome": self.subgenome,
            "confidence": self.confidence,
            "evidence": self.evidence.value,
            "marker_support": self.marker_support,
            "ortholog_support": self.ortholog_support,
            "n_genes": self.n_genes,
        }


@dataclass
class SubgenomeAssignmentResult:
    """Results of subgenome assignment across an assembly.

    Parameters
    ----------
    assembly : str
        Assembly name.
    subgenomes : list[str]
        Expected subgenomes.
    assignments : dict[str, SubgenomeAssignment]
        Assignment per contig.
    method : AssignmentMethod
        Method used.
    parameters : dict
        Parameters used.
    """

    assembly: str
    subgenomes: list[str]
    assignments: dict[str, SubgenomeAssignment] = field(default_factory=dict)
    method: AssignmentMethod = AssignmentMethod.MARKERS
    parameters: dict = field(default_factory=dict)

    @property
    def n_contigs(self) -> int:
        """Return total number of contigs."""
        return len(self.assignments)

    @property
    def n_assigned(self) -> int:
        """Return number of assigned contigs."""
        return sum(1 for a in self.assignments.values() if a.is_assigned)

    @property
    def n_unassigned(self) -> int:
        """Return number of unassigned contigs."""
        return sum(1 for a in self.assignments.values() if not a.is_assigned)

    def by_subgenome(self, subgenome: str) -> list[str]:
        """Return contigs assigned to a specific subgenome.

        Parameters
        ----------
        subgenome : str
            Subgenome name.

        Returns
        -------
        list[str]
            Contig names assigned to subgenome.
        """
        return [
            name for name, a in self.assignments.items()
            if a.subgenome == subgenome
        ]

    def unassigned(self) -> list[str]:
        """Return list of unassigned contig names.

        Returns
        -------
        list[str]
            Names of unassigned contigs.
        """
        return [name for name, a in self.assignments.items() if not a.is_assigned]

    def summary(self) -> dict:
        """Generate summary statistics.

        Returns
        -------
        dict
            Summary statistics.
        """
        total_bp = sum(a.length for a in self.assignments.values())

        by_subgenome: dict[str, dict] = {}
        for sg in self.subgenomes:
            sg_contigs = [a for a in self.assignments.values() if a.subgenome == sg]
            by_subgenome[sg] = {
                "n_contigs": len(sg_contigs),
                "total_bp": sum(a.length for a in sg_contigs),
                "mean_confidence": (
                    sum(a.confidence for a in sg_contigs) / len(sg_contigs)
                    if sg_contigs else 0.0
                ),
            }

        unassigned_contigs = [a for a in self.assignments.values() if not a.is_assigned]

        return {
            "assembly": self.assembly,
            "n_contigs": self.n_contigs,
            "n_assigned": self.n_assigned,
            "n_unassigned": self.n_unassigned,
            "total_bp": total_bp,
            "assignment_rate": self.n_assigned / self.n_contigs if self.n_contigs > 0 else 0.0,
            "by_subgenome": by_subgenome,
            "unassigned_bp": sum(a.length for a in unassigned_contigs),
            "method": self.method.value,
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Assignments as DataFrame.
        """
        import pandas as pd

        rows = []
        for name, assignment in sorted(self.assignments.items()):
            row = {
                "contig": name,
                "length": assignment.length,
                "subgenome": assignment.subgenome or "unassigned",
                "confidence": assignment.confidence,
                "evidence": assignment.evidence.value,
                "n_genes": assignment.n_genes,
            }
            # Add per-subgenome support
            for sg in self.subgenomes:
                if assignment.marker_support:
                    row[f"{sg}_marker_count"] = assignment.marker_support.get(sg, 0)
                if assignment.marker_proportions:
                    row[f"{sg}_marker_prop"] = assignment.marker_proportions.get(sg, 0.0)
                if assignment.ortholog_support:
                    row[f"{sg}_ortholog_count"] = assignment.ortholog_support.get(sg, 0)
                if assignment.ortholog_proportions:
                    row[f"{sg}_ortholog_prop"] = assignment.ortholog_proportions.get(sg, 0.0)
            rows.append(row)

        return pd.DataFrame(rows)


class SubgenomeAssigner:
    """Assign contigs to subgenomes in allopolyploid assemblies.

    Parameters
    ----------
    subgenomes : list[str]
        Expected subgenomes (e.g., ['A', 'B'] for tetraploid).
    method : str
        Assignment method: 'markers', 'orthologs', 'combined'.
    min_markers : int
        Minimum subgenome-diagnostic markers for assignment.
    min_orthologs : int
        Minimum orthologs for assignment.
    min_proportion : float
        Minimum proportion for confident assignment.
    marker_weight : float
        Weight for marker evidence in combined mode (0-1).
    """

    def __init__(
        self,
        subgenomes: list[str],
        method: str = "markers",
        min_markers: int = 5,
        min_orthologs: int = 3,
        min_proportion: float = 0.7,
        marker_weight: float = 0.5,
    ) -> None:
        self.subgenomes = subgenomes
        self.method = AssignmentMethod(method)
        self.min_markers = min_markers
        self.min_orthologs = min_orthologs
        self.min_proportion = min_proportion
        self.marker_weight = marker_weight

    def assign(
        self,
        assembly: Assembly,
        marker_hits: MarkerMappingResult | list[MarkerHit] | None = None,
        orthologs: OrthoFinderResults | None = None,
        gene_to_contig: dict[str, str] | None = None,
        subgenome_markers: dict[str, set[str]] | None = None,
    ) -> SubgenomeAssignmentResult:
        """Assign contigs to subgenomes.

        Parameters
        ----------
        assembly : Assembly
            Target assembly.
        marker_hits : MarkerMappingResult | list[MarkerHit] | None
            Subgenome-diagnostic marker hits.
        orthologs : OrthoFinderResults | None
            OrthoFinder results for phylogenetic placement.
        gene_to_contig : dict[str, str] | None
            Mapping of gene IDs to contig names.
        subgenome_markers : dict[str, set[str]] | None
            Mapping of subgenome to diagnostic marker IDs.

        Returns
        -------
        SubgenomeAssignmentResult
            Assignment results.
        """
        from haplophaser.assembly.mapping import MarkerMappingResult

        logger.info(f"Assigning {assembly.n_contigs} contigs to subgenomes: {self.subgenomes}")

        # Extract hits list
        if isinstance(marker_hits, MarkerMappingResult):
            hits_list = marker_hits.unique_hits()
        elif marker_hits is not None:
            hits_list = [h for h in marker_hits if h.is_unique]
        else:
            hits_list = []

        # Calculate marker evidence
        marker_evidence: dict[str, dict[str, int]] = {}
        if hits_list and subgenome_markers:
            marker_evidence = self._calculate_marker_evidence(
                hits_list, assembly, subgenome_markers
            )
        elif hits_list:
            # If no subgenome_markers mapping, try to infer from founder_alleles
            marker_evidence = self._infer_marker_evidence(hits_list, assembly)

        # Calculate ortholog evidence
        ortholog_evidence: dict[str, dict[str, int]] = {}
        gene_counts: dict[str, int] = {}
        if orthologs and gene_to_contig:
            ortholog_evidence, gene_counts = self._calculate_ortholog_evidence(
                orthologs, gene_to_contig, assembly
            )

        # Assign each contig
        assignments: dict[str, SubgenomeAssignment] = {}

        for contig_name, contig in assembly.contigs.items():
            assignment = self._assign_contig(
                contig_name,
                contig.length,
                marker_evidence.get(contig_name, {}),
                ortholog_evidence.get(contig_name, {}),
                gene_counts.get(contig_name, 0),
            )
            assignments[contig_name] = assignment

        result = SubgenomeAssignmentResult(
            assembly=assembly.name,
            subgenomes=self.subgenomes,
            assignments=assignments,
            method=self.method,
            parameters={
                "min_markers": self.min_markers,
                "min_orthologs": self.min_orthologs,
                "min_proportion": self.min_proportion,
                "marker_weight": self.marker_weight,
            },
        )

        logger.info(
            f"Assigned {result.n_assigned}/{result.n_contigs} contigs to subgenomes"
        )

        return result

    def _calculate_marker_evidence(
        self,
        hits: list[MarkerHit],
        assembly: Assembly,
        subgenome_markers: dict[str, set[str]],
    ) -> dict[str, dict[str, int]]:
        """Calculate marker evidence per contig.

        Parameters
        ----------
        hits : list[MarkerHit]
            Marker hits.
        assembly : Assembly
            Target assembly.
        subgenome_markers : dict[str, set[str]]
            Mapping of subgenome to marker IDs.

        Returns
        -------
        dict[str, dict[str, int]]
            Marker counts per subgenome per contig.
        """
        evidence: dict[str, dict[str, int]] = {}

        for contig_name in assembly.contigs:
            evidence[contig_name] = dict.fromkeys(self.subgenomes, 0)

        for hit in hits:
            if hit.contig not in evidence:
                continue

            # Determine which subgenome this marker supports
            for sg, marker_ids in subgenome_markers.items():
                if hit.marker_id in marker_ids:
                    evidence[hit.contig][sg] += 1
                    break

        return evidence

    def _infer_marker_evidence(
        self,
        hits: list[MarkerHit],
        assembly: Assembly,
    ) -> dict[str, dict[str, int]]:
        """Infer marker evidence from founder alleles.

        Assumes founder names correspond to subgenomes.

        Parameters
        ----------
        hits : list[MarkerHit]
            Marker hits.
        assembly : Assembly
            Target assembly.

        Returns
        -------
        dict[str, dict[str, int]]
            Marker counts per subgenome per contig.
        """
        evidence: dict[str, dict[str, int]] = {}

        for contig_name in assembly.contigs:
            evidence[contig_name] = dict.fromkeys(self.subgenomes, 0)

        for hit in hits:
            if hit.contig not in evidence:
                continue

            # Check if inferred founder matches a subgenome
            inferred = hit.inferred_founder()
            if inferred and inferred in self.subgenomes:
                evidence[hit.contig][inferred] += 1

        return evidence

    def _calculate_ortholog_evidence(
        self,
        orthologs: OrthoFinderResults,
        gene_to_contig: dict[str, str],
        assembly: Assembly,
    ) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
        """Calculate ortholog evidence per contig.

        Parameters
        ----------
        orthologs : OrthoFinderResults
            OrthoFinder results.
        gene_to_contig : dict[str, str]
            Gene to contig mapping.
        assembly : Assembly
            Target assembly.

        Returns
        -------
        tuple[dict[str, dict[str, int]], dict[str, int]]
            (Ortholog counts per subgenome per contig, gene counts per contig)
        """
        evidence: dict[str, dict[str, int]] = {}
        gene_counts: dict[str, int] = {}

        for contig_name in assembly.contigs:
            evidence[contig_name] = dict.fromkeys(self.subgenomes, 0)
            gene_counts[contig_name] = 0

        # Get genes per contig and their subgenome placement
        for gene_id, contig in gene_to_contig.items():
            if contig not in evidence:
                continue

            gene_counts[contig] = gene_counts.get(contig, 0) + 1

            # Get phylogenetic placement for this gene
            placement = orthologs.get_gene_placement(gene_id)
            if placement and placement in self.subgenomes:
                evidence[contig][placement] += 1

        return evidence, gene_counts

    def _assign_contig(
        self,
        contig_name: str,
        contig_length: int,
        marker_counts: dict[str, int],
        ortholog_counts: dict[str, int],
        n_genes: int,
    ) -> SubgenomeAssignment:
        """Assign a single contig to a subgenome.

        Parameters
        ----------
        contig_name : str
            Contig name.
        contig_length : int
            Contig length.
        marker_counts : dict[str, int]
            Marker counts per subgenome.
        ortholog_counts : dict[str, int]
            Ortholog counts per subgenome.
        n_genes : int
            Number of genes on contig.

        Returns
        -------
        SubgenomeAssignment
            Assignment for contig.
        """
        # Calculate proportions
        total_markers = sum(marker_counts.values())
        total_orthologs = sum(ortholog_counts.values())

        marker_props = {}
        ortholog_props = {}

        if total_markers > 0:
            marker_props = {sg: c / total_markers for sg, c in marker_counts.items()}
        if total_orthologs > 0:
            ortholog_props = {sg: c / total_orthologs for sg, c in ortholog_counts.items()}

        # Determine assignment based on method
        assigned_sg: str | None = None
        confidence = 0.0
        evidence_type = EvidenceType.MARKERS

        if self.method == AssignmentMethod.MARKERS:
            if total_markers >= self.min_markers:
                assigned_sg, confidence = self._assign_by_proportion(
                    marker_props, total_markers
                )
            evidence_type = EvidenceType.MARKERS

        elif self.method == AssignmentMethod.ORTHOLOGS:
            if total_orthologs >= self.min_orthologs:
                assigned_sg, confidence = self._assign_by_proportion(
                    ortholog_props, total_orthologs
                )
            evidence_type = EvidenceType.ORTHOLOGS

        elif self.method == AssignmentMethod.COMBINED:
            assigned_sg, confidence, evidence_type = self._assign_combined(
                marker_props, ortholog_props,
                total_markers, total_orthologs,
            )

        return SubgenomeAssignment(
            contig=contig_name,
            length=contig_length,
            subgenome=assigned_sg,
            confidence=confidence,
            evidence=evidence_type,
            marker_support=marker_counts if marker_counts else None,
            ortholog_support=ortholog_counts if ortholog_counts else None,
            marker_proportions=marker_props if marker_props else None,
            ortholog_proportions=ortholog_props if ortholog_props else None,
            n_genes=n_genes,
        )

    def _assign_by_proportion(
        self,
        proportions: dict[str, float],
        n_evidence: int,
    ) -> tuple[str | None, float]:
        """Assign based on proportions.

        Parameters
        ----------
        proportions : dict[str, float]
            Proportions per subgenome.
        n_evidence : int
            Total evidence count.

        Returns
        -------
        tuple[str | None, float]
            (assigned subgenome, confidence)
        """
        if not proportions:
            return None, 0.0

        # Find majority subgenome
        majority_sg = max(proportions, key=proportions.get)
        majority_prop = proportions[majority_sg]

        if majority_prop >= self.min_proportion:
            # Calculate confidence
            import numpy as np
            size_factor = 1 / (1 + np.exp(-(n_evidence - self.min_markers) / 2))
            confidence = 0.6 * majority_prop + 0.4 * size_factor
            return majority_sg, round(min(confidence, 1.0), 3)

        return None, 0.0

    def _assign_combined(
        self,
        marker_props: dict[str, float],
        ortholog_props: dict[str, float],
        n_markers: int,
        n_orthologs: int,
    ) -> tuple[str | None, float, EvidenceType]:
        """Assign using combined evidence.

        Parameters
        ----------
        marker_props : dict[str, float]
            Marker proportions.
        ortholog_props : dict[str, float]
            Ortholog proportions.
        n_markers : int
            Total markers.
        n_orthologs : int
            Total orthologs.

        Returns
        -------
        tuple[str | None, float, EvidenceType]
            (assigned subgenome, confidence, evidence type)
        """
        has_markers = n_markers >= self.min_markers
        has_orthologs = n_orthologs >= self.min_orthologs

        if not has_markers and not has_orthologs:
            return None, 0.0, EvidenceType.MARKERS

        # Combine proportions
        combined_props: dict[str, float] = dict.fromkeys(self.subgenomes, 0.0)

        if has_markers and has_orthologs:
            for sg in self.subgenomes:
                combined_props[sg] = (
                    self.marker_weight * marker_props.get(sg, 0.0) +
                    (1 - self.marker_weight) * ortholog_props.get(sg, 0.0)
                )
            evidence_type = EvidenceType.BOTH
        elif has_markers:
            combined_props = marker_props
            evidence_type = EvidenceType.MARKERS
        else:
            combined_props = ortholog_props
            evidence_type = EvidenceType.ORTHOLOGS

        # Find majority
        majority_sg = max(combined_props, key=combined_props.get)
        majority_prop = combined_props[majority_sg]

        if majority_prop >= self.min_proportion:
            # Confidence based on both evidence types
            import numpy as np
            n_evidence = n_markers + n_orthologs
            size_factor = 1 / (1 + np.exp(-(n_evidence - self.min_markers) / 3))
            confidence = 0.5 * majority_prop + 0.3 * size_factor

            # Bonus for concordant evidence
            if has_markers and has_orthologs:
                marker_majority = max(marker_props, key=marker_props.get)
                ortholog_majority = max(ortholog_props, key=ortholog_props.get)
                if marker_majority == ortholog_majority == majority_sg:
                    confidence += 0.2

            return majority_sg, round(min(confidence, 1.0), 3), evidence_type

        return None, 0.0, evidence_type


def assign_subgenomes(
    assembly: Assembly,
    subgenomes: list[str],
    marker_hits: list[MarkerHit] | None = None,
    orthologs: OrthoFinderResults | None = None,
    gene_to_contig: dict[str, str] | None = None,
    method: str = "markers",
    min_markers: int = 5,
    min_proportion: float = 0.7,
) -> SubgenomeAssignmentResult:
    """Convenience function for subgenome assignment.

    Parameters
    ----------
    assembly : Assembly
        Target assembly.
    subgenomes : list[str]
        Expected subgenomes.
    marker_hits : list[MarkerHit] | None
        Subgenome-diagnostic marker hits.
    orthologs : OrthoFinderResults | None
        OrthoFinder results.
    gene_to_contig : dict[str, str] | None
        Gene to contig mapping.
    method : str
        Assignment method.
    min_markers : int
        Minimum markers for assignment.
    min_proportion : float
        Minimum proportion for assignment.

    Returns
    -------
    SubgenomeAssignmentResult
        Assignment results.
    """
    assigner = SubgenomeAssigner(
        subgenomes=subgenomes,
        method=method,
        min_markers=min_markers,
        min_proportion=min_proportion,
    )
    return assigner.assign(
        assembly,
        marker_hits=marker_hits,
        orthologs=orthologs,
        gene_to_contig=gene_to_contig,
    )
