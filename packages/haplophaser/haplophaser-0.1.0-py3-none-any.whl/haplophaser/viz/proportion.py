"""Haplotype proportion visualization."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import chromoplot as cp

from .utils import get_founder_colors, get_phaser_theme, load_reference

if TYPE_CHECKING:
    pass


class ProportionFigure:
    """
    Single-region haplotype proportion figure.

    Displays haplotype blocks, optional genes, and other tracks
    for a specific genomic region.

    Parameters
    ----------
    reference : str or Path
        Reference genome (.fai or .sizes)
    region : str, optional
        Region to display (e.g., "chr1:1-10000000")
    founders : list[str], optional
        Founder names for color assignment
    title : str, optional
        Figure title
    figsize : tuple, optional
        Figure size (width, height)

    Examples
    --------
    >>> fig = ProportionFigure("genome.fa.fai", region="chr1:1-10000000")
    >>> fig.add_haplotypes("haplotype_blocks.bed")
    >>> fig.add_genes("genes.gff3")
    >>> fig.save("haplotypes.pdf")
    """

    def __init__(
        self,
        reference: str | Path,
        region: str | None = None,
        founders: list[str] | None = None,
        title: str | None = None,
        figsize: tuple[float, float] | None = None,
    ):
        self.coordinates = load_reference(reference)
        self.region = region
        self.founders = founders
        self.title = title
        self.figsize = figsize or (12, 6)

        self._tracks: list[tuple[str, dict]] = []
        self._fig: cp.GenomeFigure | None = None

    def add_ideogram(self, **style) -> "ProportionFigure":
        """Add chromosome ideogram track."""
        self._tracks.append(("ideogram", {"style": style}))
        return self

    def add_haplotypes(
        self,
        path: str | Path,
        label: str = "Haplotypes",
        **style,
    ) -> "ProportionFigure":
        """
        Add haplotype block track.

        Parameters
        ----------
        path : str or Path
            Path to haplotype BED file
        label : str
            Track label
        **style
            Additional style parameters
        """
        self._tracks.append((
            "haplotype",
            {
                "path": path,
                "label": label,
                "founders": self.founders,
                "style": style,
            },
        ))
        return self

    def add_proportions(
        self,
        path: str | Path,
        founder: str,
        label: str | None = None,
        **style,
    ) -> "ProportionFigure":
        """
        Add proportion signal track for a specific founder.

        Parameters
        ----------
        path : str or Path
            Path to bedGraph file with proportions
        founder : str
            Founder name (for labeling)
        label : str, optional
            Track label (default: "{founder} proportion")
        **style
            Additional style parameters
        """
        self._tracks.append((
            "signal",
            {
                "path": path,
                "label": label or f"{founder} proportion",
                "style": style,
            },
        ))
        return self

    def add_genes(
        self,
        path: str | Path,
        label: str = "Genes",
        **style,
    ) -> "ProportionFigure":
        """Add gene track."""
        self._tracks.append((
            "gene",
            {
                "path": path,
                "label": label,
                "style": style,
            },
        ))
        return self

    def add_features(
        self,
        path: str | Path,
        label: str | None = None,
        **style,
    ) -> "ProportionFigure":
        """Add generic feature track from BED."""
        self._tracks.append((
            "feature",
            {
                "path": path,
                "label": label or Path(path).stem,
                "style": style,
            },
        ))
        return self

    def add_breakpoints(
        self,
        path: str | Path,
        label: str = "Breakpoints",
        **style,
    ) -> "ProportionFigure":
        """Add recombination breakpoint markers."""
        self._tracks.append((
            "annotation",
            {
                "path": path,
                "label": label,
                "style": {"marker": "v", "marker_color": "#e41a1c", **style},
            },
        ))
        return self

    def add_scale_bar(self, **style) -> "ProportionFigure":
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
        """Create chromoplot track from config."""
        style = config.get("style", {})

        if track_type == "ideogram":
            return cp.IdeogramTrack(style=style)

        elif track_type == "haplotype":
            # Apply founder colors
            founders = config.get("founders") or self.founders
            if founders:
                colors = get_founder_colors(founders)
                # Inject into style if not overridden
                if "color_map" not in style:
                    style["color_map"] = colors

            return cp.HaplotypeTrack(
                config["path"],
                founders=founders,
                label=config.get("label"),
                style=style,
            )

        elif track_type == "signal":
            return cp.SignalTrack(
                config["path"],
                label=config.get("label"),
                style=style,
            )

        elif track_type == "gene":
            return cp.GeneTrack(
                config["path"],
                label=config.get("label"),
                style=style,
            )

        elif track_type == "feature":
            return cp.FeatureTrack(
                config["path"],
                label=config.get("label"),
                style=style,
            )

        elif track_type == "annotation":
            return cp.AnnotationTrack(
                config["path"],
                label=config.get("label"),
                style=style,
            )

        elif track_type == "scale":
            return cp.ScaleBarTrack(style=style)

        else:
            raise ValueError(f"Unknown track type: {track_type}")

    def save(self, path: str | Path, **kwargs) -> None:
        """Save figure to file."""
        if self._fig is None:
            self.render()
        self._fig.save(path, **kwargs)

    def show(self) -> None:
        """Display figure interactively."""
        if self._fig is None:
            self.render()
        self._fig.show()


class ProportionGenomeFigure:
    """
    Whole-genome haplotype proportion figure.

    Displays haplotype blocks across all chromosomes in a grid layout.

    Parameters
    ----------
    reference : str or Path
        Reference genome (.fai or .sizes)
    founders : list[str], optional
        Founder names for color assignment
    n_cols : int
        Number of columns in grid
    figsize : tuple, optional
        Figure size

    Examples
    --------
    >>> fig = ProportionGenomeFigure("genome.fa.fai", n_cols=5)
    >>> fig.add_haplotypes("haplotype_blocks.bed")
    >>> fig.save("genome_haplotypes.pdf")
    """

    def __init__(
        self,
        reference: str | Path,
        founders: list[str] | None = None,
        n_cols: int = 5,
        figsize: tuple[float, float] | None = None,
    ):
        self.coordinates = load_reference(reference)
        self.founders = founders
        self.n_cols = n_cols
        self.figsize = figsize

        self._tracks: list[tuple[str, dict]] = []
        self._layout: cp.GenomeLayout | None = None

    def add_ideogram(self, **style) -> "ProportionGenomeFigure":
        """Add ideogram track to all chromosomes."""
        self._tracks.append(("ideogram", {"style": style}))
        return self

    def add_haplotypes(
        self,
        path: str | Path,
        label: str = "Haplotypes",
        **style,
    ) -> "ProportionGenomeFigure":
        """Add haplotype track to all chromosomes."""
        self._tracks.append((
            "haplotype",
            {
                "path": path,
                "label": label,
                "founders": self.founders,
                "style": style,
            },
        ))
        return self

    def render(self) -> cp.GenomeLayout:
        """Render the figure."""
        # Calculate figsize based on content
        n_chroms = self.coordinates.n_chromosomes
        n_rows = (n_chroms + self.n_cols - 1) // self.n_cols
        n_tracks = len(self._tracks)

        if self.figsize is None:
            width = 3 * self.n_cols
            height = 1.2 * n_tracks * n_rows
            self.figsize = (width, height)

        self._layout = cp.GenomeLayout(
            self.coordinates,
            arrangement="grid",
            n_cols=self.n_cols,
            figsize=self.figsize,
            theme=get_phaser_theme(),
        )

        for track_type, config in self._tracks:
            track = self._create_track(track_type, config)
            self._layout.add_track(track)

        return self._layout.render()

    def _create_track(self, track_type: str, config: dict):
        """Create track (same as ProportionFigure)."""
        style = config.get("style", {})

        if track_type == "ideogram":
            return cp.IdeogramTrack(style=style)

        elif track_type == "haplotype":
            founders = config.get("founders") or self.founders
            if founders:
                colors = get_founder_colors(founders)
                if "color_map" not in style:
                    style["color_map"] = colors

            return cp.HaplotypeTrack(
                config["path"],
                founders=founders,
                label=config.get("label"),
                style=style,
            )

        raise ValueError(f"Unknown track type: {track_type}")

    def save(self, path: str | Path, **kwargs) -> None:
        """Save figure."""
        if self._layout is None:
            self.render()
        self._layout.save(path, **kwargs)

    def show(self) -> None:
        """Display figure."""
        if self._layout is None:
            self.render()
        self._layout.show()
