"""Haplotype block visualization track (designed for phaser output)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region
from ..io.bed import read_bed_to_dataframe
from ..themes.colors import founder_colors


class HaplotypeTrack(BaseTrack):
    """
    Haplotype block visualization.

    Designed to display phaser output showing founder/subgenome
    assignments along chromosomes. Each block is colored by its
    assigned founder.

    Parameters
    ----------
    data_source : str or Path
        Path to BED file with haplotype blocks.
        Name column should contain founder/haplotype identifier.
    founders : list[str], optional
        Founder names for consistent coloring and legend
    label : str, optional
        Track label
    height : float
        Track height (default: 1.0)
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = HaplotypeTrack("haplotypes.bed")
    >>> track = HaplotypeTrack("haplotypes.bed", founders=["B73", "Mo17"])
    """

    def __init__(
        self,
        data_source: str | Path,
        founders: list[str] | None = None,
        label: str | None = None,
        height: float = 1.0,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.founders = founders
        self._color_map: dict[str, str] | None = None

    def default_style(self) -> dict:
        return {
            'block_height': 0.8,
            'block_alpha': 0.9,
            'show_boundaries': True,
            'boundary_color': 'white',
            'boundary_width': 0.5,
            'uncertain_color': '#cccccc',
            'uncertain_pattern': 'hatch',
            'show_legend': True,
            'legend_loc': 'upper right',
        }

    def load_data(self, region: Region) -> None:
        """Load haplotype block data."""
        df = read_bed_to_dataframe(self.data_source, region=region)

        if self._data is None:
            self._data = df
        else:
            import pandas as pd
            self._data = pd.concat([self._data, df], ignore_index=True)

        self._loaded_regions.append(region)

        # Build color map
        if self._color_map is None:
            self._build_color_map()

    def _build_color_map(self) -> None:
        """Build founder to color mapping."""
        if self.founders:
            self._color_map = founder_colors(self.founders)
        elif self._data is not None and 'name' in self._data.columns:
            unique_founders = self._data['name'].dropna().unique().tolist()
            self._color_map = founder_colors(unique_founders)
        else:
            self._color_map = {}

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render haplotype blocks."""
        if self._data is None or len(self._data) == 0:
            ax.set_xlim(regions[0].start, regions[0].end)
            ax.set_ylim(0, 1)
            return

        style = self.style

        # Calculate dimensions
        y_center = 0.5
        block_height = style['block_height']
        y_bottom = y_center - block_height / 2

        # Render each block
        legend_handles = {}

        for _, row in self._data.iterrows():
            founder = row.get('name', 'unknown')
            color = self._color_map.get(founder, style['uncertain_color'])

            # Create block
            rect = mpatches.Rectangle(
                (row['start'], y_bottom),
                row['end'] - row['start'],
                block_height,
                facecolor=color,
                edgecolor=style['boundary_color'] if style['show_boundaries'] else 'none',
                linewidth=style['boundary_width'],
                alpha=style['block_alpha'],
            )
            ax.add_patch(rect)

            # Track for legend
            if founder not in legend_handles and founder != 'unknown':
                legend_handles[founder] = mpatches.Patch(
                    facecolor=color,
                    edgecolor='none',
                    label=founder,
                )

        # Add legend
        if style['show_legend'] and legend_handles:
            ax.legend(
                handles=list(legend_handles.values()),
                loc=style['legend_loc'],
                fontsize=8,
                framealpha=0.9,
            )

        # Set axis limits
        ax.set_xlim(regions[0].start, regions[0].end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
