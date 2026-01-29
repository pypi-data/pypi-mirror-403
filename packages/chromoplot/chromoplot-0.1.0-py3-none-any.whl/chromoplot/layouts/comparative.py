"""Comparative layout for two-genome synteny visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region

if TYPE_CHECKING:
    from ..tracks.base import BaseTrack
    from ..tracks.synteny import SyntenyTrack
    from ..themes.theme import Theme


class ComparativeLayout:
    """
    Layout for comparing two genomes with synteny.

    Displays reference genome tracks on top, query genome tracks
    on bottom, with synteny ribbons connecting them.

    Parameters
    ----------
    ref_coordinates : GenomeCoordinates
        Reference genome coordinates
    query_coordinates : GenomeCoordinates
        Query genome coordinates
    ref_region : str or Region, optional
        Region to display from reference
    query_region : str or Region, optional
        Region to display from query
    figsize : tuple, optional
        Figure size
    theme : Theme, optional
        Visual theme

    Examples
    --------
    >>> layout = ComparativeLayout(ref_coords, query_coords)
    >>> layout.add_ref_track(IdeogramTrack())
    >>> layout.add_ref_track(GeneTrack("ref_genes.gff3"))
    >>> layout.add_synteny_track(SyntenyTrack("synteny.paf"))
    >>> layout.add_query_track(GeneTrack("query_genes.gff3"))
    >>> layout.add_query_track(IdeogramTrack())
    >>> fig = layout.render()
    """

    def __init__(
        self,
        ref_coordinates: GenomeCoordinates,
        query_coordinates: GenomeCoordinates,
        ref_region: str | Region | None = None,
        query_region: str | Region | None = None,
        figsize: tuple[float, float] | None = None,
        theme: 'Theme' | None = None,
    ):
        self.ref_coordinates = ref_coordinates
        self.query_coordinates = query_coordinates

        # Parse regions
        if ref_region is None:
            # Use first chromosome
            chrom = ref_coordinates.chromosome_names[0]
            self.ref_region = Region.whole_chromosome(chrom, ref_coordinates)
        elif isinstance(ref_region, str):
            self.ref_region = Region.parse(ref_region, ref_coordinates)
        else:
            self.ref_region = ref_region

        if query_region is None:
            chrom = query_coordinates.chromosome_names[0]
            self.query_region = Region.whole_chromosome(chrom, query_coordinates)
        elif isinstance(query_region, str):
            self.query_region = Region.parse(query_region, query_coordinates)
        else:
            self.query_region = query_region

        self.figsize = figsize or (14, 10)

        from ..themes.theme import get_theme
        self.theme = theme or get_theme('publication')

        self._ref_tracks: list[BaseTrack] = []
        self._query_tracks: list[BaseTrack] = []
        self._synteny_track: SyntenyTrack | None = None

        self._fig: plt.Figure | None = None

    def add_ref_track(self, track: 'BaseTrack') -> 'ComparativeLayout':
        """Add track to reference genome (top)."""
        self._ref_tracks.append(track)
        return self

    def add_query_track(self, track: 'BaseTrack') -> 'ComparativeLayout':
        """Add track to query genome (bottom)."""
        self._query_tracks.append(track)
        return self

    def add_synteny_track(self, track: 'SyntenyTrack') -> 'ComparativeLayout':
        """Add synteny track (middle)."""
        self._synteny_track = track
        return self

    def render(self) -> plt.Figure:
        """Render the comparative figure."""
        n_ref_tracks = len(self._ref_tracks)
        n_query_tracks = len(self._query_tracks)
        has_synteny = self._synteny_track is not None

        # Calculate height ratios
        # Reference tracks : synteny : query tracks
        ref_heights = [t.height for t in self._ref_tracks]
        query_heights = [t.height for t in self._query_tracks]
        synteny_height = self._synteny_track.height if has_synteny else 0

        total_ref = sum(ref_heights)
        total_query = sum(query_heights)

        height_ratios = ref_heights + ([synteny_height] if has_synteny else []) + query_heights
        n_rows = len(height_ratios)

        # Create figure
        self._fig = plt.figure(figsize=self.figsize)
        self._fig.patch.set_facecolor(self.theme.figure_facecolor)

        gs = gridspec.GridSpec(
            n_rows, 1,
            figure=self._fig,
            height_ratios=height_ratios,
            hspace=0.05,
        )

        axes = []

        # Render reference tracks (top)
        for i, track in enumerate(self._ref_tracks):
            ax = self._fig.add_subplot(gs[i])
            track.load_data(self.ref_region)
            track.render(ax, [self.ref_region], self.ref_coordinates)
            self._style_track_axes(ax, track, is_ref=True, is_top=(i == 0))
            axes.append(ax)

        # Render synteny (middle)
        if has_synteny:
            synteny_idx = n_ref_tracks
            ax_synteny = self._fig.add_subplot(gs[synteny_idx])

            # Load synteny data
            self._synteny_track.load_data(self.ref_region)

            # Calculate y positions for ribbons
            ref_y = 1.0
            query_y = 0.0

            # Set axis limits
            ax_synteny.set_xlim(self.ref_region.start, self.ref_region.end)
            ax_synteny.set_ylim(0, 1)

            # Render synteny ribbons
            self._synteny_track.render_between(
                ax_synteny,
                self.ref_region,
                self.query_region,
                ref_y, query_y,
                self.ref_coordinates,
                self.query_coordinates,
            )

            # Clean up synteny axes
            ax_synteny.set_yticks([])
            ax_synteny.axis('off')
            axes.append(ax_synteny)

        # Render query tracks (bottom)
        query_start_idx = n_ref_tracks + (1 if has_synteny else 0)
        for i, track in enumerate(self._query_tracks):
            ax = self._fig.add_subplot(gs[query_start_idx + i])
            track.load_data(self.query_region)
            track.render(ax, [self.query_region], self.query_coordinates)
            self._style_track_axes(
                ax, track,
                is_ref=False,
                is_bottom=(i == len(self._query_tracks) - 1)
            )
            axes.append(ax)

        # Add titles
        if self._ref_tracks:
            axes[0].set_title(
                f"Reference: {self.ref_region.chrom}",
                fontsize=self.theme.title_fontsize,
                fontweight='bold',
            )

        query_title_idx = n_ref_tracks + (1 if has_synteny else 0)
        if self._query_tracks and query_title_idx < len(axes):
            # Add query label
            pass

        plt.tight_layout()
        return self._fig

    def _style_track_axes(
        self,
        ax: plt.Axes,
        track: 'BaseTrack',
        is_ref: bool,
        is_top: bool = False,
        is_bottom: bool = False,
    ) -> None:
        """Style track axes."""
        # Track label
        if track.label:
            ax.set_ylabel(
                track.label,
                fontsize=self.theme.label_fontsize,
                rotation=0,
                ha='right',
                va='center',
            )

        # Remove spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        # X-axis only on bottom
        if not is_bottom:
            ax.tick_params(axis='x', labelbottom=False)
        else:
            from matplotlib.ticker import FuncFormatter
            ax.xaxis.set_major_formatter(
                FuncFormatter(lambda x, p: f'{x/1e6:.1f}')
            )
            ax.set_xlabel('Position (Mb)', fontsize=self.theme.label_fontsize)

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
