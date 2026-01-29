"""
Ortholog-based subgenome assignment.

Assigns genes and genomic regions to subgenomes based on phylogenetic
placement using orthologs. Uses OrthoFinder results and outgroup
comparisons to determine which subgenome each gene belongs to.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from haplophaser.subgenome.models import (
    GeneSubgenomeCall,
    SubgenomeAssignment,
    SubgenomeAssignmentResult,
    SubgenomeConfig,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class OrthologAssignmentParams:
    """Parameters for ortholog-based assignment.

    Parameters
    ----------
    tree_method : str
        Method for placement: 'gene_trees', 'species_tree', 'distance'.
    min_bootstrap : float
        Minimum bootstrap support for tree-based placement.
    min_genes_per_region : int
        Minimum genes to call a region.
    region_size : int
        Size of regions for aggregation.
    """

    tree_method: str = "gene_trees"
    min_bootstrap: float = 70.0
    min_genes_per_region: int = 3
    region_size: int = 500_000


@dataclass
class GeneInfo:
    """Gene annotation information.

    Parameters
    ----------
    gene_id : str
        Gene identifier.
    chrom : str
        Chromosome.
    start : int
        Start position (0-based).
    end : int
        End position (exclusive).
    strand : str
        Strand (+/-).
    """

    gene_id: str
    chrom: str
    start: int
    end: int
    strand: str = "+"


class OrthologSubgenomeAssigner:
    """Assign subgenomes using ortholog phylogenetic placement.

    For each gene in the query genome, determines which subgenome it
    belongs to by analyzing its phylogenetic relationship to reference
    genes from known subgenomes and outgroup species.

    Parameters
    ----------
    config : SubgenomeConfig
        Subgenome configuration.
    tree_method : str
        Placement method: 'gene_trees', 'species_tree', 'distance'.
    min_bootstrap : float
        Minimum bootstrap support.

    Examples
    --------
    >>> config = SubgenomeConfig.maize_default()
    >>> assigner = OrthologSubgenomeAssigner(config)
    >>> result = assigner.assign(
    ...     query_genes="genes.gff3",
    ...     query_proteins="proteins.faa",
    ...     orthofinder_dir="OrthoFinder/Results/",
    ...     outgroup="Sorghum_bicolor",
    ... )
    """

    def __init__(
        self,
        config: SubgenomeConfig,
        tree_method: str = "gene_trees",
        min_bootstrap: float = 70.0,
    ) -> None:
        self.config = config
        self.params = OrthologAssignmentParams(
            tree_method=tree_method,
            min_bootstrap=min_bootstrap,
        )

    def assign(
        self,
        query_genes: Path | str,
        query_proteins: Path | str | None = None,
        orthofinder_dir: Path | str | None = None,
        orthogroups: Path | str | None = None,
        gene_trees_dir: Path | str | None = None,
        outgroup: str | None = None,
        reference_species: str | None = None,
        reference_assignments: Path | str | None = None,
    ) -> SubgenomeAssignmentResult:
        """Assign subgenomes using ortholog information.

        Parameters
        ----------
        query_genes : Path or str
            GFF3 file with query gene annotations.
        query_proteins : Path or str, optional
            FASTA with query proteins.
        orthofinder_dir : Path or str, optional
            OrthoFinder results directory.
        orthogroups : Path or str, optional
            Orthogroups.tsv file.
        gene_trees_dir : Path or str, optional
            Directory with gene trees.
        outgroup : str, optional
            Outgroup species name.
        reference_species : str, optional
            Reference species name.
        reference_assignments : Path or str, optional
            Known assignments for reference genes.

        Returns
        -------
        SubgenomeAssignmentResult
            Subgenome assignments.
        """
        # Load gene annotations
        genes = self._load_genes(query_genes)
        logger.info(f"Loaded {len(genes)} genes from {query_genes}")

        # Load ortholog information
        orthogroup_assignments = self._load_orthogroups(
            orthofinder_dir, orthogroups
        )

        # Get outgroup for rooting
        outgroup_species = outgroup or (
            self.config.outgroup_species[0] if self.config.outgroup_species else None
        )

        # Load reference gene assignments if provided
        ref_gene_assignments: dict[str, str] = {}
        if reference_assignments:
            ref_gene_assignments = self._load_reference_gene_assignments(
                reference_assignments
            )

        # Assign each gene
        gene_calls = []
        for gene in genes:
            call = self._assign_gene(
                gene,
                orthogroup_assignments,
                ref_gene_assignments,
                outgroup_species,
                gene_trees_dir,
            )
            gene_calls.append(call)

        # Aggregate to regions
        assignments = self._aggregate_to_regions(gene_calls)

        return SubgenomeAssignmentResult(
            query_name=Path(query_genes).stem,
            config=self.config,
            assignments=assignments,
            method="orthologs",
            parameters={
                "tree_method": self.params.tree_method,
                "min_bootstrap": self.params.min_bootstrap,
                "outgroup": outgroup_species,
            },
        )

    def assign_genes(
        self,
        query_genes: Path | str,
        orthofinder_dir: Path | str | None = None,
        orthogroups: Path | str | None = None,
        reference_assignments: Path | str | None = None,
        outgroup: str | None = None,
    ) -> list[GeneSubgenomeCall]:
        """Assign subgenomes to individual genes.

        Parameters
        ----------
        query_genes : Path or str
            GFF3 file with gene annotations.
        orthofinder_dir : Path or str, optional
            OrthoFinder results directory.
        orthogroups : Path or str, optional
            Orthogroups.tsv file.
        reference_assignments : Path or str, optional
            Known assignments for reference genes.
        outgroup : str, optional
            Outgroup species.

        Returns
        -------
        list[GeneSubgenomeCall]
            Gene-level assignments.
        """
        genes = self._load_genes(query_genes)
        orthogroup_assignments = self._load_orthogroups(orthofinder_dir, orthogroups)

        ref_gene_assignments: dict[str, str] = {}
        if reference_assignments:
            ref_gene_assignments = self._load_reference_gene_assignments(
                reference_assignments
            )

        outgroup_species = outgroup or (
            self.config.outgroup_species[0] if self.config.outgroup_species else None
        )

        gene_calls = []
        for gene in genes:
            call = self._assign_gene(
                gene,
                orthogroup_assignments,
                ref_gene_assignments,
                outgroup_species,
                None,
            )
            gene_calls.append(call)

        assigned = sum(1 for c in gene_calls if c.is_assigned)
        logger.info(f"Assigned {assigned}/{len(gene_calls)} genes to subgenomes")

        return gene_calls

    def _load_genes(self, gff_path: Path | str) -> list[GeneInfo]:
        """Load gene annotations from GFF3.

        Parameters
        ----------
        gff_path : Path or str
            Path to GFF3 file.

        Returns
        -------
        list[GeneInfo]
            Gene annotations.
        """
        path = Path(gff_path)
        genes = []

        with open(path) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                fields = line.strip().split("\t")
                if len(fields) < 9:
                    continue

                feature_type = fields[2].lower()
                if feature_type not in ("gene", "mrna"):
                    continue

                chrom = fields[0]
                start = int(fields[3]) - 1  # Convert to 0-based
                end = int(fields[4])
                strand = fields[6]

                # Parse attributes
                attrs = {}
                for attr in fields[8].split(";"):
                    if "=" in attr:
                        key, value = attr.split("=", 1)
                        attrs[key] = value

                gene_id = attrs.get("ID", attrs.get("Name", ""))
                if not gene_id:
                    continue

                genes.append(GeneInfo(
                    gene_id=gene_id,
                    chrom=chrom,
                    start=start,
                    end=end,
                    strand=strand,
                ))

        return genes

    def _load_orthogroups(
        self,
        orthofinder_dir: Path | str | None,
        orthogroups_file: Path | str | None,
    ) -> dict[str, str]:
        """Load orthogroup assignments.

        Parameters
        ----------
        orthofinder_dir : Path or str, optional
            OrthoFinder results directory.
        orthogroups_file : Path or str, optional
            Direct path to Orthogroups.tsv.

        Returns
        -------
        dict[str, str]
            Gene ID to orthogroup mapping.
        """
        gene_to_og: dict[str, str] = {}

        if orthogroups_file:
            path = Path(orthogroups_file)
        elif orthofinder_dir:
            path = Path(orthofinder_dir) / "Orthogroups" / "Orthogroups.tsv"
            if not path.exists():
                path = Path(orthofinder_dir) / "Orthogroups.tsv"
        else:
            logger.warning("No orthogroup information provided")
            return gene_to_og

        if not path.exists():
            logger.warning(f"Orthogroups file not found: {path}")
            return gene_to_og

        with open(path) as f:
            header = None
            for line in f:
                fields = line.strip().split("\t")
                if header is None:
                    header = fields
                    continue

                og_id = fields[0]
                for species_genes in fields[1:]:
                    if not species_genes:
                        continue
                    for gene in species_genes.split(", "):
                        gene = gene.strip()
                        if gene:
                            gene_to_og[gene] = og_id

        logger.info(f"Loaded {len(gene_to_og)} gene orthogroup assignments")
        return gene_to_og

    def _load_reference_gene_assignments(
        self,
        path: Path | str,
    ) -> dict[str, str]:
        """Load known subgenome assignments for reference genes.

        Parameters
        ----------
        path : Path or str
            TSV file with gene_id, subgenome columns.

        Returns
        -------
        dict[str, str]
            Gene ID to subgenome mapping.
        """
        path = Path(path)
        assignments: dict[str, str] = {}

        with open(path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                fields = line.strip().split("\t")
                if len(fields) >= 2:
                    gene_id = fields[0]
                    subgenome = fields[1]
                    assignments[gene_id] = subgenome

        logger.info(f"Loaded {len(assignments)} reference gene assignments")
        return assignments

    def _assign_gene(
        self,
        gene: GeneInfo,
        orthogroup_assignments: dict[str, str],
        ref_gene_assignments: dict[str, str],
        outgroup_species: str | None,
        gene_trees_dir: Path | str | None,
    ) -> GeneSubgenomeCall:
        """Assign a single gene to a subgenome.

        Parameters
        ----------
        gene : GeneInfo
            Gene to assign.
        orthogroup_assignments : dict
            Gene to orthogroup mapping.
        ref_gene_assignments : dict
            Reference gene subgenome assignments.
        outgroup_species : str, optional
            Outgroup species.
        gene_trees_dir : Path or str, optional
            Directory with gene trees.

        Returns
        -------
        GeneSubgenomeCall
            Gene assignment.
        """
        og = orthogroup_assignments.get(gene.gene_id)

        if og is None:
            return GeneSubgenomeCall(
                gene_id=gene.gene_id,
                chrom=gene.chrom,
                start=gene.start,
                end=gene.end,
                orthogroup="",
                subgenome=None,
                confidence=0.0,
            )

        # Find reference genes in same orthogroup with known assignments
        og_ref_genes = [
            (g, sg) for g, og2 in orthogroup_assignments.items()
            if og2 == og and g in ref_gene_assignments
            for sg in [ref_gene_assignments[g]]
        ]

        if not og_ref_genes:
            return GeneSubgenomeCall(
                gene_id=gene.gene_id,
                chrom=gene.chrom,
                start=gene.start,
                end=gene.end,
                orthogroup=og,
                subgenome=None,
                confidence=0.0,
            )

        # Count subgenome assignments in orthogroup
        sg_counts: dict[str, int] = defaultdict(int)
        for _, sg in og_ref_genes:
            sg_counts[sg] += 1

        # Use majority vote
        total = sum(sg_counts.values())
        majority_sg = max(sg_counts, key=sg_counts.get)
        proportion = sg_counts[majority_sg] / total

        # Confidence based on proportion and total evidence
        confidence = 0.5 * proportion
        if total >= 3:
            confidence += 0.2
        if total >= 5:
            confidence += 0.1

        # Try gene tree for better confidence
        tree_support = None
        if gene_trees_dir and self.params.tree_method == "gene_trees":
            tree_support = self._get_tree_support(gene.gene_id, og, gene_trees_dir)
            if tree_support and tree_support >= self.params.min_bootstrap:
                confidence = min(confidence + 0.2, 1.0)

        return GeneSubgenomeCall(
            gene_id=gene.gene_id,
            chrom=gene.chrom,
            start=gene.start,
            end=gene.end,
            orthogroup=og,
            subgenome=majority_sg if proportion >= 0.6 else None,
            confidence=round(confidence, 3),
            tree_support=tree_support,
        )

    def _get_tree_support(
        self,
        gene_id: str,
        orthogroup: str,
        gene_trees_dir: Path | str,
    ) -> float | None:
        """Get bootstrap support from gene tree.

        Parameters
        ----------
        gene_id : str
            Gene identifier.
        orthogroup : str
            Orthogroup ID.
        gene_trees_dir : Path or str
            Directory with gene trees.

        Returns
        -------
        float or None
            Bootstrap support if available.
        """
        # This would parse Newick trees and find bootstrap support
        # for the clade containing this gene
        # Placeholder implementation
        return None

    def _aggregate_to_regions(
        self,
        gene_calls: list[GeneSubgenomeCall],
    ) -> list[SubgenomeAssignment]:
        """Aggregate gene calls to genomic regions.

        Parameters
        ----------
        gene_calls : list[GeneSubgenomeCall]
            Gene-level calls.

        Returns
        -------
        list[SubgenomeAssignment]
            Region-level assignments.
        """
        # Group by chromosome
        by_chrom: dict[str, list[GeneSubgenomeCall]] = defaultdict(list)
        for call in gene_calls:
            if call.is_assigned:
                by_chrom[call.chrom].append(call)

        assignments = []

        for chrom, chrom_calls in by_chrom.items():
            # Sort by position
            sorted_calls = sorted(chrom_calls, key=lambda x: x.start)

            # Group into regions
            region_size = self.params.region_size
            current_start = 0
            current_calls: list[GeneSubgenomeCall] = []

            for call in sorted_calls:
                region_start = (call.start // region_size) * region_size

                if region_start != current_start and current_calls:
                    # Finalize previous region
                    assignment = self._calls_to_assignment(
                        chrom, current_start, current_start + region_size, current_calls
                    )
                    if assignment:
                        assignments.append(assignment)
                    current_calls = []

                current_start = region_start
                current_calls.append(call)

            # Finalize last region
            if current_calls:
                assignment = self._calls_to_assignment(
                    chrom, current_start, current_start + region_size, current_calls
                )
                if assignment:
                    assignments.append(assignment)

        return sorted(assignments, key=lambda x: (x.chrom, x.start))

    def _calls_to_assignment(
        self,
        chrom: str,
        start: int,
        end: int,
        calls: list[GeneSubgenomeCall],
    ) -> SubgenomeAssignment | None:
        """Convert gene calls to a region assignment.

        Parameters
        ----------
        chrom : str
            Chromosome.
        start : int
            Region start.
        end : int
            Region end.
        calls : list[GeneSubgenomeCall]
            Gene calls in region.

        Returns
        -------
        SubgenomeAssignment or None
            Assignment if sufficient evidence.
        """
        if len(calls) < self.params.min_genes_per_region:
            return None

        # Count subgenomes
        sg_counts: dict[str, int] = defaultdict(int)
        confidences: list[float] = []

        for call in calls:
            if call.subgenome:
                sg_counts[call.subgenome] += 1
                confidences.append(call.confidence)

        if not sg_counts:
            return None

        majority_sg = max(sg_counts, key=sg_counts.get)
        total = sum(sg_counts.values())
        proportion = sg_counts[majority_sg] / total

        if proportion < 0.6:
            return None

        mean_confidence = float(np.mean(confidences)) if confidences else 0.0

        return SubgenomeAssignment(
            chrom=chrom,
            start=start,
            end=end,
            subgenome=majority_sg,
            confidence=round(mean_confidence * proportion, 3),
            evidence="orthologs",
            evidence_details={
                "n_genes": len(calls),
                "sg_counts": dict(sg_counts),
                "proportion": proportion,
            },
        )


def assign_by_orthologs(
    query_genes: Path | str,
    orthofinder_dir: Path | str | None = None,
    orthogroups: Path | str | None = None,
    config: SubgenomeConfig | None = None,
    outgroup: str | None = None,
) -> SubgenomeAssignmentResult:
    """Convenience function for ortholog-based assignment.

    Parameters
    ----------
    query_genes : Path or str
        GFF3 file with gene annotations.
    orthofinder_dir : Path or str, optional
        OrthoFinder results directory.
    orthogroups : Path or str, optional
        Orthogroups.tsv file.
    config : SubgenomeConfig, optional
        Subgenome configuration.
    outgroup : str, optional
        Outgroup species.

    Returns
    -------
    SubgenomeAssignmentResult
        Assignment result.
    """
    if config is None:
        config = SubgenomeConfig.maize_default()

    assigner = OrthologSubgenomeAssigner(config)

    return assigner.assign(
        query_genes=query_genes,
        orthofinder_dir=orthofinder_dir,
        orthogroups=orthogroups,
        outgroup=outgroup,
    )


def write_gene_calls(
    calls: list[GeneSubgenomeCall],
    output: Path | str,
) -> None:
    """Write gene subgenome calls to file.

    Parameters
    ----------
    calls : list[GeneSubgenomeCall]
        Gene calls to write.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        header = [
            "gene_id", "chrom", "start", "end", "orthogroup",
            "subgenome", "confidence", "tree_support",
        ]
        f.write("\t".join(header) + "\n")

        for call in calls:
            row = [
                call.gene_id,
                call.chrom,
                str(call.start),
                str(call.end),
                call.orthogroup,
                call.subgenome or ".",
                f"{call.confidence:.3f}",
                f"{call.tree_support:.1f}" if call.tree_support else ".",
            ]
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {len(calls)} gene calls to {output}")
