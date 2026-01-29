"""Generic feature track for BED files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region
from ..io.bed import read_bed_to_dataframe


class FeatureTrack(BaseTrack):
    """
    Generic feature track from BED file.

    Displays genomic features as colored rectangles. Supports
    coloring by column value and stacking of overlapping features.

    Parameters
    ----------
    data_source : str or Path
        Path to BED file
    label : str, optional
        Track label
    height : float
        Track height (default: 1.0)
    color : str, optional
        Feature color (overrides style)
    color_by : str, optional
        Column name to color features by
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = FeatureTrack("features.bed", label="Genes")
    >>> track = FeatureTrack("features.bed", color="steelblue")
    >>> track = FeatureTrack("features.bed", color_by="score")
    """

    def __init__(
        self,
        data_source: str | Path,
        label: str | None = None,
        height: float = 1.0,
        color: str | None = None,
        color_by: str | None = None,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.color = color
        self.color_by = color_by

    def default_style(self) -> dict:
        return {
            'feature_color': '#2c5aa0',
            'feature_height': 0.6,
            'feature_alpha': 0.8,
            'border_color': None,
            'border_width': 0,
            'min_feature_width': 1,     # Minimum width in pixels
            'collapse_overlapping': False,
            'show_labels': False,
            'label_fontsize': 7,
        }

    def load_data(self, region: Region) -> None:
        """Load BED data for region."""
        df = read_bed_to_dataframe(self.data_source, region=region)

        if self._data is None:
            self._data = df
        else:
            import pandas as pd
            self._data = pd.concat([self._data, df], ignore_index=True)

        self._loaded_regions.append(region)

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render features."""
        if self._data is None or len(self._data) == 0:
            ax.set_xlim(regions[0].start, regions[0].end)
            ax.set_ylim(0, 1)
            return

        style = self.style

        # Determine color
        if self.color:
            colors = [self.color] * len(self._data)
        elif self.color_by and self.color_by in self._data.columns:
            colors = self._get_colors_by_column(self._data[self.color_by])
        else:
            colors = [style['feature_color']] * len(self._data)

        # Calculate y positions (stack if needed)
        if style['collapse_overlapping']:
            y_positions = self._calculate_stacked_positions(self._data)
            max_stack = max(y_positions) + 1
        else:
            y_positions = [0] * len(self._data)
            max_stack = 1

        # Render features
        feature_height = style['feature_height'] / max_stack

        for idx, (_, row) in enumerate(self._data.iterrows()):
            y_base = y_positions[idx] * feature_height + (1 - style['feature_height']) / 2

            rect = mpatches.Rectangle(
                (row['start'], y_base),
                row['end'] - row['start'],
                feature_height * 0.9,
                facecolor=colors[idx],
                edgecolor=style['border_color'],
                linewidth=style['border_width'],
                alpha=style['feature_alpha'],
            )
            ax.add_patch(rect)

            # Add label if requested
            if style['show_labels'] and 'name' in row and row['name']:
                ax.text(
                    (row['start'] + row['end']) / 2,
                    y_base + feature_height * 0.45,
                    row['name'],
                    ha='center',
                    va='center',
                    fontsize=style['label_fontsize'],
                )

        # Set axis limits
        ax.set_xlim(regions[0].start, regions[0].end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])

    def _get_colors_by_column(self, values) -> list[str]:
        """Get colors based on column values."""
        from ..themes.colors import get_palette

        unique_values = values.unique()
        palette = get_palette('categorical', n=len(unique_values))
        color_map = dict(zip(unique_values, palette))

        return [color_map[v] for v in values]

    def _calculate_stacked_positions(self, df) -> list[int]:
        """Calculate y positions to avoid overlapping features."""
        positions = []
        ends_by_level = {}  # level -> end position

        for _, row in df.iterrows():
            # Find first level where feature fits
            level = 0
            while level in ends_by_level and ends_by_level[level] > row['start']:
                level += 1

            positions.append(level)
            ends_by_level[level] = row['end']

        return positions
