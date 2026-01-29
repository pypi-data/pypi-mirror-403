"""
Homeolog detection for paleopolyploid genomes.

Identifies homeologous gene pairs - genes derived from the whole-genome
duplication event, with one copy in each subgenome. Uses synteny and
sequence similarity to identify pairs and calculate Ks (synonymous
substitution rate) for dating.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from haplophaser.subgenome.models import (
    HomeologPair,
    HomeologResult,
    SubgenomeAssignment,
    SubgenomeConfig,
    SyntenyBlock,
)

logger = logging.getLogger(__name__)


@dataclass
class HomeologParams:
    """Parameters for homeolog detection.

    Parameters
    ----------
    method : str
        Detection method: 'synteny', 'sequence', 'combined'.
    max_ks : float
        Maximum Ks for homeologs (filters out paralogs from other events).
    min_identity : float
        Minimum sequence identity.
    require_synteny : bool
        Require synteny support for pairs.
    min_synteny_genes : int
        Minimum genes in synteny block for support.
    """

    method: str = "synteny"
    max_ks: float = 1.0
    min_identity: float = 0.3
    require_synteny: bool = False
    min_synteny_genes: int = 3


@dataclass
class GeneInfo:
    """Gene information for homeolog detection.

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
    strand : str
        Strand.
    subgenome : str, optional
        Assigned subgenome.
    protein_id : str, optional
        Protein ID for sequence lookup.
    """

    gene_id: str
    chrom: str
    start: int
    end: int
    strand: str = "+"
    subgenome: str | None = None
    protein_id: str | None = None


class HomeologFinder:
    """Find homeologous gene pairs between subgenomes.

    Identifies gene pairs that arose from the whole-genome duplication
    using synteny and/or sequence similarity evidence.

    Parameters
    ----------
    config : SubgenomeConfig
        Subgenome configuration.
    method : str
        Detection method: 'synteny', 'sequence', 'combined'.
    max_ks : float
        Maximum Ks value for homeologs.

    Examples
    --------
    >>> config = SubgenomeConfig.maize_default()
    >>> finder = HomeologFinder(config, method="synteny")
    >>> result = finder.find(
    ...     genes="genes.gff3",
    ...     subgenome_assignments="subgenome_assignments.bed",
    ...     synteny_blocks="synteny_blocks.tsv",
    ...     proteins="proteins.faa",
    ... )
    >>> print(f"Found {result.n_pairs} homeolog pairs")
    """

    def __init__(
        self,
        config: SubgenomeConfig,
        method: str = "synteny",
        max_ks: float = 1.0,
    ) -> None:
        self.config = config
        self.params = HomeologParams(
            method=method,
            max_ks=max_ks,
        )

    def find(
        self,
        genes: Path | str,
        subgenome_assignments: Path | str | list[SubgenomeAssignment],
        synteny_blocks: Path | str | list[SyntenyBlock] | None = None,
        proteins: Path | str | None = None,
        blast_results: Path | str | None = None,
        orthogroups: Path | str | None = None,
    ) -> HomeologResult:
        """Find homeolog pairs.

        Parameters
        ----------
        genes : Path or str
            GFF3 file with gene annotations.
        subgenome_assignments : Path, str, or list
            Subgenome assignments.
        synteny_blocks : Path, str, or list, optional
            Synteny blocks for synteny-based detection.
        proteins : Path or str, optional
            Protein FASTA for Ks calculation.
        blast_results : Path or str, optional
            Pre-computed BLAST results.
        orthogroups : Path or str, optional
            OrthoFinder orthogroups.

        Returns
        -------
        HomeologResult
            Detected homeolog pairs.
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

        # Load synteny blocks
        blocks: list[SyntenyBlock] = []
        if synteny_blocks:
            if isinstance(synteny_blocks, (str, Path)):
                from haplophaser.io.synteny import load_synteny
                blocks = load_synteny(synteny_blocks)
            else:
                blocks = synteny_blocks

        # Find pairs based on method
        if self.params.method == "synteny":
            pairs = self._find_by_synteny(gene_list, blocks)
        elif self.params.method == "sequence":
            pairs = self._find_by_sequence(gene_list, blast_results, orthogroups)
        else:  # combined
            synteny_pairs = self._find_by_synteny(gene_list, blocks)
            sequence_pairs = self._find_by_sequence(gene_list, blast_results, orthogroups)
            pairs = self._combine_pairs(synteny_pairs, sequence_pairs)

        # Calculate Ks if proteins provided
        if proteins:
            pairs = self._calculate_ks(pairs, proteins)

        # Filter by max Ks
        pairs = [p for p in pairs if p.ks is None or p.ks <= self.params.max_ks]

        logger.info(f"Found {len(pairs)} homeolog pairs")

        return HomeologResult(
            pairs=pairs,
            config=self.config,
            parameters={
                "method": self.params.method,
                "max_ks": self.params.max_ks,
            },
        )

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
        seen_ids = set()

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
                start = int(fields[3]) - 1
                end = int(fields[4])
                strand = fields[6]

                attrs = {}
                for attr in fields[8].split(";"):
                    if "=" in attr:
                        key, value = attr.split("=", 1)
                        attrs[key] = value

                gene_id = attrs.get("ID", attrs.get("Name", ""))
                if not gene_id or gene_id in seen_ids:
                    continue

                seen_ids.add(gene_id)
                genes.append(GeneInfo(
                    gene_id=gene_id,
                    chrom=chrom,
                    start=start,
                    end=end,
                    strand=strand,
                ))

        return genes

    def _load_assignments(
        self,
        path: Path | str,
    ) -> list[SubgenomeAssignment]:
        """Load subgenome assignments from BED."""
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
                subgenome = fields[3].split("|")[0]

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
        """Assign each gene to a subgenome."""
        by_chrom: dict[str, list[SubgenomeAssignment]] = defaultdict(list)
        for a in assignments:
            by_chrom[a.chrom].append(a)

        for chrom in by_chrom:
            by_chrom[chrom].sort(key=lambda x: x.start)

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

    def _find_by_synteny(
        self,
        genes: list[GeneInfo],
        blocks: list[SyntenyBlock],
    ) -> list[HomeologPair]:
        """Find homeologs based on synteny.

        Genes from different subgenomes that are in syntenic positions
        are likely homeologs.

        Parameters
        ----------
        genes : list[GeneInfo]
            Genes with subgenome assignments.
        blocks : list[SyntenyBlock]
            Synteny blocks.

        Returns
        -------
        list[HomeologPair]
            Homeolog pairs.
        """
        if not blocks:
            logger.warning("No synteny blocks provided for synteny-based detection")
            return []

        pairs = []

        # Index genes by position
        genes_by_chrom: dict[str, list[GeneInfo]] = defaultdict(list)
        for gene in genes:
            if gene.subgenome:
                genes_by_chrom[gene.chrom].append(gene)

        for chrom in genes_by_chrom:
            genes_by_chrom[chrom].sort(key=lambda x: x.start)

        # For each synteny block, find gene pairs
        for block in blocks:
            query_genes = genes_by_chrom.get(block.query_chrom, [])
            ref_genes = genes_by_chrom.get(block.ref_chrom, [])

            # Find genes in each region
            query_region_genes = [
                g for g in query_genes
                if block.query_start <= g.start < block.query_end
            ]
            ref_region_genes = [
                g for g in ref_genes
                if block.ref_start <= g.start < block.ref_end
            ]

            # Match genes by relative position
            if query_region_genes and ref_region_genes:
                matched = self._match_genes_in_block(
                    query_region_genes, ref_region_genes, block
                )
                for g1, g2 in matched:
                    # Only pair genes from different subgenomes
                    if g1.subgenome != g2.subgenome:
                        pairs.append(HomeologPair(
                            gene1_id=g1.gene_id,
                            gene1_chrom=g1.chrom,
                            gene1_subgenome=g1.subgenome or "",
                            gene2_id=g2.gene_id,
                            gene2_chrom=g2.chrom,
                            gene2_subgenome=g2.subgenome or "",
                            synteny_support=True,
                            confidence=0.8,
                        ))

        # Remove duplicate pairs
        seen = set()
        unique_pairs = []
        for p in pairs:
            key = tuple(sorted([p.gene1_id, p.gene2_id]))
            if key not in seen:
                seen.add(key)
                unique_pairs.append(p)

        return unique_pairs

    def _match_genes_in_block(
        self,
        query_genes: list[GeneInfo],
        ref_genes: list[GeneInfo],
        block: SyntenyBlock,
    ) -> list[tuple[GeneInfo, GeneInfo]]:
        """Match genes within a synteny block by position.

        Parameters
        ----------
        query_genes : list[GeneInfo]
            Genes in query region.
        ref_genes : list[GeneInfo]
            Genes in reference region.
        block : SyntenyBlock
            Synteny block.

        Returns
        -------
        list[tuple[GeneInfo, GeneInfo]]
            Matched gene pairs.
        """
        matches = []

        # Simple position-based matching
        # Normalize positions to 0-1 within block
        def normalize_query(g: GeneInfo) -> float:
            if block.query_end == block.query_start:
                return 0.5
            return (g.start - block.query_start) / (block.query_end - block.query_start)

        def normalize_ref(g: GeneInfo) -> float:
            if block.ref_end == block.ref_start:
                return 0.5
            pos = (g.start - block.ref_start) / (block.ref_end - block.ref_start)
            # Flip if inverted
            return 1 - pos if block.is_inverted else pos

        # Match each query gene to closest ref gene
        used_ref = set()
        for qg in query_genes:
            q_pos = normalize_query(qg)
            best_match = None
            best_dist = float('inf')

            for rg in ref_genes:
                if rg.gene_id in used_ref:
                    continue
                r_pos = normalize_ref(rg)
                dist = abs(q_pos - r_pos)

                if dist < best_dist and dist < 0.1:  # Within 10% of block
                    best_dist = dist
                    best_match = rg

            if best_match:
                matches.append((qg, best_match))
                used_ref.add(best_match.gene_id)

        return matches

    def _find_by_sequence(
        self,
        genes: list[GeneInfo],
        blast_results: Path | str | None,
        orthogroups: Path | str | None,
    ) -> list[HomeologPair]:
        """Find homeologs based on sequence similarity.

        Parameters
        ----------
        genes : list[GeneInfo]
            Genes with subgenome assignments.
        blast_results : Path or str, optional
            Pre-computed BLAST results.
        orthogroups : Path or str, optional
            OrthoFinder orthogroups.

        Returns
        -------
        list[HomeologPair]
            Homeolog pairs.
        """
        pairs = []

        # Index genes
        gene_dict = {g.gene_id: g for g in genes if g.subgenome}

        if orthogroups:
            # Use orthogroups to find pairs
            og_members = self._parse_orthogroups(orthogroups)

            for _og_id, members in og_members.items():
                # Find genes from this genome in the orthogroup
                our_genes = [gene_dict[m] for m in members if m in gene_dict]

                # Group by subgenome
                by_sg: dict[str, list[GeneInfo]] = defaultdict(list)
                for g in our_genes:
                    if g.subgenome:
                        by_sg[g.subgenome].append(g)

                # Pair genes from different subgenomes
                sg_list = list(by_sg.keys())
                for i, sg1 in enumerate(sg_list):
                    for sg2 in sg_list[i + 1:]:
                        for g1 in by_sg[sg1]:
                            for g2 in by_sg[sg2]:
                                pairs.append(HomeologPair(
                                    gene1_id=g1.gene_id,
                                    gene1_chrom=g1.chrom,
                                    gene1_subgenome=g1.subgenome,
                                    gene2_id=g2.gene_id,
                                    gene2_chrom=g2.chrom,
                                    gene2_subgenome=g2.subgenome,
                                    synteny_support=False,
                                    confidence=0.6,
                                ))

        elif blast_results:
            pairs = self._parse_blast_pairs(blast_results, gene_dict)

        return pairs

    def _parse_orthogroups(
        self,
        path: Path | str,
    ) -> dict[str, list[str]]:
        """Parse OrthoFinder orthogroups file.

        Parameters
        ----------
        path : Path or str
            Path to Orthogroups.tsv.

        Returns
        -------
        dict[str, list[str]]
            Orthogroup ID to gene list mapping.
        """
        path = Path(path)
        orthogroups: dict[str, list[str]] = {}

        with open(path) as f:
            header = None
            for line in f:
                fields = line.strip().split("\t")
                if header is None:
                    header = fields
                    continue

                og_id = fields[0]
                genes = []
                for species_genes in fields[1:]:
                    if species_genes:
                        genes.extend([g.strip() for g in species_genes.split(", ")])

                orthogroups[og_id] = genes

        return orthogroups

    def _parse_blast_pairs(
        self,
        path: Path | str,
        gene_dict: dict[str, GeneInfo],
    ) -> list[HomeologPair]:
        """Parse BLAST results for homeolog pairs.

        Parameters
        ----------
        path : Path or str
            Path to BLAST tabular output.
        gene_dict : dict
            Gene ID to GeneInfo mapping.

        Returns
        -------
        list[HomeologPair]
            Pairs from BLAST hits.
        """
        path = Path(path)
        pairs = []
        seen = set()

        with open(path) as f:
            for line in f:
                fields = line.strip().split("\t")
                if len(fields) < 12:
                    continue

                gene1 = fields[0]
                gene2 = fields[1]
                identity = float(fields[2])

                if gene1 == gene2:
                    continue

                if identity < self.params.min_identity * 100:
                    continue

                key = tuple(sorted([gene1, gene2]))
                if key in seen:
                    continue
                seen.add(key)

                g1 = gene_dict.get(gene1)
                g2 = gene_dict.get(gene2)

                if not g1 or not g2:
                    continue

                if g1.subgenome == g2.subgenome:
                    continue

                pairs.append(HomeologPair(
                    gene1_id=g1.gene_id,
                    gene1_chrom=g1.chrom,
                    gene1_subgenome=g1.subgenome or "",
                    gene2_id=g2.gene_id,
                    gene2_chrom=g2.chrom,
                    gene2_subgenome=g2.subgenome or "",
                    sequence_identity=identity / 100,
                    synteny_support=False,
                    confidence=0.7,
                ))

        return pairs

    def _combine_pairs(
        self,
        synteny_pairs: list[HomeologPair],
        sequence_pairs: list[HomeologPair],
    ) -> list[HomeologPair]:
        """Combine pairs from synteny and sequence evidence.

        Parameters
        ----------
        synteny_pairs : list[HomeologPair]
            Pairs from synteny.
        sequence_pairs : list[HomeologPair]
            Pairs from sequence.

        Returns
        -------
        list[HomeologPair]
            Combined pairs with merged evidence.
        """
        # Index synteny pairs
        synteny_dict: dict[tuple, HomeologPair] = {}
        for p in synteny_pairs:
            key = tuple(sorted([p.gene1_id, p.gene2_id]))
            synteny_dict[key] = p

        combined = list(synteny_pairs)

        # Add sequence pairs, merging if overlap
        for p in sequence_pairs:
            key = tuple(sorted([p.gene1_id, p.gene2_id]))
            if key in synteny_dict:
                # Merge evidence
                sp = synteny_dict[key]
                merged = HomeologPair(
                    gene1_id=sp.gene1_id,
                    gene1_chrom=sp.gene1_chrom,
                    gene1_subgenome=sp.gene1_subgenome,
                    gene2_id=sp.gene2_id,
                    gene2_chrom=sp.gene2_chrom,
                    gene2_subgenome=sp.gene2_subgenome,
                    synteny_support=True,
                    sequence_identity=p.sequence_identity,
                    confidence=min(0.95, sp.confidence + 0.15),
                )
                # Replace in combined list
                for i, cp in enumerate(combined):
                    if (cp.gene1_id, cp.gene2_id) == (merged.gene1_id, merged.gene2_id):
                        combined[i] = merged
                        break
            else:
                combined.append(p)

        return combined

    def _calculate_ks(
        self,
        pairs: list[HomeologPair],
        proteins: Path | str,
    ) -> list[HomeologPair]:
        """Calculate Ks values for homeolog pairs.

        Parameters
        ----------
        pairs : list[HomeologPair]
            Homeolog pairs.
        proteins : Path or str
            Protein FASTA file.

        Returns
        -------
        list[HomeologPair]
            Pairs with Ks values.
        """
        # Load protein sequences
        protein_seqs = self._load_proteins(proteins)

        # For each pair, calculate Ks
        # This is a simplified implementation - real Ks calculation would
        # use tools like yn00 from PAML or KaKs_Calculator
        updated_pairs = []

        for pair in pairs:
            seq1 = protein_seqs.get(pair.gene1_id)
            seq2 = protein_seqs.get(pair.gene2_id)

            ks = None
            ka = None
            identity = pair.sequence_identity

            if seq1 and seq2:
                # Simplified: estimate Ks from sequence divergence
                # Real implementation would align CDSs and calculate properly
                if identity > 0:
                    # Very rough approximation
                    divergence = 1 - identity
                    ks = divergence * 3  # Rough scaling
                    ka = divergence * 0.5

            updated_pairs.append(HomeologPair(
                gene1_id=pair.gene1_id,
                gene1_chrom=pair.gene1_chrom,
                gene1_subgenome=pair.gene1_subgenome,
                gene2_id=pair.gene2_id,
                gene2_chrom=pair.gene2_chrom,
                gene2_subgenome=pair.gene2_subgenome,
                ks=ks,
                ka=ka,
                synteny_support=pair.synteny_support,
                sequence_identity=identity,
                confidence=pair.confidence,
            ))

        return updated_pairs

    def _load_proteins(self, path: Path | str) -> dict[str, str]:
        """Load protein sequences from FASTA.

        Parameters
        ----------
        path : Path or str
            Path to FASTA file.

        Returns
        -------
        dict[str, str]
            Gene ID to sequence mapping.
        """
        path = Path(path)
        proteins: dict[str, str] = {}
        current_id = ""
        current_seq: list[str] = []

        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    if current_id:
                        proteins[current_id] = "".join(current_seq)
                    current_id = line[1:].split()[0]
                    current_seq = []
                else:
                    current_seq.append(line)

            if current_id:
                proteins[current_id] = "".join(current_seq)

        return proteins


def find_homeologs(
    genes: Path | str,
    subgenome_assignments: Path | str,
    synteny_blocks: Path | str | None = None,
    proteins: Path | str | None = None,
    config: SubgenomeConfig | None = None,
    method: str = "synteny",
) -> HomeologResult:
    """Convenience function to find homeolog pairs.

    Parameters
    ----------
    genes : Path or str
        GFF3 file with gene annotations.
    subgenome_assignments : Path or str
        Subgenome assignments BED file.
    synteny_blocks : Path or str, optional
        Synteny blocks file.
    proteins : Path or str, optional
        Protein FASTA for Ks calculation.
    config : SubgenomeConfig, optional
        Subgenome configuration.
    method : str
        Detection method.

    Returns
    -------
    HomeologResult
        Detected homeolog pairs.
    """
    if config is None:
        config = SubgenomeConfig.maize_default()

    finder = HomeologFinder(config, method=method)

    return finder.find(
        genes=genes,
        subgenome_assignments=subgenome_assignments,
        synteny_blocks=synteny_blocks,
        proteins=proteins,
    )


def write_homeolog_pairs(
    result: HomeologResult,
    output: Path | str,
) -> None:
    """Write homeolog pairs to file.

    Parameters
    ----------
    result : HomeologResult
        Homeolog detection results.
    output : Path or str
        Output file path.
    """
    output = Path(output)

    with open(output, "w") as f:
        header = [
            "gene1_id", "gene1_chrom", "gene1_subgenome",
            "gene2_id", "gene2_chrom", "gene2_subgenome",
            "ks", "ka", "synteny_support", "sequence_identity", "confidence",
        ]
        f.write("\t".join(header) + "\n")

        for pair in result.pairs:
            row = [
                pair.gene1_id,
                pair.gene1_chrom,
                pair.gene1_subgenome,
                pair.gene2_id,
                pair.gene2_chrom,
                pair.gene2_subgenome,
                f"{pair.ks:.4f}" if pair.ks is not None else ".",
                f"{pair.ka:.4f}" if pair.ka is not None else ".",
                str(pair.synteny_support).lower(),
                f"{pair.sequence_identity:.4f}",
                f"{pair.confidence:.3f}",
            ]
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote {len(result.pairs)} homeolog pairs to {output}")
