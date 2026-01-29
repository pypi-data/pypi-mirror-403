"""Whole-genome layout for multi-chromosome visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from .base import BaseLayout
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region

if TYPE_CHECKING:
    from ..tracks.base import BaseTrack
    from ..themes.theme import Theme


class GenomeLayout(BaseLayout):
    """
    Layout for whole-genome visualization.

    Displays all chromosomes in a grid or linear arrangement
    with shared tracks.

    Parameters
    ----------
    coordinates : GenomeCoordinates
        Genome coordinate system
    arrangement : str
        'grid', 'horizontal', 'vertical'
    n_cols : int, optional
        Number of columns for grid arrangement
    figsize : tuple, optional
        Figure size (auto-calculated if None)
    theme : Theme, optional
        Visual theme

    Examples
    --------
    >>> layout = GenomeLayout(coordinates, arrangement='grid')
    >>> layout.add_track(IdeogramTrack())
    >>> layout.add_track(HaplotypeTrack("haplotypes.bed"))
    >>> fig = layout.render()
    """

    def __init__(
        self,
        coordinates: GenomeCoordinates,
        arrangement: str = 'grid',
        n_cols: int | None = None,
        figsize: tuple[float, float] | None = None,
        theme: 'Theme' | None = None,
    ):
        self.coordinates = coordinates
        self.arrangement = arrangement
        self.n_cols = n_cols or self._default_cols()
        self.figsize = figsize

        from ..themes.theme import get_theme
        self.theme = theme or get_theme('publication')

        self._tracks: list[BaseTrack] = []
        self._fig: plt.Figure | None = None
        self._offset_cache: dict[str, float] = {}

    def _default_cols(self) -> int:
        """Calculate default number of columns."""
        n_chroms = self.coordinates.n_chromosomes
        if self.arrangement == 'horizontal':
            return n_chroms
        elif self.arrangement == 'vertical':
            return 1
        else:  # grid
            return min(5, max(2, int(np.sqrt(n_chroms))))

    def add_track(self, track: 'BaseTrack') -> 'GenomeLayout':
        """Add track to all chromosomes."""
        self._tracks.append(track)
        return self

    def setup_axes(
        self,
        fig: plt.Figure,
        regions: list[Region],
        n_tracks: int,
    ) -> list[list[plt.Axes]]:
        """Create axes spanning all chromosomes (BaseLayout interface)."""
        # For compatibility with base interface
        height_ratios = [1.0] * n_tracks

        axes = fig.subplots(
            nrows=n_tracks,
            ncols=1,
            gridspec_kw={
                'height_ratios': height_ratios,
                'hspace': self.theme.track_spacing,
            },
            squeeze=False,
        )

        # Calculate chromosome offsets
        total_size = sum(len(r) for r in regions)
        gap_total = 0.02 * len(regions)
        scale = (1.0 - gap_total) / total_size

        offset = 0.0
        for region in regions:
            self._offset_cache[region.chrom] = offset
            offset += len(region) * scale + 0.02

        return [[ax[0]] for ax in axes]

    def transform_position(
        self,
        chrom: str,
        pos: int,
        coordinates: GenomeCoordinates,
    ) -> float:
        """Transform to linearized genome position."""
        offset = self._offset_cache.get(chrom, 0.0)
        return offset + pos

    def render(self) -> plt.Figure:
        """Render the whole-genome figure."""
        chroms = self.coordinates.chromosome_names
        n_chroms = len(chroms)
        n_tracks = len(self._tracks)

        if n_tracks == 0:
            raise ValueError("No tracks added to layout")

        # Calculate grid dimensions
        n_cols = self.n_cols
        n_rows = (n_chroms + n_cols - 1) // n_cols

        # Calculate figure size
        if self.figsize is None:
            width = 3 * n_cols
            height = 1.5 * n_tracks * n_rows
            self.figsize = (width, height)

        # Create figure
        self._fig = plt.figure(figsize=self.figsize)
        self._fig.patch.set_facecolor(self.theme.figure_facecolor)

        # Create outer grid for chromosomes
        outer_grid = gridspec.GridSpec(
            n_rows, n_cols,
            figure=self._fig,
            hspace=0.3,
            wspace=0.2,
        )

        # Render each chromosome
        for chrom_idx, chrom in enumerate(chroms):
            row = chrom_idx // n_cols
            col = chrom_idx % n_cols

            # Create inner grid for tracks
            inner_grid = gridspec.GridSpecFromSubplotSpec(
                n_tracks, 1,
                subplot_spec=outer_grid[row, col],
                hspace=self.theme.track_spacing,
            )

            # Get region for this chromosome
            region = Region.whole_chromosome(chrom, self.coordinates)

            # Render each track
            for track_idx, track in enumerate(self._tracks):
                ax = self._fig.add_subplot(inner_grid[track_idx])

                # Load and render track
                track.load_data(region)
                track.render(ax, [region], self.coordinates)

                # Style axes
                self._style_axes(ax, track, chrom, track_idx, n_tracks)

                # Clear track data for next chromosome
                track.clear_data()

        plt.tight_layout()
        return self._fig

    def _style_axes(
        self,
        ax: plt.Axes,
        track: 'BaseTrack',
        chrom: str,
        track_idx: int,
        n_tracks: int,
    ) -> None:
        """Apply styling to chromosome/track axes."""
        # Add chromosome label to top track
        if track_idx == 0:
            ax.set_title(
                chrom,
                fontsize=self.theme.label_fontsize,
                fontweight='bold',
            )

        # Remove x-axis labels except bottom
        if track_idx < n_tracks - 1:
            ax.tick_params(axis='x', labelbottom=False)
        else:
            # Format as Mb
            from matplotlib.ticker import FuncFormatter
            ax.xaxis.set_major_formatter(
                FuncFormatter(lambda x, p: f'{x/1e6:.0f}')
            )
            ax.set_xlabel('Mb', fontsize=self.theme.tick_fontsize)

        # Track label (only on leftmost)
        if track.label:
            ax.set_ylabel(
                track.label,
                fontsize=self.theme.tick_fontsize,
                rotation=90,
                va='center',
            )

        # Clean up spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

    def save(self, path: str, **kwargs) -> None:
        """Save figure."""
        if self._fig is None:
            self.render()
        self._fig.savefig(path, bbox_inches='tight', **kwargs)

    def show(self) -> None:
        """Display figure."""
        if self._fig is None:
            self.render()
        plt.show()
