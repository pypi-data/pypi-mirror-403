"""Coverage/depth visualization track."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


class DepthTrack(BaseTrack):
    """
    Read depth/coverage visualization.

    Displays coverage as a filled area plot or line plot.
    Supports BAM files and pre-computed bedGraph/bigWig.

    Parameters
    ----------
    data_source : str or Path
        Path to BAM, bedGraph, or bigWig file
    label : str, optional
        Track label
    height : float
        Track height (default: 1.0)
    plot_type : str
        Plot type: 'fill', 'line', 'bar'
    bin_size : int
        Bin size for BAM coverage (default: 1000)
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = DepthTrack("reads.bam", label="Coverage")
    >>> track = DepthTrack("coverage.bedGraph", plot_type='line')
    """

    def __init__(
        self,
        data_source: str | Path,
        label: str | None = None,
        height: float = 1.0,
        plot_type: Literal['fill', 'line', 'bar'] = 'fill',
        bin_size: int = 1000,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.plot_type = plot_type
        self.bin_size = bin_size
        self._positions: np.ndarray | None = None
        self._coverage: np.ndarray | None = None

    def default_style(self) -> dict:
        return {
            'fill_color': '#2171b5',
            'line_color': '#08519c',
            'fill_alpha': 0.6,
            'line_width': 1.0,
            'show_baseline': True,
            'baseline_color': '#cccccc',
            'y_max': None,          # Auto-scale if None
            'y_min': 0,
            'log_scale': False,
            'smooth': False,
            'smooth_window': 5,
        }

    def load_data(self, region: Region) -> None:
        """Load coverage data for region."""
        path = Path(self.data_source)

        if path.suffix in ('.bam', '.cram'):
            from ..io.bam import get_coverage
            self._positions, self._coverage = get_coverage(
                path, region, bin_size=self.bin_size
            )
        elif path.suffix in ('.bedGraph', '.bedgraph', '.bg'):
            self._load_bedgraph(path, region)
        elif path.suffix in ('.bw', '.bigwig', '.bigWig'):
            self._load_bigwig(path, region)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        self._loaded_regions.append(region)

    def _load_bedgraph(self, path: Path, region: Region) -> None:
        """Load bedGraph file."""
        positions = []
        values = []

        with open(path) as f:
            for line in f:
                if line.startswith('#') or line.startswith('track'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) < 4:
                    continue

                chrom = parts[0]
                start = int(parts[1])
                end = int(parts[2])
                value = float(parts[3])

                if chrom != region.chrom:
                    continue
                if end <= region.start or start >= region.end:
                    continue

                # Add midpoint
                positions.append((start + end) / 2)
                values.append(value)

        self._positions = np.array(positions)
        self._coverage = np.array(values)

    def _load_bigwig(self, path: Path, region: Region) -> None:
        """Load bigWig file."""
        try:
            import pyBigWig
        except ImportError:
            raise ImportError("pyBigWig required for bigWig support")

        bw = pyBigWig.open(str(path))

        # Get values
        values = bw.values(region.chrom, region.start, region.end)

        if values is None:
            self._positions = np.array([])
            self._coverage = np.array([])
        else:
            self._positions = np.arange(region.start, region.end)
            self._coverage = np.array(values)
            # Handle NaN
            self._coverage = np.nan_to_num(self._coverage, nan=0.0)

        bw.close()

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render coverage plot."""
        style = self.style

        if self._positions is None or len(self._positions) == 0:
            ax.set_xlim(regions[0].start, regions[0].end)
            ax.set_ylim(0, 1)
            return

        positions = self._positions
        coverage = self._coverage.copy()

        # Apply smoothing if requested
        if style['smooth']:
            coverage = self._smooth(coverage, style['smooth_window'])

        # Apply log scale
        if style['log_scale']:
            coverage = np.log10(coverage + 1)

        # Determine y limits
        y_min = style['y_min']
        y_max = style['y_max'] or np.percentile(coverage[coverage > 0], 99) if len(coverage[coverage > 0]) > 0 else 1

        # Normalize to track height
        coverage_norm = (coverage - y_min) / (y_max - y_min)
        coverage_norm = np.clip(coverage_norm, 0, 1)

        # Plot based on type
        if self.plot_type == 'fill':
            ax.fill_between(
                positions,
                0,
                coverage_norm,
                color=style['fill_color'],
                alpha=style['fill_alpha'],
                linewidth=0,
            )
            ax.plot(
                positions,
                coverage_norm,
                color=style['line_color'],
                linewidth=style['line_width'] * 0.5,
            )

        elif self.plot_type == 'line':
            ax.plot(
                positions,
                coverage_norm,
                color=style['line_color'],
                linewidth=style['line_width'],
            )

        elif self.plot_type == 'bar':
            ax.bar(
                positions,
                coverage_norm,
                width=positions[1] - positions[0] if len(positions) > 1 else 1,
                color=style['fill_color'],
                alpha=style['fill_alpha'],
                edgecolor='none',
            )

        # Add baseline
        if style['show_baseline']:
            ax.axhline(
                y=0,
                color=style['baseline_color'],
                linewidth=0.5,
            )

        # Set limits
        ax.set_xlim(regions[0].start, regions[0].end)
        ax.set_ylim(0, 1.05)

        # Add y-axis label with scale
        if self.label:
            ax.set_ylabel(
                f"{self.label}\n(0-{y_max:.0f})",
                fontsize=8,
            )

    def _smooth(self, data: np.ndarray, window: int) -> np.ndarray:
        """Apply moving average smoothing."""
        if len(data) < window:
            return data
        return np.convolve(data, np.ones(window) / window, mode='same')

    def clear_data(self) -> None:
        """Clear cached data."""
        super().clear_data()
        self._positions = None
        self._coverage = None
