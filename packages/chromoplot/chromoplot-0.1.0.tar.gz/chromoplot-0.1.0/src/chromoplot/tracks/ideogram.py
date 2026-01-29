"""Chromosome ideogram track."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


class IdeogramTrack(BaseTrack):
    """
    Chromosome ideogram/backbone visualization.

    Displays chromosome as a rounded rectangle with optional
    cytoband coloring and centromere indication.

    Parameters
    ----------
    cytobands : str or Path, optional
        Path to cytoband file (UCSC format)
    label : str, optional
        Track label
    height : float
        Track height (default: 0.5)
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = IdeogramTrack()
    >>> track = IdeogramTrack(cytobands="cytoBand.txt")
    >>> track = IdeogramTrack(style={'backbone_color': 'lightblue'})
    """

    def __init__(
        self,
        cytobands: str | Path | None = None,
        label: str | None = None,
        height: float = 0.5,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=cytobands,
            label=label,
            height=height,
            style=style,
        )
        self._cytobands: list[dict] | None = None

    def default_style(self) -> dict:
        return {
            'backbone_color': '#e0e0e0',
            'backbone_edgecolor': '#999999',
            'backbone_linewidth': 0.5,
            'backbone_height': 0.6,        # Fraction of track height
            'corner_radius': 0.02,          # Fraction of region length
            'centromere_color': '#c0c0c0',
            'centromere_width': 0.01,       # Fraction of region length
            'show_labels': False,
            'label_fontsize': 8,
        }

    def load_data(self, region: Region) -> None:
        """Load cytoband data if provided."""
        if self.data_source is not None and self._cytobands is None:
            self._cytobands = self._parse_cytobands(self.data_source)
        self._loaded_regions.append(region)

    def _parse_cytobands(self, path: Path) -> list[dict]:
        """Parse UCSC cytoband file."""
        cytobands = []
        with open(path) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    cytobands.append({
                        'chrom': parts[0],
                        'start': int(parts[1]),
                        'end': int(parts[2]),
                        'name': parts[3],
                        'stain': parts[4] if len(parts) > 4 else 'gneg',
                    })
        return cytobands

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render ideogram."""
        for region in regions:
            self._render_region(ax, region)

        # Set axis limits
        if len(regions) == 1:
            region = regions[0]
            ax.set_xlim(region.start, region.end)

        # Clean up axes
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.axis('off')

    def _render_region(self, ax: plt.Axes, region: Region) -> None:
        """Render ideogram for a single region."""
        style = self.style

        # Calculate dimensions
        y_center = 0.5
        height = style['backbone_height']
        y_bottom = y_center - height / 2

        # Draw backbone as rounded rectangle
        from matplotlib.patches import FancyBboxPatch

        bbox = FancyBboxPatch(
            (region.start, y_bottom),
            len(region),
            height,
            boxstyle=f"round,pad=0,rounding_size={len(region) * style['corner_radius']}",
            facecolor=style['backbone_color'],
            edgecolor=style['backbone_edgecolor'],
            linewidth=style['backbone_linewidth'],
        )
        ax.add_patch(bbox)

        # Draw cytobands if available
        if self._cytobands:
            self._render_cytobands(ax, region, y_bottom, height)

        # Add label if requested
        if style['show_labels']:
            ax.text(
                region.start + len(region) / 2,
                y_center,
                region.chrom,
                ha='center',
                va='center',
                fontsize=style['label_fontsize'],
            )

    def _render_cytobands(
        self,
        ax: plt.Axes,
        region: Region,
        y_bottom: float,
        height: float
    ) -> None:
        """Render cytoband coloring."""
        # Cytoband color mapping
        stain_colors = {
            'gneg': '#ffffff',
            'gpos25': '#c0c0c0',
            'gpos50': '#808080',
            'gpos75': '#404040',
            'gpos100': '#000000',
            'acen': '#cc4444',      # Centromere
            'gvar': '#e0e0e0',
            'stalk': '#4444cc',
        }

        for band in self._cytobands:
            if band['chrom'] != region.chrom:
                continue

            # Check overlap with region
            band_start = max(band['start'], region.start)
            band_end = min(band['end'], region.end)

            if band_start >= band_end:
                continue

            color = stain_colors.get(band['stain'], '#e0e0e0')

            rect = mpatches.Rectangle(
                (band_start, y_bottom),
                band_end - band_start,
                height,
                facecolor=color,
                edgecolor='none',
            )
            ax.add_patch(rect)
