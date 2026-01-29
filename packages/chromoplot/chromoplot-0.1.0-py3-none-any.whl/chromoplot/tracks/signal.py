"""Signal/continuous data track."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


class SignalTrack(BaseTrack):
    """
    Continuous signal data visualization.

    For bedGraph, bigWig, or any continuous genomic data.
    Supports various plot types including heatmap-style.

    Parameters
    ----------
    data_source : str or Path
        Path to bedGraph or bigWig file
    label : str, optional
        Track label
    height : float
        Track height
    plot_type : str
        'fill', 'line', 'heatmap', 'points'
    style : dict, optional
        Style overrides
    """

    def __init__(
        self,
        data_source: str | Path,
        label: str | None = None,
        height: float = 1.0,
        plot_type: Literal['fill', 'line', 'heatmap', 'points'] = 'fill',
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.plot_type = plot_type
        self._positions: np.ndarray | None = None
        self._values: np.ndarray | None = None

    def default_style(self) -> dict:
        return {
            'fill_color': '#2ca02c',
            'line_color': '#1a7a1a',
            'fill_alpha': 0.7,
            'line_width': 1.0,
            'cmap': 'viridis',
            'vmin': None,
            'vmax': None,
            'show_zero_line': True,
            'zero_line_color': '#888888',
        }

    def load_data(self, region: Region) -> None:
        """Load signal data."""
        path = Path(self.data_source)

        if path.suffix in ('.bedGraph', '.bedgraph', '.bg'):
            self._load_bedgraph(path, region)
        elif path.suffix in ('.bw', '.bigwig', '.bigWig'):
            self._load_bigwig(path, region)
        else:
            # Try bedGraph format
            self._load_bedgraph(path, region)

        self._loaded_regions.append(region)

    def _load_bedgraph(self, path: Path, region: Region) -> None:
        """Load bedGraph format."""
        positions = []
        values = []

        with open(path) as f:
            for line in f:
                if line.startswith(('#', 'track', 'browser')):
                    continue
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    continue

                chrom, start, end, value = parts[0], int(parts[1]), int(parts[2]), float(parts[3])

                if chrom != region.chrom:
                    continue
                if end <= region.start or start >= region.end:
                    continue

                positions.append((start + end) / 2)
                values.append(value)

        self._positions = np.array(positions)
        self._values = np.array(values)

    def _load_bigwig(self, path: Path, region: Region) -> None:
        """Load bigWig format."""
        try:
            import pyBigWig
        except ImportError:
            raise ImportError("pyBigWig required")

        bw = pyBigWig.open(str(path))
        values = bw.values(region.chrom, region.start, region.end)
        bw.close()

        if values:
            self._positions = np.arange(region.start, region.end)
            self._values = np.nan_to_num(np.array(values), nan=0.0)
        else:
            self._positions = np.array([])
            self._values = np.array([])

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render signal track."""
        style = self.style

        if self._positions is None or len(self._positions) == 0:
            ax.set_xlim(regions[0].start, regions[0].end)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            return

        vmin = style['vmin'] if style['vmin'] is not None else np.min(self._values)
        vmax = style['vmax'] if style['vmax'] is not None else np.max(self._values)

        if self.plot_type == 'heatmap':
            # Render as 1D heatmap
            extent = [regions[0].start, regions[0].end, 0, 1]
            values_2d = self._values.reshape(1, -1)
            ax.imshow(
                values_2d,
                aspect='auto',
                extent=extent,
                cmap=style['cmap'],
                vmin=vmin,
                vmax=vmax,
            )

        elif self.plot_type == 'fill':
            # Normalize values
            values_norm = (self._values - vmin) / (vmax - vmin + 1e-10)
            values_norm = np.clip(values_norm, 0, 1)

            ax.fill_between(
                self._positions,
                0,
                values_norm,
                color=style['fill_color'],
                alpha=style['fill_alpha'],
            )

        elif self.plot_type == 'line':
            values_norm = (self._values - vmin) / (vmax - vmin + 1e-10)
            ax.plot(
                self._positions,
                values_norm,
                color=style['line_color'],
                linewidth=style['line_width'],
            )

        elif self.plot_type == 'points':
            values_norm = (self._values - vmin) / (vmax - vmin + 1e-10)
            ax.scatter(
                self._positions,
                values_norm,
                c=style['fill_color'],
                s=2,
                alpha=style['fill_alpha'],
            )

        ax.set_xlim(regions[0].start, regions[0].end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])

    def clear_data(self) -> None:
        """Clear cached data."""
        super().clear_data()
        self._positions = None
        self._values = None
