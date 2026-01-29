"""Multi-sample comparison for haplotype proportions.

This module provides tools for comparing haplotype patterns
across multiple samples, including similarity measures,
clustering, and shared block identification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from haplophaser.proportion.blocks import BlockResults
    from haplophaser.proportion.results import ProportionResults

logger = logging.getLogger(__name__)


class SimilarityMethod(Enum):
    """Method for computing sample similarity."""

    CORRELATION = "correlation"
    IBS = "ibs"  # Identity by state
    JACCARD = "jaccard"  # On blocks
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"


@dataclass
class SharedBlock:
    """A haplotype block shared between multiple samples.

    Attributes:
        chrom: Chromosome name
        start: Block start position
        end: Block end position
        founder: Dominant founder
        samples: List of samples sharing this block
        mean_proportion: Mean founder proportion across samples
        overlap_fraction: Minimum pairwise overlap fraction
    """

    chrom: str
    start: int
    end: int
    founder: str
    samples: list[str]
    mean_proportion: float = 0.0
    overlap_fraction: float = 0.0

    @property
    def length(self) -> int:
        """Get block length."""
        return self.end - self.start

    @property
    def n_samples(self) -> int:
        """Get number of samples sharing this block."""
        return len(self.samples)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "chrom": self.chrom,
            "start": self.start,
            "end": self.end,
            "founder": self.founder,
            "samples": self.samples.copy(),
            "mean_proportion": self.mean_proportion,
            "overlap_fraction": self.overlap_fraction,
            "length": self.length,
            "n_samples": self.n_samples,
        }


@dataclass
class ClusterResult:
    """Result of clustering samples.

    Attributes:
        n_clusters: Number of clusters
        labels: Cluster label for each sample
        sample_names: List of sample names
        centroids: Cluster centroids (if applicable)
        method: Clustering method used
    """

    n_clusters: int
    labels: list[int]
    sample_names: list[str]
    centroids: np.ndarray | None = None
    method: str = "hierarchical"

    def get_cluster_samples(self, cluster_id: int) -> list[str]:
        """Get samples in a specific cluster."""
        return [s for s, l in zip(self.sample_names, self.labels, strict=False) if l == cluster_id]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "n_clusters": self.n_clusters,
            "labels": self.labels,
            "sample_names": self.sample_names,
            "method": self.method,
            "clusters": {
                i: self.get_cluster_samples(i) for i in range(self.n_clusters)
            },
        }


class SampleComparison:
    """Compare haplotype patterns across multiple samples.

    Provides methods for computing pairwise similarity,
    clustering samples, and finding shared haplotype blocks.
    """

    def __init__(
        self,
        proportions: ProportionResults,
        blocks: BlockResults | None = None,
    ) -> None:
        """Initialize the comparison tool.

        Args:
            proportions: Proportion estimation results
            blocks: Optional haplotype block results
        """
        self.proportions = proportions
        self.blocks = blocks
        self.founders = proportions.founders
        self.sample_names = proportions.sample_names

        self._similarity_cache: dict[str, np.ndarray] = {}

    def pairwise_similarity(
        self,
        method: str | SimilarityMethod = "correlation",
        use_windows: bool = True,
    ) -> np.ndarray:
        """Compute pairwise similarity matrix between samples.

        Args:
            method: Similarity method
            use_windows: If True, use window-level data; else genome-wide

        Returns:
            Square similarity matrix (n_samples x n_samples)
        """
        if isinstance(method, str):
            method = SimilarityMethod(method)

        cache_key = f"{method.value}_{use_windows}"
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        n_samples = len(self.sample_names)
        similarity = np.zeros((n_samples, n_samples))

        if use_windows:
            # Build proportion vectors per sample
            vectors = self._build_proportion_vectors()
        else:
            # Use genome-wide proportions
            vectors = {}
            for sample in self.proportions:
                vectors[sample.sample_name] = np.array(
                    [sample.genome_wide.get(f, 0.0) for f in self.founders]
                )

        for i, s1 in enumerate(self.sample_names):
            for j, s2 in enumerate(self.sample_names):
                if i == j:
                    similarity[i, j] = 1.0
                elif j < i:
                    similarity[i, j] = similarity[j, i]
                else:
                    v1 = vectors.get(s1)
                    v2 = vectors.get(s2)

                    if v1 is None or v2 is None:
                        similarity[i, j] = 0.0
                    else:
                        similarity[i, j] = self._compute_similarity(v1, v2, method)

        self._similarity_cache[cache_key] = similarity
        return similarity

    def _build_proportion_vectors(self) -> dict[str, np.ndarray]:
        """Build proportion vectors for window-level comparison.

        Returns:
            Dict mapping sample names to proportion vectors
        """
        vectors = {}

        # Get all unique window positions
        all_windows = set()
        for sample in self.proportions:
            for window in sample.windows:
                all_windows.add((window.chrom, window.start, window.end))

        # Sort windows
        sorted_windows = sorted(all_windows)
        n_windows = len(sorted_windows)
        n_founders = len(self.founders)

        for sample in self.proportions:
            # Build lookup for this sample's windows
            window_lookup = {}
            for window in sample.windows:
                key = (window.chrom, window.start, window.end)
                window_lookup[key] = window

            # Build vector
            vector = np.zeros(n_windows * n_founders)
            for i, window_key in enumerate(sorted_windows):
                window = window_lookup.get(window_key)
                for j, founder in enumerate(self.founders):
                    if window:
                        vector[i * n_founders + j] = window.proportions.get(founder, 0.0)
                    else:
                        vector[i * n_founders + j] = 0.0

            vectors[sample.sample_name] = vector

        return vectors

    def _compute_similarity(
        self,
        v1: np.ndarray,
        v2: np.ndarray,
        method: SimilarityMethod,
    ) -> float:
        """Compute similarity between two vectors.

        Args:
            v1: First vector
            v2: Second vector
            method: Similarity method

        Returns:
            Similarity score (higher = more similar)
        """
        if len(v1) != len(v2):
            # Pad shorter vector
            max_len = max(len(v1), len(v2))
            v1 = np.pad(v1, (0, max_len - len(v1)))
            v2 = np.pad(v2, (0, max_len - len(v2)))

        if method == SimilarityMethod.CORRELATION:
            if np.std(v1) == 0 or np.std(v2) == 0:
                return 0.0
            return float(np.corrcoef(v1, v2)[0, 1])

        elif method == SimilarityMethod.IBS:
            # Identity by state: proportion of matching alleles
            # Treat as discrete states based on max proportion
            s1 = np.argmax(v1.reshape(-1, len(self.founders)), axis=1)
            s2 = np.argmax(v2.reshape(-1, len(self.founders)), axis=1)
            return float(np.mean(s1 == s2))

        elif method == SimilarityMethod.COSINE:
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(v1, v2) / (norm1 * norm2))

        elif method == SimilarityMethod.EUCLIDEAN:
            # Convert distance to similarity
            dist = np.linalg.norm(v1 - v2)
            max_dist = np.sqrt(len(v1))  # Maximum possible distance
            return 1.0 - dist / max_dist if max_dist > 0 else 1.0

        elif method == SimilarityMethod.JACCARD:
            # Jaccard on blocks (requires block data)
            # Fall back to threshold-based Jaccard on proportions
            threshold = 0.5
            s1 = v1 > threshold
            s2 = v2 > threshold
            intersection = np.sum(s1 & s2)
            union = np.sum(s1 | s2)
            return intersection / union if union > 0 else 0.0

        return 0.0

    def cluster(
        self,
        n_clusters: int = 3,
        method: str = "hierarchical",
        similarity_method: str = "correlation",
    ) -> ClusterResult:
        """Cluster samples based on haplotype similarity.

        Args:
            n_clusters: Number of clusters
            method: Clustering method ('hierarchical', 'kmeans')
            similarity_method: Method for computing similarity

        Returns:
            ClusterResult with cluster assignments
        """
        from scipy.cluster.hierarchy import fcluster, linkage

        similarity = self.pairwise_similarity(similarity_method)

        # Convert similarity to distance
        distance = 1 - similarity
        np.fill_diagonal(distance, 0)

        if method == "hierarchical":
            # Condensed distance matrix for hierarchical clustering
            n = len(self.sample_names)
            condensed = []
            for i in range(n):
                for j in range(i + 1, n):
                    condensed.append(distance[i, j])

            if len(condensed) > 0:
                Z = linkage(condensed, method="ward")
                labels = fcluster(Z, n_clusters, criterion="maxclust")
                labels = [int(l) - 1 for l in labels]  # 0-indexed
            else:
                labels = [0] * n

        elif method == "kmeans":
            from scipy.cluster.vq import kmeans2

            # Build feature matrix from genome-wide proportions
            features = []
            for sample in self.proportions:
                features.append([sample.genome_wide.get(f, 0.0) for f in self.founders])

            features = np.array(features)
            if len(features) >= n_clusters:
                _, labels = kmeans2(features, n_clusters, minit="++")
                labels = [int(l) for l in labels]
            else:
                labels = list(range(len(features)))

        else:
            labels = [0] * len(self.sample_names)

        return ClusterResult(
            n_clusters=n_clusters,
            labels=labels,
            sample_names=self.sample_names,
            method=method,
        )

    def find_shared_blocks(
        self,
        min_samples: int = 2,
        min_overlap: float = 0.5,
        min_length: int = 10000,
    ) -> list[SharedBlock]:
        """Find haplotype blocks shared between multiple samples.

        Args:
            min_samples: Minimum number of samples sharing a block
            min_overlap: Minimum reciprocal overlap fraction
            min_length: Minimum block length in bp

        Returns:
            List of SharedBlock objects
        """
        if self.blocks is None:
            logger.warning("No block data available for finding shared blocks")
            return []

        shared_blocks = []

        # Group blocks by chromosome and founder
        blocks_by_chrom_founder: dict[tuple[str, str], list[tuple[str, tuple]]] = {}

        for sample_name in self.sample_names:
            sample_blocks = self.blocks.get_sample(sample_name)
            if sample_blocks is None:
                continue

            for block in sample_blocks.blocks:
                key = (block.chrom, block.dominant_founder)
                if key not in blocks_by_chrom_founder:
                    blocks_by_chrom_founder[key] = []
                blocks_by_chrom_founder[key].append(
                    (sample_name, (block.start, block.end, block.mean_proportion))
                )

        # Find overlapping blocks
        for (chrom, founder), block_list in blocks_by_chrom_founder.items():
            if len(block_list) < min_samples:
                continue

            # Sort by start position
            block_list = sorted(block_list, key=lambda x: x[1][0])

            # Greedy clustering of overlapping blocks
            clusters = []
            for sample, (start, end, prop) in block_list:
                placed = False
                for cluster in clusters:
                    # Check overlap with cluster representative
                    rep_start, rep_end = cluster["range"]

                    overlap_start = max(start, rep_start)
                    overlap_end = min(end, rep_end)
                    overlap = max(0, overlap_end - overlap_start)

                    len1 = end - start
                    len2 = rep_end - rep_start

                    if len1 > 0 and len2 > 0:
                        overlap_frac = min(overlap / len1, overlap / len2)

                        if overlap_frac >= min_overlap:
                            cluster["samples"].append(sample)
                            cluster["proportions"].append(prop)
                            cluster["range"] = (
                                min(rep_start, start),
                                max(rep_end, end),
                            )
                            placed = True
                            break

                if not placed:
                    clusters.append({
                        "range": (start, end),
                        "samples": [sample],
                        "proportions": [prop],
                    })

            # Convert clusters to SharedBlock
            for cluster in clusters:
                if len(cluster["samples"]) >= min_samples:
                    start, end = cluster["range"]
                    if end - start >= min_length:
                        shared_blocks.append(SharedBlock(
                            chrom=chrom,
                            start=start,
                            end=end,
                            founder=founder,
                            samples=cluster["samples"],
                            mean_proportion=float(np.mean(cluster["proportions"])),
                            overlap_fraction=min_overlap,
                        ))

        return shared_blocks

    def find_private_blocks(
        self,
        sample: str,
        min_length: int = 10000,
    ) -> list[dict]:
        """Find haplotype blocks unique to a specific sample.

        Args:
            sample: Sample name
            min_length: Minimum block length

        Returns:
            List of private block descriptions
        """
        if self.blocks is None:
            return []

        sample_blocks = self.blocks.get_sample(sample)
        if sample_blocks is None:
            return []

        private_blocks = []

        for block in sample_blocks.blocks:
            if block.length < min_length:
                continue

            # Check if any other sample has overlapping block with same founder
            is_private = True

            for other_name in self.sample_names:
                if other_name == sample:
                    continue

                other_blocks = self.blocks.get_sample(other_name)
                if other_blocks is None:
                    continue

                for other_block in other_blocks.blocks:
                    if (
                        other_block.chrom == block.chrom
                        and other_block.dominant_founder == block.dominant_founder
                    ):
                        # Check overlap
                        overlap_start = max(block.start, other_block.start)
                        overlap_end = min(block.end, other_block.end)
                        overlap = max(0, overlap_end - overlap_start)

                        if overlap > 0.5 * min(block.length, other_block.length):
                            is_private = False
                            break

                if not is_private:
                    break

            if is_private:
                private_blocks.append({
                    "chrom": block.chrom,
                    "start": block.start,
                    "end": block.end,
                    "length": block.length,
                    "founder": block.dominant_founder,
                    "proportion": block.mean_proportion,
                })

        return private_blocks

    def most_similar_samples(
        self,
        sample: str,
        n: int = 5,
        method: str = "correlation",
    ) -> list[tuple[str, float]]:
        """Find samples most similar to a given sample.

        Args:
            sample: Query sample name
            n: Number of similar samples to return
            method: Similarity method

        Returns:
            List of (sample_name, similarity_score) tuples
        """
        similarity = self.pairwise_similarity(method)

        if sample not in self.sample_names:
            return []

        idx = self.sample_names.index(sample)
        scores = []

        for i, other in enumerate(self.sample_names):
            if i != idx:
                scores.append((other, float(similarity[idx, i])))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:n]

    def distance_matrix(
        self,
        method: str = "correlation",
    ) -> tuple[list[str], np.ndarray]:
        """Get distance matrix for samples.

        Args:
            method: Similarity method (converted to distance)

        Returns:
            Tuple of (sample_names, distance_matrix)
        """
        similarity = self.pairwise_similarity(method)
        distance = 1 - similarity
        np.fill_diagonal(distance, 0)
        return self.sample_names.copy(), distance

    def to_dict(self) -> dict:
        """Export comparison results to dictionary."""
        return {
            "n_samples": len(self.sample_names),
            "founders": self.founders,
            "sample_names": self.sample_names,
            "similarity_correlation": self.pairwise_similarity("correlation").tolist(),
        }
