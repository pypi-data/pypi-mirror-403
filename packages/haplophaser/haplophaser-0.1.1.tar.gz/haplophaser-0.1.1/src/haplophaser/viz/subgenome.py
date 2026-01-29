"""Subgenome assignment visualization."""

from __future__ import annotations

from pathlib import Path

import chromoplot as cp

from .utils import get_phaser_theme, load_reference

# Subgenome color palettes
SUBGENOME_COLORS = {
    # Maize
    "maize": {"maize1": "#1b9e77", "maize2": "#d95f02"},
    # Wheat (hexaploid)
    "wheat": {"A": "#e41a1c", "B": "#377eb8", "D": "#4daf4a"},
    # Brassica
    "brassica": {"A": "#984ea3", "C": "#ff7f00"},
    # Generic
    "default": {"SG1": "#1b9e77", "SG2": "#d95f02", "SG3": "#7570b3"},
}


def get_subgenome_colors(
    subgenomes: list[str],
    organism: str = "auto",
) -> dict[str, str]:
    """
    Get colors for subgenome visualization.

    Parameters
    ----------
    subgenomes : list[str]
        Subgenome names
    organism : str
        Organism name for preset colors: 'maize', 'wheat', 'brassica', 'auto'

    Returns
    -------
    dict[str, str]
        Mapping of subgenome names to colors
    """
    if organism == "auto":
        # Try to detect from subgenome names
        sg_lower = [s.lower() for s in subgenomes]
        if any("maize" in s for s in sg_lower) or set(subgenomes) == {"1", "2"}:
            organism = "maize"
        elif set(subgenomes) <= {"A", "B", "D"}:
            organism = "wheat"
        elif set(subgenomes) <= {"A", "C"}:
            organism = "brassica"
        else:
            organism = "default"

    palette = SUBGENOME_COLORS.get(organism, SUBGENOME_COLORS["default"])

    # Build color map
    colors = {}
    default_colors = cp.get_palette("subgenome", n=len(subgenomes))

    for i, sg in enumerate(subgenomes):
        if sg in palette:
            colors[sg] = palette[sg]
        else:
            colors[sg] = default_colors[i % len(default_colors)]

    return colors


class SubgenomeFigure:
    """
    Subgenome assignment visualization.

    Displays subgenome assignments along chromosomes with
    optional fractionation and gene density tracks.

    Parameters
    ----------
    reference : str or Path
        Reference genome (.fai)
    region : str, optional
        Region to display
    subgenomes : list[str], optional
        Subgenome names
    organism : str
        Organism for color presets
    title : str, optional
        Figure title
    figsize : tuple, optional
        Figure size

    Examples
    --------
    >>> fig = SubgenomeFigure("maize.fa.fai", subgenomes=['maize1', 'maize2'])
    >>> fig.add_subgenome_track("subgenome_assignments.bed")
    >>> fig.add_gene_density("gene_density.bedGraph")
    >>> fig.save("subgenomes.pdf")
    """

    def __init__(
        self,
        reference: str | Path,
        region: str | None = None,
        subgenomes: list[str] | None = None,
        organism: str = "auto",
        title: str | None = None,
        figsize: tuple[float, float] | None = None,
    ):
        self.coordinates = load_reference(reference)
        self.region = region
        self.subgenomes = subgenomes or ["SG1", "SG2"]
        self.organism = organism
        self.title = title
        self.figsize = figsize or (12, 6)

        self._tracks: list[tuple[str, dict]] = []
        self._fig: cp.GenomeFigure | None = None

    def add_ideogram(self, **style) -> "SubgenomeFigure":
        """Add chromosome backbone."""
        self._tracks.append(("ideogram", {"style": style}))
        return self

    def add_subgenome_track(
        self,
        path: str | Path,
        label: str = "Subgenome",
        **style,
    ) -> "SubgenomeFigure":
        """
        Add subgenome assignment track.

        Parameters
        ----------
        path : str or Path
            Path to subgenome BED file
        label : str
            Track label
        """
        self._tracks.append((
            "subgenome",
            {
                "path": path,
                "label": label,
                "style": style,
            },
        ))
        return self

    def add_gene_density(
        self,
        path: str | Path,
        label: str = "Gene density",
        **style,
    ) -> "SubgenomeFigure":
        """Add gene density signal track."""
        self._tracks.append((
            "signal",
            {
                "path": path,
                "label": label,
                "style": style,
            },
        ))
        return self

    def add_fractionation(
        self,
        path: str | Path,
        label: str = "Fractionation",
        **style,
    ) -> "SubgenomeFigure":
        """
        Add fractionation bias track.

        Shows which subgenome retained more genes per window.
        """
        self._tracks.append((
            "signal",
            {
                "path": path,
                "label": label,
                "style": {"cmap": "RdBu_r", **style},
            },
        ))
        return self

    def add_scale_bar(self, **style) -> "SubgenomeFigure":
        """Add scale bar."""
        self._tracks.append(("scale", {"style": style}))
        return self

    def render(self) -> cp.GenomeFigure:
        """Render the figure."""
        self._fig = cp.GenomeFigure(
            reference=self.coordinates,
            region=self.region,
            figsize=self.figsize,
            theme=get_phaser_theme(),
            title=self.title,
        )

        for track_type, config in self._tracks:
            track = self._create_track(track_type, config)
            self._fig.add_track(track)

        return self._fig.render()

    def _create_track(self, track_type: str, config: dict):
        """Create track."""
        style = config.get("style", {})

        if track_type == "ideogram":
            return cp.IdeogramTrack(style=style)

        elif track_type == "subgenome":
            colors = get_subgenome_colors(self.subgenomes, self.organism)
            if "color_map" not in style:
                style["color_map"] = colors

            return cp.HaplotypeTrack(
                config["path"],
                founders=self.subgenomes,
                label=config.get("label"),
                style=style,
            )

        elif track_type == "signal":
            return cp.SignalTrack(
                config["path"],
                label=config.get("label"),
                style=style,
            )

        elif track_type == "scale":
            return cp.ScaleBarTrack(style=style)

        raise ValueError(f"Unknown track type: {track_type}")

    def save(self, path: str | Path, **kwargs) -> None:
        """Save figure."""
        if self._fig is None:
            self.render()
        self._fig.save(path, **kwargs)

    def show(self) -> None:
        """Display figure."""
        if self._fig is None:
            self.render()
        self._fig.show()
