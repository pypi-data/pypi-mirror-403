"""Main GenomeFigure class for creating genome visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .coordinates import GenomeCoordinates
from .regions import Region, parse_regions

if TYPE_CHECKING:
    from ..tracks.base import BaseTrack
    from ..themes.theme import Theme


class GenomeFigure:
    """
    Main class for creating genome visualizations.

    Manages tracks, layout, and rendering to create publication-ready
    genome figures.

    Parameters
    ----------
    reference : str, Path, dict, or GenomeCoordinates
        Reference genome specification. Can be:
        - Path to .fai file
        - Path to chrom.sizes file
        - Dictionary of {chrom: size}
        - GenomeCoordinates object
    region : str, optional
        Region to display (e.g., "chr1:1000000-2000000").
        If None, displays all chromosomes.
    figsize : tuple[float, float], optional
        Figure size in inches (width, height)
    theme : str or Theme, optional
        Color theme name or Theme object
    title : str, optional
        Figure title

    Examples
    --------
    >>> fig = GenomeFigure("genome.fa.fai", region="chr1:1-10000000")
    >>> fig.add_track(FeatureTrack("genes.bed"))
    >>> fig.add_track(HaplotypeTrack("haplotypes.bed"))
    >>> fig.save("figure.pdf")
    """

    def __init__(
        self,
        reference: str | Path | dict | GenomeCoordinates,
        region: str | None = None,
        figsize: tuple[float, float] | None = None,
        theme: str | Theme | None = None,
        title: str | None = None,
    ):
        # Set up coordinates
        self.coordinates = self._parse_reference(reference)

        # Parse region
        self.regions = parse_regions(region, self.coordinates)
        self.is_whole_genome = region is None

        # Set up theme
        from ..themes.theme import get_theme
        if theme is None:
            self.theme = get_theme('publication')
        elif isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme

        # Figure settings
        self.figsize = figsize or self._default_figsize()
        self.title = title

        # Track storage
        self._tracks: list[BaseTrack] = []

        # Matplotlib objects (created on render)
        self._fig: plt.Figure | None = None
        self._axes: list[plt.Axes] = []

    def _parse_reference(
        self,
        reference: str | Path | dict | GenomeCoordinates
    ) -> GenomeCoordinates:
        """Parse reference into GenomeCoordinates."""
        if isinstance(reference, GenomeCoordinates):
            return reference

        if isinstance(reference, dict):
            return GenomeCoordinates.from_dict(reference)

        path = Path(reference)
        if path.suffix == '.fai':
            return GenomeCoordinates.from_fai(path)
        elif path.name.endswith('.sizes') or path.name.endswith('chrom.sizes'):
            return GenomeCoordinates.from_chrom_sizes(path)
        else:
            # Try .fai first, then chrom.sizes format
            try:
                return GenomeCoordinates.from_fai(path)
            except Exception:
                return GenomeCoordinates.from_chrom_sizes(path)

    def _default_figsize(self) -> tuple[float, float]:
        """Calculate default figure size based on content."""
        if self.is_whole_genome:
            # Wider for whole genome
            return (14, 8)
        else:
            # Standard for single region
            return (12, 6)

    def add_track(self, track: BaseTrack) -> GenomeFigure:
        """
        Add a track to the figure.

        Parameters
        ----------
        track : BaseTrack
            Track to add

        Returns
        -------
        GenomeFigure
            Self, for method chaining
        """
        self._tracks.append(track)
        return self

    def remove_track(self, index: int) -> BaseTrack:
        """
        Remove a track by index.

        Parameters
        ----------
        index : int
            Track index

        Returns
        -------
        BaseTrack
            Removed track
        """
        return self._tracks.pop(index)

    @property
    def n_tracks(self) -> int:
        """Number of tracks."""
        return len(self._tracks)

    def render(self) -> plt.Figure:
        """
        Render the figure.

        Returns
        -------
        matplotlib.Figure
            Rendered figure
        """
        # Calculate layout
        total_height = sum(t.height for t in self._tracks)
        height_ratios = [t.height for t in self._tracks]

        # Create figure and axes
        self._fig, axes = plt.subplots(
            nrows=len(self._tracks),
            ncols=1,
            figsize=self.figsize,
            gridspec_kw={
                'height_ratios': height_ratios,
                'hspace': self.theme.track_spacing,
            },
            squeeze=False,
        )
        self._axes = [ax[0] for ax in axes]

        # Apply theme to figure
        self._fig.patch.set_facecolor(self.theme.figure_facecolor)

        # Render each track
        for track, ax in zip(self._tracks, self._axes):
            # Load data for regions
            for region in self.regions:
                track.load_data(region)

            # Render track
            track.render(ax, self.regions, self.coordinates)

            # Apply track styling
            self._style_track_axes(ax, track)

        # Add title if specified
        if self.title:
            self._fig.suptitle(
                self.title,
                fontsize=self.theme.title_fontsize,
                fontfamily=self.theme.font_family,
            )

        # Add x-axis label to bottom track
        if self._axes:
            self._add_genomic_axis(self._axes[-1])

        plt.tight_layout()

        return self._fig

    def _style_track_axes(self, ax: plt.Axes, track: BaseTrack) -> None:
        """Apply theme styling to track axes."""
        # Track label
        if track.label:
            ax.set_ylabel(
                track.label,
                fontsize=self.theme.label_fontsize,
                fontfamily=self.theme.font_family,
                rotation=0,
                ha='right',
                va='center',
            )

        # Spine styling
        for spine in ax.spines.values():
            spine.set_color(self.theme.spine_color)
            spine.set_linewidth(self.theme.spine_width)

        # Remove top and right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Y-axis ticks
        ax.tick_params(
            axis='y',
            labelsize=self.theme.tick_fontsize,
        )

        # Hide x-axis for all but bottom track
        ax.tick_params(axis='x', labelbottom=False)

    def _add_genomic_axis(self, ax: plt.Axes) -> None:
        """Add genomic coordinate axis to bottom track."""
        ax.tick_params(axis='x', labelbottom=True)
        ax.set_xlabel(
            'Position (Mb)',
            fontsize=self.theme.label_fontsize,
            fontfamily=self.theme.font_family,
        )

        # Format x-axis as Mb
        from matplotlib.ticker import FuncFormatter
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda x, p: f'{x/1e6:.1f}')
        )

    def save(
        self,
        path: str | Path,
        dpi: int = 300,
        transparent: bool = False,
        bbox_inches: str = 'tight',
        **kwargs,
    ) -> None:
        """
        Save figure to file.

        Parameters
        ----------
        path : str or Path
            Output file path. Format inferred from extension.
        dpi : int
            Resolution for raster formats
        transparent : bool
            Transparent background
        bbox_inches : str
            Bounding box setting
        **kwargs
            Additional arguments passed to savefig
        """
        if self._fig is None:
            self.render()

        self._fig.savefig(
            path,
            dpi=dpi,
            transparent=transparent,
            bbox_inches=bbox_inches,
            facecolor=self._fig.get_facecolor(),
            edgecolor='none',
            **kwargs,
        )

    def show(self) -> None:
        """Display figure interactively."""
        if self._fig is None:
            self.render()
        plt.show()

    def close(self) -> None:
        """Close figure and free memory."""
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._axes = []
