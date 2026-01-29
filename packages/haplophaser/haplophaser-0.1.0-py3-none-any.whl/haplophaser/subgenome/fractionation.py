"""
Fractionation analysis for paleopolyploid genomes.

Analyzes biased gene loss (fractionation) between subgenomes after
whole-genome duplication. In paleopolyploids like maize, one subgenome
(the "dominant" subgenome) typically retains more genes.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from scipy import stats

from haplophaser.subgenome.models import (
    HomeologPair,
    SubgenomeAssignment,
    SubgenomeConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class GeneInfo:
    """Gene information for fractionation analysis.

    Parameters
    ----------
    gene_id : str
        Gene identifier.
    chrom : str
        Chromosome.
    start : int
        Start position.
    end : int
        End position.
    subgenome : str, optional
        Assigned subgenome.
    has_homeolog : bool
        Whether gene has a homeolog partner.
    """

    gene_id: str
    chrom: str
    start: int
    end: int
    subgenome: str | None = None
    has_homeolog: bool = False


@dataclass
class ChromosomeFractionation:
    """Fractionation statistics for a chromosome.

    Parameters
    ----------
    chrom : str
        Chromosome name.
    genes_by_subgenome : dict[str, int]
        Gene counts per subgenome.
    singletons_by_subgenome : dict[str, int]
        Singleton gene counts per subgenome.
    pairs : int
        Number of retained homeolog pairs.
    """

    chrom: str
    genes_by_subgenome: dict[str, int]
    singletons_by_subgenome: dict[str, int]
    pairs: int

    @property
    def total_genes(self) -> int:
        """Total genes on chromosome."""
        return sum(self.genes_by_subgenome.values())

    @property
    def retention_by_subgenome(self) -> dict[str, float]:
        """Retention rate per subgenome."""
        total = self.total_genes + sum(self.singletons_by_subgenome.values())
        if total == 0:
            return {}
        return {
            sg: count / total
            for sg, count in self.genes_by_subgenome.items()
        }


@dataclass
class FractionationReport:
    """Complete fractionation analysis report.

    Parameters
    ----------
    total_genes : int
        Total number of genes analyzed.
    genes_by_subgenome : dict[str, int]
        Gene counts per subgenome.
    singleton_genes : int
        Genes that lost their homeolog partner.
    retained_pairs : int
        Homeolog pairs where both copies retained.
    retention_by_subgenome : dict[str, float]
        Retention rate per subgenome.
    fractionation_bias : float
        Ratio of dominant to recessive subgenome genes.
    bias_pvalue : float
        Statistical significance of bias.
    fractionation_by_chromosome : dict[str, ChromosomeFractionation]
        Per-chromosome statistics.
    enriched_functions_retained : list[str] | None
        GO terms enriched in retained genes.
    enriched_functions_lost : list[str] | None
        GO terms enriched in lost genes.
    config : SubgenomeConfig
        Configuration used.
    """

    total_genes: int
    genes_by_subgenome: dict[str, int]
    singleton_genes: int
    retained_pairs: int
    retention_by_subgenome: dict[str, float]
    fractionation_bias: float
    bias_pvalue: float
    fractionation_by_chromosome: dict[str, ChromosomeFractionation]
    enriched_functions_retained: list[str] | None = None
    enriched_functions_lost: list[str] | None = None
    config: SubgenomeConfig | None = None

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns
        -------
        str
            Summary text.
        """
        lines = [
            "Fractionation Analysis Summary",
            "=" * 40,
            f"Total genes analyzed: {self.total_genes:,}",
            "",
            "Gene counts by subgenome:",
        ]

        for sg, count in sorted(self.genes_by_subgenome.items()):
            pct = 100 * count / self.total_genes if self.total_genes > 0 else 0
            lines.append(f"  {sg}: {count:,} ({pct:.1f}%)")

        lines.extend([
            "",
            f"Retained homeolog pairs: {self.retained_pairs:,}",
            f"Singleton genes: {self.singleton_genes:,}",
            "",
            "Retention rates by subgenome:",
        ])

        for sg, rate in sorted(self.retention_by_subgenome.items()):
            lines.append(f"  {sg}: {rate:.1%}")

        lines.extend([
            "",
            f"Fractionation bias (SG1/SG2): {self.fractionation_bias:.3f}",
            f"Bias p-value: {self.bias_pvalue:.2e}",
        ])

        if self.fractionation_bias > 1.0:
            dominant = max(self.genes_by_subgenome, key=self.genes_by_subgenome.get)
            lines.append(f"Dominant subgenome: {dominant}")

        return "\n".join(lines)

    def to_dataframe(self):
        """Convert to pandas DataFrame.

        Returns
        -------
        pd.DataFrame
            Fractionation data.
        """
        import pandas as pd

        rows = []
        for chrom, chrom_data in self.fractionation_by_chromosome.items():
            for sg, count in chrom_data.genes_by_subgenome.items():
                rows.append({
                    "chromosome": chrom,
                    "subgenome": sg,
                    "gene_count": count,
                    "singleton_count": chrom_data.singletons_by_subgenome.get(sg, 0),
                    "pairs": chrom_data.pairs,
                })

        return pd.DataFrame(rows)


class FractionationAnalyzer:
    """Analyze fractionation patterns between subgenomes.

    Examines biased gene loss following whole-genome duplication.
    The dominant subgenome typically shows:
    - Higher gene retention
    - Higher expression levels
    - Retention of functionally important genes

    Parameters
    ----------
    config : SubgenomeConfig
        Subgenome configuration.

    Examples
    --------
    >>> config = SubgenomeConfig.maize_default()
    >>> analyzer = FractionationAnalyzer(config)
    >>> report = analyzer.analyze(
    ...     genes="genes.gff3",
    ...     subgenome_assignments="subgenome_assignments.bed",
    ...     homeolog_pairs="homeolog_pairs.tsv",
    ... )
    >>> print(report.summary())
    """

    def __init__(self, config: SubgenomeConfig) -> None:
        self.config = config

    def analyze(
        self,
        genes: Path | str,
        subgenome_assignments: Path | str | list[SubgenomeAssignment],
        homeolog_pairs: Path | str | list[HomeologPair] | None = None,
        outgroup_genes: Path | str | None = None,
        go_annotations: Path | str | None = None,
    ) -> FractionationReport:
        """Analyze fractionation patterns.

        Parameters
        ----------
        genes : Path or str
            GFF3 file with gene annotations.
        subgenome_assignments : Path, str, or list
            Subgenome assignments (BED file or list).
        homeolog_pairs : Path, str, or list, optional
            Known homeolog pairs.
        outgroup_genes : Path or str, optional
            Outgroup gene annotations for ancestral state.
        go_annotations : Path or str, optional
            GO annotations for enrichment analysis.

        Returns
        -------
        FractionationReport
            Fractionation analysis results.
        """
        # Load genes
        gene_list = self._load_genes(genes)
        logger.info(f"Loaded {len(gene_list)} genes")

        # Load subgenome assignments
        if isinstance(subgenome_assignments, (str, Path)):
            assignments = self._load_assignments(subgenome_assignments)
        else:
            assignments = subgenome_assignments

        # Assign genes to subgenomes
        gene_list = self._assign_genes_to_subgenomes(gene_list, assignments)

        # Load homeolog pairs if provided
        homeologs: list[HomeologPair] = []
        if homeolog_pairs:
            if isinstance(homeolog_pairs, (str, Path)):
                homeologs = self._load_homeolog_pairs(homeolog_pairs)
            else:
                homeologs = homeolog_pairs

        # Mark genes with homeologs
        paired_genes = set()
        for pair in homeologs:
            paired_genes.add(pair.gene1_id)
            paired_genes.add(pair.gene2_id)

        for gene in gene_list:
            gene.has_homeolog = gene.gene_id in paired_genes

        # Calculate statistics
        return self._calculate_fractionation(gene_list, homeologs, go_annotations)

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

                # Parse attributes
                attrs = {}
                for attr in fields[8].split(";"):
                    if "=" in attr:
                        key, value = attr.split("=", 1)
                        attrs[key] = value

                gene_id = attrs.get("ID", attrs.get("Name", ""))
                if not gene_id:
                    continue

                # Only add genes, not mRNAs of same genes
                if feature_type == "gene" or not any(g.gene_id == gene_id for g in genes):
                    genes.append(GeneInfo(
                        gene_id=gene_id,
                        chrom=chrom,
                        start=start,
                        end=end,
                    ))

        return genes

    def _load_assignments(
        self,
        path: Path | str,
    ) -> list[SubgenomeAssignment]:
        """Load subgenome assignments from BED.

        Parameters
        ----------
        path : Path or str
            Path to BED file.

        Returns
        -------
        list[SubgenomeAssignment]
            Assignments.
        """
        path = Path(path)
        assignments = []

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
                subgenome = fields[3].split("|")[0]  # Handle name|evidence format

                assignments.append(SubgenomeAssignment(
                    chrom=chrom,
                    start=start,
                    end=end,
                    subgenome=subgenome,
                    confidence=1.0,
                    evidence="loaded",
                ))

        return assignments

    def _assign_genes_to_subgenomes(
        self,
        genes: list[GeneInfo],
        assignments: list[SubgenomeAssignment],
    ) -> list[GeneInfo]:
        """Assign each gene to a subgenome.

        Parameters
        ----------
        genes : list[GeneInfo]
            Genes to assign.
        assignments : list[SubgenomeAssignment]
            Subgenome assignments.

        Returns
        -------
        list[GeneInfo]
            Genes with subgenome assignments.
        """
        # Index assignments by chromosome
        by_chrom: dict[str, list[SubgenomeAssignment]] = defaultdict(list)
        for a in assignments:
            by_chrom[a.chrom].append(a)

        for chrom in by_chrom:
            by_chrom[chrom].sort(key=lambda x: x.start)

        # Assign each gene
        for gene in genes:
            chrom_assignments = by_chrom.get(gene.chrom, [])
            gene_mid = (gene.start + gene.end) // 2

            for a in chrom_assignments:
                if a.start <= gene_mid < a.end:
                    gene.subgenome = a.subgenome
                    break

        assigned = sum(1 for g in genes if g.subgenome is not None)
        logger.info(f"Assigned {assigned}/{len(genes)} genes to subgenomes")

        return genes

    def _load_homeolog_pairs(
        self,
        path: Path | str,
    ) -> list[HomeologPair]:
        """Load homeolog pairs from TSV.

        Parameters
        ----------
        path : Path or str
            Path to TSV file.

        Returns
        -------
        list[HomeologPair]
            Homeolog pairs.
        """
        path = Path(path)
        pairs = []

        with open(path) as f:
            header = None
            for line in f:
                if line.startswith("#"):
                    continue

                fields = line.strip().split("\t")
                if header is None:
                    header = fields
                    continue

                row = dict(zip(header, fields, strict=False))

                pair = HomeologPair(
                    gene1_id=row.get("gene1_id", row.get("gene1", "")),
                    gene1_chrom=row.get("gene1_chrom", ""),
                    gene1_subgenome=row.get("gene1_subgenome", ""),
                    gene2_id=row.get("gene2_id", row.get("gene2", "")),
                    gene2_chrom=row.get("gene2_chrom", ""),
                    gene2_subgenome=row.get("gene2_subgenome", ""),
                    ks=float(row["ks"]) if row.get("ks") else None,
                    ka=float(row["ka"]) if row.get("ka") else None,
                    synteny_support=row.get("synteny_support", "").lower() == "true",
                    sequence_identity=float(row.get("sequence_identity", 0)),
                    confidence=float(row.get("confidence", 1.0)),
                )
                pairs.append(pair)

        logger.info(f"Loaded {len(pairs)} homeolog pairs")
        return pairs

    def _calculate_fractionation(
        self,
        genes: list[GeneInfo],
        homeologs: list[HomeologPair],
        go_annotations: Path | str | None,
    ) -> FractionationReport:
        """Calculate fractionation statistics.

        Parameters
        ----------
        genes : list[GeneInfo]
            Genes with subgenome assignments.
        homeologs : list[HomeologPair]
            Homeolog pairs.
        go_annotations : Path or str, optional
            GO annotations file.

        Returns
        -------
        FractionationReport
            Analysis results.
        """
        # Count genes by subgenome
        genes_by_sg: dict[str, int] = defaultdict(int)
        singletons_by_sg: dict[str, int] = defaultdict(int)

        for gene in genes:
            if gene.subgenome:
                genes_by_sg[gene.subgenome] += 1
                if not gene.has_homeolog:
                    singletons_by_sg[gene.subgenome] += 1

        # Calculate per-chromosome statistics
        by_chromosome: dict[str, ChromosomeFractionation] = {}

        # Group genes by chromosome
        genes_by_chrom: dict[str, list[GeneInfo]] = defaultdict(list)
        for gene in genes:
            genes_by_chrom[gene.chrom].append(gene)

        # Group homeologs by chromosome
        pairs_by_chrom: dict[str, int] = defaultdict(int)
        for pair in homeologs:
            # Count in first gene's chromosome
            pairs_by_chrom[pair.gene1_chrom] += 1

        for chrom, chrom_genes in genes_by_chrom.items():
            chrom_sg_counts: dict[str, int] = defaultdict(int)
            chrom_singleton_counts: dict[str, int] = defaultdict(int)

            for gene in chrom_genes:
                if gene.subgenome:
                    chrom_sg_counts[gene.subgenome] += 1
                    if not gene.has_homeolog:
                        chrom_singleton_counts[gene.subgenome] += 1

            by_chromosome[chrom] = ChromosomeFractionation(
                chrom=chrom,
                genes_by_subgenome=dict(chrom_sg_counts),
                singletons_by_subgenome=dict(chrom_singleton_counts),
                pairs=pairs_by_chrom.get(chrom, 0),
            )

        # Calculate overall statistics
        total_genes = len([g for g in genes if g.subgenome])
        total_singletons = sum(singletons_by_sg.values())
        retained_pairs = len(homeologs)

        # Calculate retention rates
        retention: dict[str, float] = {}
        for sg in self.config.subgenome_names:
            sg_total = genes_by_sg.get(sg, 0) + singletons_by_sg.get(sg, 0)
            if sg_total > 0:
                retention[sg] = genes_by_sg.get(sg, 0) / sg_total
            else:
                retention[sg] = 0.0

        # Calculate fractionation bias
        sg_counts = [genes_by_sg.get(sg, 0) for sg in self.config.subgenome_names]
        if len(sg_counts) >= 2 and min(sg_counts) > 0:
            fractionation_bias = max(sg_counts) / min(sg_counts)
        else:
            fractionation_bias = 1.0

        # Statistical test for bias (chi-square)
        if len(sg_counts) >= 2 and sum(sg_counts) > 0:
            expected = [sum(sg_counts) / len(sg_counts)] * len(sg_counts)
            chi2, pvalue = stats.chisquare(sg_counts, expected)
        else:
            pvalue = 1.0

        # GO enrichment analysis would go here
        enriched_retained = None
        enriched_lost = None

        return FractionationReport(
            total_genes=total_genes,
            genes_by_subgenome=dict(genes_by_sg),
            singleton_genes=total_singletons,
            retained_pairs=retained_pairs,
            retention_by_subgenome=retention,
            fractionation_bias=fractionation_bias,
            bias_pvalue=pvalue,
            fractionation_by_chromosome=by_chromosome,
            enriched_functions_retained=enriched_retained,
            enriched_functions_lost=enriched_lost,
            config=self.config,
        )


def analyze_fractionation(
    genes: Path | str,
    subgenome_assignments: Path | str,
    homeolog_pairs: Path | str | None = None,
    config: SubgenomeConfig | None = None,
) -> FractionationReport:
    """Convenience function for fractionation analysis.

    Parameters
    ----------
    genes : Path or str
        GFF3 file with gene annotations.
    subgenome_assignments : Path or str
        Subgenome assignments BED file.
    homeolog_pairs : Path or str, optional
        Homeolog pairs TSV file.
    config : SubgenomeConfig, optional
        Subgenome configuration.

    Returns
    -------
    FractionationReport
        Analysis results.
    """
    if config is None:
        config = SubgenomeConfig.maize_default()

    analyzer = FractionationAnalyzer(config)
    return analyzer.analyze(
        genes=genes,
        subgenome_assignments=subgenome_assignments,
        homeolog_pairs=homeolog_pairs,
    )


def write_fractionation_report(
    report: FractionationReport,
    output: Path | str,
) -> None:
    """Write fractionation report to file.

    Parameters
    ----------
    report : FractionationReport
        Report to write.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        f.write(report.summary())
        f.write("\n\n")
        f.write("Per-chromosome statistics:\n")
        f.write("-" * 40 + "\n")

        header = ["chromosome"]
        if report.config:
            header.extend(report.config.subgenome_names)
        header.extend(["pairs", "total"])
        f.write("\t".join(header) + "\n")

        for chrom in sorted(report.fractionation_by_chromosome.keys()):
            data = report.fractionation_by_chromosome[chrom]
            row = [chrom]
            if report.config:
                for sg in report.config.subgenome_names:
                    row.append(str(data.genes_by_subgenome.get(sg, 0)))
            row.append(str(data.pairs))
            row.append(str(data.total_genes))
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote fractionation report to {output}")
