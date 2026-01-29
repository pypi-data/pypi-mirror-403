"""Comparative/synteny visualization."""

from __future__ import annotations

from pathlib import Path

import chromoplot as cp

from .utils import get_phaser_theme, load_reference


class SyntenyFigure:
    """
    Synteny visualization between two genomes.

    Creates comparative figures showing synteny relationships
    between reference and query genomes.

    Parameters
    ----------
    ref_reference : str or Path
        Reference genome .fai file
    query_reference : str or Path
        Query genome .fai file
    ref_region : str, optional
        Region to display on reference
    query_region : str, optional
        Region to display on query
    title : str, optional
        Figure title
    figsize : tuple, optional
        Figure size

    Examples
    --------
    >>> fig = SyntenyFigure("ref.fa.fai", "query.fa.fai")
    >>> fig.add_synteny("alignment.paf")
    >>> fig.add_ref_genes("ref_genes.gff3")
    >>> fig.add_query_genes("query_genes.gff3")
    >>> fig.save("synteny.pdf")
    """

    def __init__(
        self,
        ref_reference: str | Path,
        query_reference: str | Path,
        ref_region: str | None = None,
        query_region: str | None = None,
        title: str | None = None,
        figsize: tuple[float, float] | None = None,
    ):
        self.ref_coordinates = load_reference(ref_reference)
        self.query_coordinates = load_reference(query_reference)
        self.ref_region = ref_region
        self.query_region = query_region
        self.title = title
        self.figsize = figsize or (14, 10)

        self._ref_tracks: list[tuple[str, dict]] = []
        self._query_tracks: list[tuple[str, dict]] = []
        self._synteny_track: tuple[str, dict] | None = None
        self._layout: cp.ComparativeLayout | None = None

    def add_ref_ideogram(self, **style) -> "SyntenyFigure":
        """Add reference chromosome ideogram."""
        self._ref_tracks.append(("ideogram", {"style": style}))
        return self

    def add_query_ideogram(self, **style) -> "SyntenyFigure":
        """Add query chromosome ideogram."""
        self._query_tracks.append(("ideogram", {"style": style}))
        return self

    def add_ref_genes(
        self,
        path: str | Path,
        label: str = "Genes",
        **style,
    ) -> "SyntenyFigure":
        """Add reference gene track."""
        self._ref_tracks.append((
            "gene",
            {
                "path": path,
                "label": label,
                "style": style,
            },
        ))
        return self

    def add_query_genes(
        self,
        path: str | Path,
        label: str = "Genes",
        **style,
    ) -> "SyntenyFigure":
        """Add query gene track."""
        self._query_tracks.append((
            "gene",
            {
                "path": path,
                "label": label,
                "style": style,
            },
        ))
        return self

    def add_ref_features(
        self,
        path: str | Path,
        label: str | None = None,
        **style,
    ) -> "SyntenyFigure":
        """Add reference feature track."""
        self._ref_tracks.append((
            "feature",
            {
                "path": path,
                "label": label or Path(path).stem,
                "style": style,
            },
        ))
        return self

    def add_query_features(
        self,
        path: str | Path,
        label: str | None = None,
        **style,
    ) -> "SyntenyFigure":
        """Add query feature track."""
        self._query_tracks.append((
            "feature",
            {
                "path": path,
                "label": label or Path(path).stem,
                "style": style,
            },
        ))
        return self

    def add_synteny(
        self,
        path: str | Path,
        **style,
    ) -> "SyntenyFigure":
        """
        Add synteny ribbons from alignment file.

        Parameters
        ----------
        path : str or Path
            Path to synteny file (PAF, SyRI, etc.)
        **style
            Additional style parameters
        """
        self._synteny_track = (
            "synteny",
            {
                "path": path,
                "style": style,
            },
        )
        return self

    def render(self) -> cp.ComparativeLayout:
        """Render the figure."""
        self._layout = cp.ComparativeLayout(
            self.ref_coordinates,
            self.query_coordinates,
            ref_region=self.ref_region,
            query_region=self.query_region,
            figsize=self.figsize,
            theme=get_phaser_theme(),
            title=self.title,
        )

        # Add reference tracks
        for track_type, config in self._ref_tracks:
            track = self._create_track(track_type, config)
            self._layout.add_ref_track(track)

        # Add synteny
        if self._synteny_track:
            _, config = self._synteny_track
            track = cp.SyntenyTrack(config["path"], style=config.get("style", {}))
            self._layout.add_synteny_track(track)

        # Add query tracks
        for track_type, config in self._query_tracks:
            track = self._create_track(track_type, config)
            self._layout.add_query_track(track)

        return self._layout.render()

    def _create_track(self, track_type: str, config: dict):
        """Create track."""
        style = config.get("style", {})

        if track_type == "ideogram":
            return cp.IdeogramTrack(style=style)

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
