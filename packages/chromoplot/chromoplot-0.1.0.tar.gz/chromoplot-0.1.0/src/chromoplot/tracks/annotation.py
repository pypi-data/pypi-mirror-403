"""Text annotation track for labels and markers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


@dataclass
class Annotation:
    """Single annotation."""
    chrom: str
    position: int
    label: str
    color: str | None = None
    marker: str | None = None


class AnnotationTrack(BaseTrack):
    """
    Text annotation and marker track.

    Displays text labels, markers, or both at specific
    genomic positions.

    Parameters
    ----------
    data_source : str, Path, or list
        Path to annotation file or list of Annotation objects
    label : str, optional
        Track label
    height : float
        Track height
    style : dict, optional
        Style overrides
    """

    def __init__(
        self,
        data_source: str | Path | list[Annotation],
        label: str | None = None,
        height: float = 0.5,
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self._annotations: list[Annotation] = []

    def default_style(self) -> dict:
        return {
            'text_color': '#333333',
            'text_fontsize': 8,
            'text_rotation': 45,
            'text_ha': 'left',
            'marker': 'v',
            'marker_size': 50,
            'marker_color': '#e41a1c',
            'show_line': True,
            'line_color': '#999999',
            'line_style': '--',
            'line_width': 0.5,
        }

    def load_data(self, region: Region) -> None:
        """Load annotation data."""
        if isinstance(self.data_source, list):
            self._annotations = [
                a for a in self.data_source
                if a.chrom == region.chrom and region.start <= a.position < region.end
            ]
        else:
            self._load_from_file(region)

        self._loaded_regions.append(region)

    def _load_from_file(self, region: Region) -> None:
        """Load annotations from file."""
        with open(self.data_source) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) < 3:
                    continue

                chrom = parts[0]
                pos = int(parts[1])
                label = parts[2]

                if chrom != region.chrom:
                    continue
                if pos < region.start or pos >= region.end:
                    continue

                color = parts[3] if len(parts) > 3 else None

                self._annotations.append(Annotation(
                    chrom=chrom,
                    position=pos,
                    label=label,
                    color=color,
                ))

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render annotations."""
        style = self.style
        region = regions[0]

        for annot in self._annotations:
            color = annot.color or style['marker_color']

            # Draw marker
            ax.scatter(
                [annot.position],
                [0.3],
                marker=style['marker'],
                s=style['marker_size'],
                c=color,
                zorder=3,
            )

            # Draw vertical line
            if style['show_line']:
                ax.axvline(
                    x=annot.position,
                    color=style['line_color'],
                    linestyle=style['line_style'],
                    linewidth=style['line_width'],
                    zorder=1,
                )

            # Draw label
            ax.text(
                annot.position,
                0.5,
                annot.label,
                color=annot.color or style['text_color'],
                fontsize=style['text_fontsize'],
                rotation=style['text_rotation'],
                ha=style['text_ha'],
                va='bottom',
            )

        ax.set_xlim(region.start, region.end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.axis('off')
