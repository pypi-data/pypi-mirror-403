"""Synteny ribbon/link visualization track."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import PathPatch, Polygon
from matplotlib.path import Path as MplPath
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region
from ..io.synteny import read_synteny, SyntenyBlock


class SyntenyTrack(BaseTrack):
    """
    Synteny visualization between two genomes.

    Displays synteny blocks as ribbons or links connecting
    corresponding regions between reference and query genomes.

    Note: This track is typically used with ComparativeLayout,
    not GenomeFigure directly.

    Parameters
    ----------
    data_source : str or Path
        Path to synteny file (PAF, SyRI, etc.)
    format : str
        File format ('auto', 'paf', 'syri', 'mcscanx', 'bed')
    label : str, optional
        Track label
    height : float
        Track height (ribbon area)
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = SyntenyTrack("synteny.paf")
    >>> track = SyntenyTrack("syri.out", format='syri')
    """

    def __init__(
        self,
        data_source: str | Path,
        format: str = 'auto',
        label: str | None = None,
        height: float = 2.0,
        min_length: int = 10000,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.format = format
        self.min_length = min_length
        self._blocks: list[SyntenyBlock] = []

    def default_style(self) -> dict:
        return {
            # Colors
            'forward_color': '#4393c3',
            'reverse_color': '#d6604d',
            'color_by': 'orientation',  # 'orientation', 'identity', 'chromosome'
            'alpha': 0.6,

            # Ribbon style
            'ribbon_style': 'bezier',    # 'bezier', 'straight', 'arc'
            'ribbon_resolution': 50,      # Points for bezier curve

            # Borders
            'border_color': None,
            'border_width': 0.5,

            # Filtering
            'show_inversions': True,

            # Identity coloring
            'identity_cmap': 'RdYlGn',
            'identity_min': 0.8,
            'identity_max': 1.0,
        }

    def load_data(self, region: Region) -> None:
        """Load synteny blocks."""
        self._blocks = read_synteny(
            self.data_source,
            format=self.format,
            min_length=self.min_length,
        )
        self._loaded_regions.append(region)

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """
        Render synteny ribbons.

        For comparative layout, this renders between two y-levels.
        """
        # This basic render is for standalone use
        # ComparativeLayout calls render_between() instead
        pass

    def render_between(
        self,
        ax: plt.Axes,
        ref_region: Region,
        query_region: Region,
        ref_y: float,
        query_y: float,
        ref_coords: GenomeCoordinates,
        query_coords: GenomeCoordinates,
    ) -> None:
        """
        Render synteny ribbons between two genomic regions.

        Parameters
        ----------
        ax : Axes
            Matplotlib axes
        ref_region : Region
            Reference genome region
        query_region : Region
            Query genome region
        ref_y : float
            Y-coordinate for reference (top)
        query_y : float
            Y-coordinate for query (bottom)
        ref_coords : GenomeCoordinates
            Reference coordinate system
        query_coords : GenomeCoordinates
            Query coordinate system
        """
        style = self.style

        for block in self._blocks:
            # Filter to displayed regions
            if block.ref_chrom != ref_region.chrom:
                continue
            if block.ref_end <= ref_region.start or block.ref_start >= ref_region.end:
                continue

            # Skip inversions if requested
            if not style['show_inversions'] and block.orientation == '-':
                continue

            # Clip to region
            ref_start = max(block.ref_start, ref_region.start)
            ref_end = min(block.ref_end, ref_region.end)

            # Find corresponding query coordinates
            # (simplified - assumes linear mapping)
            block_ref_frac_start = (ref_start - block.ref_start) / max(block.ref_length, 1)
            block_ref_frac_end = (ref_end - block.ref_start) / max(block.ref_length, 1)

            if block.orientation == '+':
                query_start = block.query_start + block_ref_frac_start * block.query_length
                query_end = block.query_start + block_ref_frac_end * block.query_length
            else:
                query_start = block.query_end - block_ref_frac_start * block.query_length
                query_end = block.query_end - block_ref_frac_end * block.query_length
                query_start, query_end = query_end, query_start

            # Get color
            color = self._get_block_color(block)

            # Draw ribbon
            self._draw_ribbon(
                ax,
                ref_start, ref_end, ref_y,
                query_start, query_end, query_y,
                color, style['alpha'],
            )

    def _get_block_color(self, block: SyntenyBlock) -> str:
        """Get color for synteny block."""
        style = self.style

        if style['color_by'] == 'orientation':
            return style['forward_color'] if block.orientation == '+' else style['reverse_color']

        elif style['color_by'] == 'identity' and block.identity is not None:
            import matplotlib.colors as mcolors
            cmap = plt.get_cmap(style['identity_cmap'])
            norm = mcolors.Normalize(
                vmin=style['identity_min'],
                vmax=style['identity_max']
            )
            return cmap(norm(block.identity))

        elif style['color_by'] == 'chromosome':
            # Hash chromosome to color
            hash_val = hash(block.query_chrom) % 10
            palette = plt.get_cmap('tab10')
            return palette(hash_val)

        return style['forward_color']

    def _draw_ribbon(
        self,
        ax: plt.Axes,
        ref_start: float,
        ref_end: float,
        ref_y: float,
        query_start: float,
        query_end: float,
        query_y: float,
        color,
        alpha: float,
    ) -> None:
        """Draw a ribbon connecting two regions."""
        style = self.style

        if style['ribbon_style'] == 'straight':
            # Simple polygon
            vertices = [
                (ref_start, ref_y),
                (ref_end, ref_y),
                (query_end, query_y),
                (query_start, query_y),
            ]
            polygon = Polygon(
                vertices,
                facecolor=color,
                edgecolor=style['border_color'],
                linewidth=style['border_width'] if style['border_color'] else 0,
                alpha=alpha,
            )
            ax.add_patch(polygon)

        elif style['ribbon_style'] == 'bezier':
            # Bezier curve ribbon
            self._draw_bezier_ribbon(
                ax,
                ref_start, ref_end, ref_y,
                query_start, query_end, query_y,
                color, alpha,
            )

        elif style['ribbon_style'] == 'arc':
            # Arc-style ribbon
            self._draw_arc_ribbon(
                ax,
                ref_start, ref_end, ref_y,
                query_start, query_end, query_y,
                color, alpha,
            )

    def _draw_bezier_ribbon(
        self,
        ax: plt.Axes,
        ref_start: float,
        ref_end: float,
        ref_y: float,
        query_start: float,
        query_end: float,
        query_y: float,
        color,
        alpha: float,
    ) -> None:
        """Draw bezier curve ribbon."""
        style = self.style
        n_points = style['ribbon_resolution']

        # Control point offset (how curved the ribbon is)
        y_mid = (ref_y + query_y) / 2

        # Generate bezier curves for both sides
        t = np.linspace(0, 1, n_points)

        # Left edge bezier (ref_start to query_start)
        left_x = (1-t)**3 * ref_start + \
                 3*(1-t)**2*t * ref_start + \
                 3*(1-t)*t**2 * query_start + \
                 t**3 * query_start
        left_y = (1-t)**3 * ref_y + \
                 3*(1-t)**2*t * y_mid + \
                 3*(1-t)*t**2 * y_mid + \
                 t**3 * query_y

        # Right edge bezier (ref_end to query_end)
        right_x = (1-t)**3 * ref_end + \
                  3*(1-t)**2*t * ref_end + \
                  3*(1-t)*t**2 * query_end + \
                  t**3 * query_end
        right_y = left_y  # Same y values

        # Create closed polygon from both curves
        vertices = list(zip(left_x, left_y)) + list(zip(right_x[::-1], right_y[::-1]))

        polygon = Polygon(
            vertices,
            facecolor=color,
            edgecolor=style['border_color'],
            linewidth=style['border_width'] if style['border_color'] else 0,
            alpha=alpha,
        )
        ax.add_patch(polygon)

    def _draw_arc_ribbon(
        self,
        ax: plt.Axes,
        ref_start: float,
        ref_end: float,
        ref_y: float,
        query_start: float,
        query_end: float,
        query_y: float,
        color,
        alpha: float,
    ) -> None:
        """Draw arc-style ribbon (semicircle connections)."""
        style = self.style
        n_points = style['ribbon_resolution']

        # Create arc using sine curve
        t = np.linspace(0, np.pi, n_points)

        # Left arc
        left_x = ref_start + (query_start - ref_start) * (1 - np.cos(t)) / 2
        y_range = ref_y - query_y
        left_y = ref_y - y_range * (1 - np.cos(t)) / 2

        # Right arc
        right_x = ref_end + (query_end - ref_end) * (1 - np.cos(t)) / 2
        right_y = left_y

        vertices = list(zip(left_x, left_y)) + list(zip(right_x[::-1], right_y[::-1]))

        polygon = Polygon(
            vertices,
            facecolor=color,
            edgecolor=style['border_color'],
            linewidth=style['border_width'] if style['border_color'] else 0,
            alpha=alpha,
        )
        ax.add_patch(polygon)
