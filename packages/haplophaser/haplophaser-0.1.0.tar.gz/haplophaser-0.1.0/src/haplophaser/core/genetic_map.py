"""Genetic map support for recombination modeling.

This module provides classes for loading and using genetic maps
to model recombination probabilities between genomic positions.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MapPosition:
    """A single position in a genetic map.

    Attributes:
        chrom: Chromosome name
        physical_pos: Physical position (bp)
        genetic_pos: Genetic position (cM)
        rate: Local recombination rate (cM/Mb)
        marker_id: Optional marker identifier
    """

    chrom: str
    physical_pos: int
    genetic_pos: float
    rate: float = 1.0
    marker_id: str | None = None


@dataclass
class ChromosomeMap:
    """Genetic map for a single chromosome.

    Attributes:
        chrom: Chromosome name
        positions: List of map positions sorted by physical position
    """

    chrom: str
    positions: list[MapPosition] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Sort positions by physical position."""
        if self.positions:
            self.positions = sorted(self.positions, key=lambda p: p.physical_pos)

    @property
    def n_positions(self) -> int:
        """Get number of map positions."""
        return len(self.positions)

    @property
    def physical_start(self) -> int:
        """Get first physical position."""
        return self.positions[0].physical_pos if self.positions else 0

    @property
    def physical_end(self) -> int:
        """Get last physical position."""
        return self.positions[-1].physical_pos if self.positions else 0

    @property
    def genetic_length(self) -> float:
        """Get total genetic length in cM."""
        if not self.positions:
            return 0.0
        return self.positions[-1].genetic_pos - self.positions[0].genetic_pos

    @property
    def physical_length(self) -> int:
        """Get physical length (span) in bp."""
        if not self.positions:
            return 0
        return self.positions[-1].physical_pos - self.positions[0].physical_pos

    def recombination_rate(self, pos1: int, pos2: int) -> float:
        """Get average recombination rate between two positions.

        Args:
            pos1: First physical position
            pos2: Second physical position

        Returns:
            Average recombination rate in cM/Mb
        """
        cm1 = self.physical_to_genetic(pos1)
        cm2 = self.physical_to_genetic(pos2)
        delta_mb = abs(pos2 - pos1) / 1_000_000
        if delta_mb == 0:
            return self.get_rate_at((pos1 + pos2) // 2)
        return abs(cm2 - cm1) / delta_mb

    def physical_to_genetic(self, pos: int) -> float:
        """Convert physical position to genetic position.

        Uses linear interpolation between map positions.

        Args:
            pos: Physical position in bp

        Returns:
            Genetic position in cM
        """
        if not self.positions:
            # No map data, assume 1 cM/Mb
            return pos / 1_000_000

        # Handle positions outside map range
        if pos <= self.positions[0].physical_pos:
            # Extrapolate using first rate
            rate = self.positions[0].rate if self.positions[0].rate > 0 else 1.0
            delta_bp = self.positions[0].physical_pos - pos
            return self.positions[0].genetic_pos - (delta_bp / 1_000_000) * rate

        if pos >= self.positions[-1].physical_pos:
            # Extrapolate using last rate
            rate = self.positions[-1].rate if self.positions[-1].rate > 0 else 1.0
            delta_bp = pos - self.positions[-1].physical_pos
            return self.positions[-1].genetic_pos + (delta_bp / 1_000_000) * rate

        # Binary search for bracketing positions
        left_idx = 0
        right_idx = len(self.positions) - 1

        while right_idx - left_idx > 1:
            mid = (left_idx + right_idx) // 2
            if self.positions[mid].physical_pos <= pos:
                left_idx = mid
            else:
                right_idx = mid

        # Linear interpolation
        left = self.positions[left_idx]
        right = self.positions[right_idx]

        if right.physical_pos == left.physical_pos:
            return left.genetic_pos

        fraction = (pos - left.physical_pos) / (right.physical_pos - left.physical_pos)
        return left.genetic_pos + fraction * (right.genetic_pos - left.genetic_pos)

    def genetic_to_physical(self, cm: float) -> int:
        """Convert genetic position to physical position.

        Uses linear interpolation between map positions.

        Args:
            cm: Genetic position in cM

        Returns:
            Physical position in bp
        """
        if not self.positions:
            # No map data, assume 1 cM/Mb
            return int(cm * 1_000_000)

        # Handle positions outside map range
        if cm <= self.positions[0].genetic_pos:
            rate = self.positions[0].rate if self.positions[0].rate > 0 else 1.0
            delta_cm = self.positions[0].genetic_pos - cm
            return int(self.positions[0].physical_pos - (delta_cm / rate) * 1_000_000)

        if cm >= self.positions[-1].genetic_pos:
            rate = self.positions[-1].rate if self.positions[-1].rate > 0 else 1.0
            delta_cm = cm - self.positions[-1].genetic_pos
            return int(self.positions[-1].physical_pos + (delta_cm / rate) * 1_000_000)

        # Binary search for bracketing positions
        left_idx = 0
        right_idx = len(self.positions) - 1

        while right_idx - left_idx > 1:
            mid = (left_idx + right_idx) // 2
            if self.positions[mid].genetic_pos <= cm:
                left_idx = mid
            else:
                right_idx = mid

        # Linear interpolation
        left = self.positions[left_idx]
        right = self.positions[right_idx]

        if right.genetic_pos == left.genetic_pos:
            return left.physical_pos

        fraction = (cm - left.genetic_pos) / (right.genetic_pos - left.genetic_pos)
        return int(left.physical_pos + fraction * (right.physical_pos - left.physical_pos))

    def get_rate_at(self, pos: int) -> float:
        """Get local recombination rate at a position.

        Args:
            pos: Physical position in bp

        Returns:
            Recombination rate in cM/Mb
        """
        if not self.positions:
            return 1.0  # Default rate

        # Find nearest positions
        if pos <= self.positions[0].physical_pos:
            return self.positions[0].rate

        if pos >= self.positions[-1].physical_pos:
            return self.positions[-1].rate

        # Binary search
        left_idx = 0
        right_idx = len(self.positions) - 1

        while right_idx - left_idx > 1:
            mid = (left_idx + right_idx) // 2
            if self.positions[mid].physical_pos <= pos:
                left_idx = mid
            else:
                right_idx = mid

        # Use average of bracketing rates
        left = self.positions[left_idx]
        right = self.positions[right_idx]
        return (left.rate + right.rate) / 2


class GeneticMap:
    """Genetic map for multiple chromosomes.

    Supports loading from various file formats and provides
    methods for converting between physical and genetic positions.
    """

    def __init__(
        self,
        chromosome_maps: dict[str, ChromosomeMap] | None = None,
        default_rate: float = 1.0,
    ) -> None:
        """Initialize genetic map.

        Args:
            chromosome_maps: Dict mapping chromosome names to ChromosomeMap objects
            default_rate: Default recombination rate (cM/Mb) for chromosomes without map data
        """
        self.chromosome_maps = chromosome_maps or {}
        self.default_rate = default_rate

    @classmethod
    def from_plink(cls, path: str | Path) -> GeneticMap:
        """Load PLINK-format genetic map.

        Args:
            path: Path to PLINK .map file

        Returns:
            GeneticMap object

        Raises:
            ValueError: If file is empty or contains no valid data
        """
        result = cls._load_plink(Path(path))
        if not result.chromosome_maps:
            raise ValueError(f"No valid map data found in {path}")
        return result

    @classmethod
    def from_mstmap(cls, path: str | Path) -> GeneticMap:
        """Load MSTmap-format genetic map.

        Args:
            path: Path to MSTmap file

        Returns:
            GeneticMap object
        """
        return cls._load_mstmap(Path(path))

    @classmethod
    def from_tsv(cls, path: str | Path) -> GeneticMap:
        """Load custom TSV-format genetic map.

        Args:
            path: Path to TSV file

        Returns:
            GeneticMap object
        """
        return cls._load_custom(Path(path))

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        format: str | None = None,
    ) -> GeneticMap:
        """Load genetic map from file.

        Supports PLINK, MSTmap, and custom formats.

        Args:
            path: Path to genetic map file
            format: File format ('plink', 'mstmap', 'custom', or None for auto-detect)

        Returns:
            GeneticMap object
        """
        path = Path(path)

        if format is None:
            # Auto-detect format from extension/content
            format = cls._detect_format(path)

        logger.info(f"Loading genetic map from {path} (format: {format})")

        if format == "plink":
            return cls._load_plink(path)
        elif format == "mstmap":
            return cls._load_mstmap(path)
        else:
            return cls._load_custom(path)

    @staticmethod
    def _detect_format(path: Path) -> str:
        """Detect genetic map file format.

        Args:
            path: Path to file

        Returns:
            Format string
        """
        suffix = path.suffix.lower()
        if suffix in (".map", ".plink"):
            return "plink"

        # Check first lines
        with open(path) as f:
            first_line = f.readline().strip()

        # MSTmap format starts with group/marker headers
        if first_line.startswith("group"):
            return "mstmap"

        # Default to custom (tab-separated with header)
        return "custom"

    @classmethod
    def _load_plink(cls, path: Path) -> GeneticMap:
        """Load PLINK-format genetic map.

        Format: chr marker_id genetic_pos physical_pos

        Args:
            path: Path to file

        Returns:
            GeneticMap object
        """
        chromosome_maps: dict[str, ChromosomeMap] = {}
        prev_pos: dict[str, MapPosition] = {}

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) < 4:
                    continue

                chrom = parts[0]
                genetic_pos = float(parts[2])
                physical_pos = int(parts[3])

                # Calculate rate from previous position
                rate = 1.0
                if chrom in prev_pos:
                    prev = prev_pos[chrom]
                    delta_cm = genetic_pos - prev.genetic_pos
                    delta_mb = (physical_pos - prev.physical_pos) / 1_000_000
                    if delta_mb > 0:
                        rate = delta_cm / delta_mb

                pos = MapPosition(
                    chrom=chrom,
                    physical_pos=physical_pos,
                    genetic_pos=genetic_pos,
                    rate=rate,
                )

                if chrom not in chromosome_maps:
                    chromosome_maps[chrom] = ChromosomeMap(chrom=chrom, positions=[])

                chromosome_maps[chrom].positions.append(pos)
                prev_pos[chrom] = pos

        # Sort positions
        for chrom_map in chromosome_maps.values():
            chrom_map.positions = sorted(chrom_map.positions, key=lambda p: p.physical_pos)

        logger.info(f"Loaded map for {len(chromosome_maps)} chromosomes")
        return cls(chromosome_maps=chromosome_maps)

    @classmethod
    def _load_mstmap(cls, path: Path) -> GeneticMap:
        """Load MSTmap-format genetic map.

        Format varies, typically marker-centric with groups.

        Args:
            path: Path to file

        Returns:
            GeneticMap object
        """
        chromosome_maps: dict[str, ChromosomeMap] = {}
        current_group = None

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";"):
                    continue

                if line.startswith("group"):
                    current_group = line.split()[1] if len(line.split()) > 1 else "unknown"
                    if current_group not in chromosome_maps:
                        chromosome_maps[current_group] = ChromosomeMap(
                            chrom=current_group, positions=[]
                        )
                    continue

                parts = line.split()
                if len(parts) >= 2 and current_group:
                    # Format: marker_name genetic_pos
                    marker = parts[0]
                    genetic_pos = float(parts[1])

                    # Try to parse physical position from marker name
                    # Common format: chr_pos or chr:pos
                    physical_pos = 0
                    for sep in ["_", ":", "-"]:
                        if sep in marker:
                            try:
                                physical_pos = int(marker.split(sep)[-1])
                                break
                            except ValueError:
                                continue

                    pos = MapPosition(
                        chrom=current_group,
                        physical_pos=physical_pos,
                        genetic_pos=genetic_pos,
                        rate=1.0,
                    )
                    chromosome_maps[current_group].positions.append(pos)

        return cls(chromosome_maps=chromosome_maps)

    @classmethod
    def _load_custom(cls, path: Path) -> GeneticMap:
        """Load custom tab-separated genetic map.

        Supports flexible column ordering based on header.
        Expected columns: chrom, physical_pos, genetic_pos
        Optional columns: rate, marker_id

        Args:
            path: Path to file

        Returns:
            GeneticMap object
        """
        chromosome_maps: dict[str, ChromosomeMap] = {}
        header = None
        col_indices: dict[str, int] = {}

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")
                if len(parts) < 3:
                    parts = line.split()

                # Detect header
                if header is None:
                    if any(h in parts[0].lower() for h in ["chr", "chrom", "chromosome"]):
                        header = [p.lower() for p in parts]
                        # Map column names to indices
                        for i, h in enumerate(header):
                            if "chrom" in h or h == "chr":
                                col_indices["chrom"] = i
                            elif "physical" in h or h == "position" or h == "pos":
                                col_indices["physical_pos"] = i
                            elif "genetic" in h or h == "cm":
                                col_indices["genetic_pos"] = i
                            elif "rate" in h:
                                col_indices["rate"] = i
                            elif "marker" in h or h == "id":
                                col_indices["marker_id"] = i
                        continue
                    else:
                        # Default column ordering
                        header = ["chr", "position", "cM"]
                        col_indices = {"chrom": 0, "physical_pos": 1, "genetic_pos": 2}

                # Parse using detected column indices
                chrom = parts[col_indices.get("chrom", 0)]
                physical_pos = int(float(parts[col_indices.get("physical_pos", 1)]))
                genetic_pos = float(parts[col_indices.get("genetic_pos", 2)])
                rate = float(parts[col_indices["rate"]]) if "rate" in col_indices else 1.0
                marker_id = parts[col_indices["marker_id"]] if "marker_id" in col_indices else None

                pos = MapPosition(
                    chrom=chrom,
                    physical_pos=physical_pos,
                    genetic_pos=genetic_pos,
                    rate=rate,
                    marker_id=marker_id,
                )

                if chrom not in chromosome_maps:
                    chromosome_maps[chrom] = ChromosomeMap(chrom=chrom, positions=[])

                chromosome_maps[chrom].positions.append(pos)

        # Sort and calculate rates if not provided
        for chrom, chrom_map in chromosome_maps.items():
            chrom_map.positions = sorted(chrom_map.positions, key=lambda p: p.physical_pos)

            # Calculate rates from positions
            for i in range(1, len(chrom_map.positions)):
                prev = chrom_map.positions[i - 1]
                curr = chrom_map.positions[i]
                delta_cm = curr.genetic_pos - prev.genetic_pos
                delta_mb = (curr.physical_pos - prev.physical_pos) / 1_000_000
                if delta_mb > 0 and curr.rate == 1.0:
                    curr.rate = delta_cm / delta_mb

        return cls(chromosome_maps=chromosome_maps)

    @property
    def chromosomes(self) -> list[str]:
        """Get list of chromosomes with map data."""
        return list(self.chromosome_maps.keys())

    @property
    def chromosome_names(self) -> list[str]:
        """Get list of chromosome names (alias for chromosomes)."""
        return self.chromosomes

    @property
    def n_chromosomes(self) -> int:
        """Get number of chromosomes with map data."""
        return len(self.chromosome_maps)

    @property
    def total_genetic_length(self) -> float:
        """Get total genetic length across all chromosomes in cM."""
        return sum(
            chrom_map.genetic_length for chrom_map in self.chromosome_maps.values()
        )

    def has_chromosome(self, chrom: str) -> bool:
        """Check if map data exists for a chromosome."""
        return chrom in self.chromosome_maps

    def get_chromosome_map(self, chrom: str) -> ChromosomeMap | None:
        """Get map for a specific chromosome."""
        return self.chromosome_maps.get(chrom)

    def physical_to_genetic(self, chrom: str, pos: int) -> float:
        """Convert physical position to genetic position.

        Args:
            chrom: Chromosome name
            pos: Physical position in bp

        Returns:
            Genetic position in cM
        """
        chrom_map = self.chromosome_maps.get(chrom)
        if chrom_map:
            return chrom_map.physical_to_genetic(pos)
        # Fall back to default rate
        return pos / 1_000_000 * self.default_rate

    def genetic_to_physical(self, chrom: str, cm: float) -> int:
        """Convert genetic position to physical position.

        Args:
            chrom: Chromosome name
            cm: Genetic position in cM

        Returns:
            Physical position in bp
        """
        chrom_map = self.chromosome_maps.get(chrom)
        if chrom_map:
            return chrom_map.genetic_to_physical(cm)
        # Fall back to default rate
        return int(cm / self.default_rate * 1_000_000)

    def genetic_distance(self, chrom: str, pos1: int, pos2: int) -> float:
        """Calculate genetic distance between two positions.

        Args:
            chrom: Chromosome name
            pos1: First physical position
            pos2: Second physical position

        Returns:
            Genetic distance in cM
        """
        cm1 = self.physical_to_genetic(chrom, pos1)
        cm2 = self.physical_to_genetic(chrom, pos2)
        return abs(cm2 - cm1)

    def recombination_probability(
        self,
        chrom: str,
        pos1: int,
        pos2: int,
        method: str = "haldane",
    ) -> float:
        """Calculate probability of recombination between two positions.

        Args:
            chrom: Chromosome name
            pos1: First physical position
            pos2: Second physical position
            method: Mapping function ('haldane' or 'kosambi')

        Returns:
            Recombination probability (0-0.5)
        """
        genetic_dist = self.genetic_distance(chrom, pos1, pos2)

        # Convert cM to Morgans
        morgans = genetic_dist / 100.0

        if method == "haldane":
            # Haldane mapping function: r = 0.5 * (1 - e^(-2d))
            return 0.5 * (1 - np.exp(-2 * morgans))
        elif method == "kosambi":
            # Kosambi mapping function: r = 0.5 * tanh(2d)
            return 0.5 * np.tanh(2 * morgans)
        else:
            # Simple approximation for small distances
            return min(0.5, morgans)

    def get_rate_at(self, chrom: str, pos: int) -> float:
        """Get local recombination rate at a position.

        Args:
            chrom: Chromosome name
            pos: Physical position

        Returns:
            Recombination rate in cM/Mb
        """
        chrom_map = self.chromosome_maps.get(chrom)
        if chrom_map:
            return chrom_map.get_rate_at(pos)
        return self.default_rate

    def __iter__(self) -> Iterator[ChromosomeMap]:
        """Iterate over chromosome maps."""
        return iter(self.chromosome_maps.values())

    def __len__(self) -> int:
        """Get number of chromosomes with map data."""
        return len(self.chromosome_maps)

    def summary(self) -> dict:
        """Get summary statistics for the genetic map."""
        total_physical = 0
        total_genetic = 0.0
        n_markers = 0

        for chrom_map in self.chromosome_maps.values():
            if chrom_map.positions:
                total_physical += chrom_map.physical_end - chrom_map.physical_start
                total_genetic += chrom_map.genetic_length
                n_markers += chrom_map.n_positions

        return {
            "n_chromosomes": len(self.chromosome_maps),
            "n_markers": n_markers,
            "total_physical_length_mb": total_physical / 1_000_000,
            "total_genetic_length_cm": total_genetic,
            "average_rate_cM_Mb": total_genetic / (total_physical / 1_000_000) if total_physical > 0 else self.default_rate,
        }


def create_uniform_map(
    chromosome_lengths: dict[str, int],
    rate: float = 1.0,
) -> GeneticMap:
    """Create a uniform-rate genetic map from chromosome lengths.

    Args:
        chromosome_lengths: Dict mapping chromosome names to lengths in bp
        rate: Uniform recombination rate in cM/Mb

    Returns:
        GeneticMap with uniform rate across all chromosomes
    """
    chromosome_maps = {}

    for chrom, length in chromosome_lengths.items():
        # Create positions at start and end
        positions = [
            MapPosition(chrom=chrom, physical_pos=0, genetic_pos=0.0, rate=rate),
            MapPosition(
                chrom=chrom,
                physical_pos=length,
                genetic_pos=length / 1_000_000 * rate,
                rate=rate,
            ),
        ]
        chromosome_maps[chrom] = ChromosomeMap(chrom=chrom, positions=positions)

    return GeneticMap(chromosome_maps=chromosome_maps, default_rate=rate)


def haldane_to_probability(cm_distance: float) -> float:
    """Convert genetic distance to recombination probability using Haldane function.

    The Haldane mapping function assumes no interference between crossovers.
    Formula: r = 0.5 * (1 - e^(-2d)) where d is distance in Morgans.

    Args:
        cm_distance: Genetic distance in centiMorgans

    Returns:
        Recombination probability (0 to 0.5)
    """
    morgans = cm_distance / 100.0
    return 0.5 * (1 - np.exp(-2 * morgans))


def kosambi_to_probability(cm_distance: float) -> float:
    """Convert genetic distance to recombination probability using Kosambi function.

    The Kosambi mapping function accounts for positive interference.
    Formula: r = 0.5 * tanh(2d) where d is distance in Morgans.

    Args:
        cm_distance: Genetic distance in centiMorgans

    Returns:
        Recombination probability (0 to 0.5)
    """
    morgans = cm_distance / 100.0
    return 0.5 * np.tanh(2 * morgans)
