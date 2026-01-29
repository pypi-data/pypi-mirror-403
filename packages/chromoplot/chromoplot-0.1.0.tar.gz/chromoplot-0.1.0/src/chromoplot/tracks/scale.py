"""Scale bar track for genomic reference."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


class ScaleBarTrack(BaseTrack):
    """
    Scale bar for genomic coordinates.

    Displays a scale bar indicating genomic distance.

    Parameters
    ----------
    length : int, optional
        Scale bar length in bp (auto-calculated if None)
    position : str
        Position: 'left', 'center', 'right'
    label : str, optional
        Custom label (auto-generated if None)
    height : float
        Track height
    style : dict, optional
        Style overrides
    """

    def __init__(
        self,
        length: int | None = None,
        position: str = 'right',
        label: str | None = None,
        height: float = 0.3,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=None,
            label=None,  # Use custom label handling
            height=height,
            style=style,
        )
        self.bar_length = length
        self.position = position
        self.custom_label = label

    def default_style(self) -> dict:
        return {
            'bar_color': '#333333',
            'bar_height': 0.3,
            'bar_linewidth': 2,
            'label_fontsize': 9,
            'label_offset': 0.1,
            'show_ticks': True,
            'tick_height': 0.2,
        }

    def load_data(self, region: Region) -> None:
        """Calculate scale bar length if not specified."""
        if self.bar_length is None:
            # Choose nice round number based on region size
            region_size = len(region)
            nice_lengths = [
                1000, 5000, 10000, 50000, 100000, 500000,
                1000000, 5000000, 10000000, 50000000, 100000000
            ]
            # Pick length that's about 10-20% of region
            target = region_size * 0.15
            self.bar_length = min(nice_lengths, key=lambda x: abs(x - target))

        self._loaded_regions.append(region)

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render scale bar."""
        style = self.style
        region = regions[0]

        # Calculate position
        if self.position == 'left':
            bar_start = region.start + len(region) * 0.05
        elif self.position == 'center':
            bar_start = region.start + (len(region) - self.bar_length) / 2
        else:  # right
            bar_start = region.end - len(region) * 0.05 - self.bar_length

        bar_end = bar_start + self.bar_length
        y_center = 0.5

        # Draw main bar
        ax.plot(
            [bar_start, bar_end],
            [y_center, y_center],
            color=style['bar_color'],
            linewidth=style['bar_linewidth'],
            solid_capstyle='butt',
        )

        # Draw end ticks
        if style['show_ticks']:
            tick_y_bottom = y_center - style['tick_height'] / 2
            tick_y_top = y_center + style['tick_height'] / 2

            ax.plot(
                [bar_start, bar_start],
                [tick_y_bottom, tick_y_top],
                color=style['bar_color'],
                linewidth=style['bar_linewidth'],
            )
            ax.plot(
                [bar_end, bar_end],
                [tick_y_bottom, tick_y_top],
                color=style['bar_color'],
                linewidth=style['bar_linewidth'],
            )

        # Add label
        label = self.custom_label or self._format_length(self.bar_length)
        ax.text(
            (bar_start + bar_end) / 2,
            y_center + style['label_offset'],
            label,
            ha='center',
            va='bottom',
            fontsize=style['label_fontsize'],
            fontweight='bold',
        )

        # Set axis limits and clean up
        ax.set_xlim(region.start, region.end)
        ax.set_ylim(0, 1)
        ax.axis('off')

    def _format_length(self, length: int) -> str:
        """Format length as human-readable string."""
        if length >= 1000000:
            return f"{length / 1000000:.0f} Mb"
        elif length >= 1000:
            return f"{length / 1000:.0f} kb"
        else:
            return f"{length} bp"
