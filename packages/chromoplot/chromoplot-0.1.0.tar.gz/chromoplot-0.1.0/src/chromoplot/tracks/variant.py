"""Variant visualization track for VCF files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


class VariantTrack(BaseTrack):
    """
    Variant visualization from VCF files.

    Displays variants as ticks, lollipops, or density plot.

    Parameters
    ----------
    data_source : str or Path
        Path to VCF file
    label : str, optional
        Track label
    height : float
        Track height
    plot_type : str
        'ticks', 'lollipop', 'density'
    style : dict, optional
        Style overrides
    """

    def __init__(
        self,
        data_source: str | Path,
        label: str | None = None,
        height: float = 0.5,
        plot_type: Literal['ticks', 'lollipop', 'density'] = 'ticks',
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.plot_type = plot_type
        self._positions: list[int] = []
        self._variant_types: list[str] = []

    def default_style(self) -> dict:
        return {
            'snp_color': '#2171b5',
            'indel_color': '#cb181d',
            'other_color': '#666666',
            'tick_height': 0.8,
            'tick_width': 1,
            'lollipop_size': 10,
            'density_bins': 100,
            'density_color': '#2171b5',
            'alpha': 0.7,
        }

    def load_data(self, region: Region) -> None:
        """Load variant positions from VCF."""
        import gzip

        path = Path(self.data_source)
        opener = gzip.open if str(path).endswith('.gz') else open

        with opener(path, 'rt') as f:
            for line in f:
                if line.startswith('#'):
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 5:
                    continue

                chrom = parts[0]
                pos = int(parts[1]) - 1  # Convert to 0-based
                ref = parts[3]
                alt = parts[4]

                if chrom != region.chrom:
                    continue
                if pos < region.start or pos >= region.end:
                    continue

                # Determine variant type
                if len(ref) == 1 and len(alt) == 1:
                    var_type = 'snp'
                elif len(ref) != len(alt):
                    var_type = 'indel'
                else:
                    var_type = 'other'

                self._positions.append(pos)
                self._variant_types.append(var_type)

        self._loaded_regions.append(region)

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render variants."""
        style = self.style
        region = regions[0]

        if not self._positions:
            ax.set_xlim(region.start, region.end)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            return

        if self.plot_type == 'density':
            self._render_density(ax, region)
        elif self.plot_type == 'lollipop':
            self._render_lollipop(ax, region)
        else:  # ticks
            self._render_ticks(ax, region)

        ax.set_xlim(region.start, region.end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])

    def _render_ticks(self, ax: plt.Axes, region: Region) -> None:
        """Render variants as vertical ticks."""
        style = self.style

        for pos, var_type in zip(self._positions, self._variant_types):
            color = {
                'snp': style['snp_color'],
                'indel': style['indel_color'],
                'other': style['other_color'],
            }.get(var_type, style['other_color'])

            ax.axvline(
                x=pos,
                ymin=0.5 - style['tick_height'] / 2,
                ymax=0.5 + style['tick_height'] / 2,
                color=color,
                linewidth=style['tick_width'],
                alpha=style['alpha'],
            )

    def _render_lollipop(self, ax: plt.Axes, region: Region) -> None:
        """Render variants as lollipops."""
        style = self.style

        for pos, var_type in zip(self._positions, self._variant_types):
            color = {
                'snp': style['snp_color'],
                'indel': style['indel_color'],
                'other': style['other_color'],
            }.get(var_type, style['other_color'])

            # Stem
            ax.plot(
                [pos, pos],
                [0, 0.7],
                color=color,
                linewidth=0.5,
                alpha=style['alpha'],
            )

            # Head
            ax.scatter(
                [pos],
                [0.7],
                c=color,
                s=style['lollipop_size'],
                alpha=style['alpha'],
                zorder=3,
            )

    def _render_density(self, ax: plt.Axes, region: Region) -> None:
        """Render variant density histogram."""
        style = self.style

        positions = np.array(self._positions)

        bins = np.linspace(region.start, region.end, style['density_bins'] + 1)
        counts, edges = np.histogram(positions, bins=bins)

        # Normalize
        max_count = max(counts) if max(counts) > 0 else 1
        heights = counts / max_count

        centers = (edges[:-1] + edges[1:]) / 2
        width = edges[1] - edges[0]

        ax.bar(
            centers,
            heights,
            width=width,
            color=style['density_color'],
            alpha=style['alpha'],
            edgecolor='none',
        )

    def clear_data(self) -> None:
        """Clear cached data."""
        super().clear_data()
        self._positions = []
        self._variant_types = []
