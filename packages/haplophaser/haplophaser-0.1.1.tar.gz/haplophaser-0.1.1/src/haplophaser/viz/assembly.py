"""Assembly painting visualization."""

from __future__ import annotations

from pathlib import Path

import chromoplot as cp

from .utils import get_founder_colors, get_phaser_theme, load_reference


class AssemblyPaintingFigure:
    """
    Assembly haplotype painting visualization.

    Shows contig assignments to haplotypes/subgenomes with
    optional chimera highlighting.

    Parameters
    ----------
    reference : str or Path
        Reference/assembly genome (.fai)
    region : str, optional
        Region to display
    founders : list[str], optional
        Founder/haplotype names
    title : str, optional
        Figure title
    figsize : tuple, optional
        Figure size

    Examples
    --------
    >>> fig = AssemblyPaintingFigure("assembly.fa.fai")
    >>> fig.add_painting("contig_assignments.bed")
    >>> fig.add_chimeras("chimera_breakpoints.bed")
    >>> fig.save("assembly_painting.pdf")
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
        self.figsize = figsize or (14, 6)

        self._tracks: list[tuple[str, dict]] = []
        self._fig: cp.GenomeFigure | None = None

    def add_ideogram(self, **style) -> "AssemblyPaintingFigure":
        """Add contig/chromosome backbone."""
        self._tracks.append(("ideogram", {"style": style}))
        return self

    def add_painting(
        self,
        path: str | Path,
        label: str = "Haplotype",
        **style,
    ) -> "AssemblyPaintingFigure":
        """
        Add contig haplotype painting track.

        Parameters
        ----------
        path : str or Path
            Path to painting BED file
        label : str
            Track label
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

    def add_chimeras(
        self,
        path: str | Path,
        label: str = "Chimeras",
        **style,
    ) -> "AssemblyPaintingFigure":
        """
        Add chimera breakpoint markers.

        Parameters
        ----------
        path : str or Path
            Path to chimera BED file
        label : str
            Track label
        """
        default_style = {
            "marker": "|",
            "marker_size": 100,
            "marker_color": "#d62728",
            "show_line": True,
            "line_color": "#d62728",
            "line_style": "-",
            "line_width": 2,
        }
        default_style.update(style)

        self._tracks.append((
            "annotation",
            {
                "path": path,
                "label": label,
                "style": default_style,
            },
        ))
        return self

    def add_markers(
        self,
        path: str | Path,
        label: str = "Markers",
        **style,
    ) -> "AssemblyPaintingFigure":
        """Add diagnostic marker density track."""
        default_style = {
            "plot_type": "density",
            "density_color": "#2ca02c",
        }
        default_style.update(style)

        self._tracks.append((
            "variant",
            {
                "path": path,
                "label": label,
                "style": default_style,
            },
        ))
        return self

    def add_scale_bar(self, **style) -> "AssemblyPaintingFigure":
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
        """Create chromoplot track."""
        style = config.get("style", {})

        if track_type == "ideogram":
            return cp.IdeogramTrack(style=style)

        elif track_type == "haplotype":
            founders = config.get("founders") or self.founders
            if founders:
                colors = get_founder_colors(founders, use_maize_colors=False)
                if "color_map" not in style:
                    style["color_map"] = colors

            return cp.HaplotypeTrack(
                config["path"],
                founders=founders,
                label=config.get("label"),
                style=style,
            )

        elif track_type == "annotation":
            return cp.AnnotationTrack(
                config["path"],
                label=config.get("label"),
                style=style,
            )

        elif track_type == "variant":
            return cp.VariantTrack(
                config["path"],
                label=config.get("label"),
                plot_type=style.pop("plot_type", "density"),
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
