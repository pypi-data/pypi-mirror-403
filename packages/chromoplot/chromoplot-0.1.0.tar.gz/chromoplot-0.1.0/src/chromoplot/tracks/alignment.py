"""Alignment visualization track for PAF files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region
from ..io.paf import read_paf, PAFRecord


class AlignmentTrack(BaseTrack):
    """
    Alignment visualization from PAF files.

    Displays sequence alignments (e.g., contigs to reference) as colored
    blocks. Color indicates identity or strand, height indicates mapping
    quality.

    Parameters
    ----------
    data_source : str or Path
        Path to PAF file
    label : str, optional
        Track label
    height : float
        Track height (default: 1.5)
    color_by : str
        Color by: 'identity', 'strand', 'query', 'mapq'
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = AlignmentTrack("alignments.paf")
    >>> track = AlignmentTrack("alignments.paf", color_by='identity')
    >>> track = AlignmentTrack("alignments.paf", color_by='strand')
    """

    def __init__(
        self,
        data_source: str | Path,
        label: str | None = None,
        height: float = 1.5,
        color_by: Literal['identity', 'strand', 'query', 'mapq'] = 'identity',
        min_length: int = 1000,
        min_mapq: int = 0,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.color_by = color_by
        self.min_length = min_length
        self.min_mapq = min_mapq
        self._alignments: list[PAFRecord] = []

    def default_style(self) -> dict:
        return {
            # Colors
            'forward_color': '#2166ac',
            'reverse_color': '#b2182b',
            'identity_cmap': 'RdYlGn',
            'identity_min': 0.8,
            'identity_max': 1.0,

            # Dimensions
            'block_height': 0.7,
            'block_alpha': 0.8,
            'min_block_width': 2,       # Minimum width in pixels

            # Borders
            'border_color': 'white',
            'border_width': 0.5,

            # Stacking
            'stack_overlaps': True,
            'max_rows': 20,

            # Labels
            'show_labels': False,
            'label_fontsize': 6,
            'label_min_width': 50000,   # Min alignment length to show label
        }

    def load_data(self, region: Region) -> None:
        """Load alignment data for region."""
        alignments = list(read_paf(
            self.data_source,
            target_region=region,
            min_mapq=self.min_mapq,
            min_length=self.min_length,
        ))
        self._alignments.extend(alignments)
        self._loaded_regions.append(region)

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render alignments."""
        if not self._alignments:
            ax.set_xlim(regions[0].start, regions[0].end)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            return

        style = self.style

        # Calculate row assignments
        if style['stack_overlaps']:
            row_assignments, n_rows = self._calculate_rows()
        else:
            row_assignments = [0] * len(self._alignments)
            n_rows = 1

        n_rows = min(n_rows, style['max_rows'])
        row_height = 1.0 / n_rows

        # Set up colormap for identity coloring
        cmap = None
        norm = None
        if self.color_by == 'identity':
            cmap = plt.get_cmap(style['identity_cmap'])
            norm = mcolors.Normalize(
                vmin=style['identity_min'],
                vmax=style['identity_max']
            )

        # Render each alignment
        for aln, row in zip(self._alignments, row_assignments):
            if row >= style['max_rows']:
                continue

            y_base = 1.0 - (row + 1) * row_height
            block_height = row_height * style['block_height']
            y_center = y_base + row_height / 2
            block_y = y_center - block_height / 2

            # Determine color
            color = self._get_alignment_color(aln, cmap, norm)

            # Draw alignment block
            rect = mpatches.Rectangle(
                (aln.target_start, block_y),
                aln.target_end - aln.target_start,
                block_height,
                facecolor=color,
                edgecolor=style['border_color'],
                linewidth=style['border_width'],
                alpha=style['block_alpha'],
            )
            ax.add_patch(rect)

            # Add label if requested
            if style['show_labels'] and aln.target_span >= style['label_min_width']:
                ax.text(
                    (aln.target_start + aln.target_end) / 2,
                    y_center,
                    aln.query_name,
                    ha='center',
                    va='center',
                    fontsize=style['label_fontsize'],
                    color='white' if self._is_dark(color) else 'black',
                )

        # Add colorbar for identity
        if self.color_by == 'identity':
            self._add_colorbar(ax, cmap, norm)

        # Set axis limits
        ax.set_xlim(regions[0].start, regions[0].end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])

    def _calculate_rows(self) -> tuple[list[int], int]:
        """Calculate row assignments to avoid overlapping alignments."""
        sorted_alns = sorted(
            enumerate(self._alignments),
            key=lambda x: x[1].target_start
        )

        row_assignments = [0] * len(self._alignments)
        row_ends = []

        for orig_idx, aln in sorted_alns:
            assigned = False
            for row_idx, row_end in enumerate(row_ends):
                if aln.target_start >= row_end:
                    row_assignments[orig_idx] = row_idx
                    row_ends[row_idx] = aln.target_end
                    assigned = True
                    break

            if not assigned:
                row_assignments[orig_idx] = len(row_ends)
                row_ends.append(aln.target_end)

        return row_assignments, len(row_ends)

    def _get_alignment_color(
        self,
        aln: PAFRecord,
        cmap,
        norm
    ) -> str:
        """Get color for alignment based on color_by setting."""
        style = self.style

        if self.color_by == 'strand':
            return style['forward_color'] if aln.strand == '+' else style['reverse_color']

        elif self.color_by == 'identity':
            return cmap(norm(aln.identity))

        elif self.color_by == 'mapq':
            # Scale mapq to color intensity
            intensity = min(aln.mapq / 60, 1.0)
            return plt.get_cmap('Blues')(intensity)

        elif self.color_by == 'query':
            # Hash query name to color
            hash_val = hash(aln.query_name) % 10
            palette = plt.get_cmap('tab10')
            return palette(hash_val)

        return style['forward_color']

    def _is_dark(self, color) -> bool:
        """Check if color is dark (for text contrast)."""
        if isinstance(color, str):
            color = mcolors.to_rgb(color)
        luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        return luminance < 0.5

    def _add_colorbar(self, ax: plt.Axes, cmap, norm) -> None:
        """Add colorbar for identity scale."""
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="2%", pad=0.05)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, cax=cax, label='Identity')

    def clear_data(self) -> None:
        """Clear cached data."""
        super().clear_data()
        self._alignments = []
