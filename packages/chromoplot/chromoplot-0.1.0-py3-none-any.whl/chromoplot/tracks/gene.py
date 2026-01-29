"""Gene model visualization track."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

from .base import BaseTrack
from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region
from ..io.gff import read_genes, Gene


class GeneTrack(BaseTrack):
    """
    Gene model visualization with exon/intron structure.

    Displays genes with UTRs, exons, introns, and directional arrows.
    Supports various display modes from simple boxes to detailed
    transcript structures.

    Parameters
    ----------
    data_source : str or Path
        Path to GFF3/GTF file
    label : str, optional
        Track label
    height : float
        Track height (default: 1.5)
    mode : str
        Display mode: 'collapsed', 'squish', 'pack', 'full'
    style : dict, optional
        Style overrides

    Examples
    --------
    >>> track = GeneTrack("genes.gff3")
    >>> track = GeneTrack("genes.gff3", mode='collapsed')
    >>> track = GeneTrack("genes.gff3", style={'exon_color': 'navy'})
    """

    def __init__(
        self,
        data_source: str | Path,
        label: str | None = None,
        height: float = 1.5,
        mode: Literal['collapsed', 'squish', 'pack', 'full'] = 'squish',
        style: dict | None = None,
    ):
        super().__init__(
            data_source=data_source,
            label=label,
            height=height,
            style=style,
        )
        self.mode = mode
        self._genes: list[Gene] = []

    def default_style(self) -> dict:
        return {
            # Colors
            'exon_color': '#2c5aa0',
            'cds_color': '#1a3a6e',
            'utr_color': '#7ba3d8',
            'intron_color': '#666666',

            # Dimensions
            'exon_height': 0.8,
            'cds_height': 0.8,
            'utr_height': 0.5,
            'intron_height': 0.1,

            # Intron style
            'intron_style': 'line',      # 'line', 'hat', 'arrow'

            # Labels
            'show_labels': True,
            'label_fontsize': 7,
            'label_position': 'top',     # 'top', 'inside', 'none'

            # Direction
            'show_direction': True,
            'direction_style': 'arrow',  # 'arrow', 'chevron'

            # Stacking
            'gene_spacing': 0.1,
            'max_rows': 10,
        }

    def load_data(self, region: Region) -> None:
        """Load gene data for region."""
        genes = read_genes(self.data_source, region=region)
        self._genes.extend(genes)
        self._loaded_regions.append(region)

    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """Render gene models."""
        if not self._genes:
            ax.set_xlim(regions[0].start, regions[0].end)
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            return

        style = self.style

        # Calculate row assignments to avoid overlap
        if self.mode == 'collapsed':
            row_assignments = [0] * len(self._genes)
            n_rows = 1
        else:
            row_assignments, n_rows = self._calculate_rows(self._genes)

        n_rows = min(n_rows, style['max_rows'])
        row_height = 1.0 / n_rows

        # Render each gene
        for gene, row in zip(self._genes, row_assignments):
            if row >= style['max_rows']:
                continue

            y_base = 1.0 - (row + 1) * row_height + style['gene_spacing'] / 2
            gene_height = row_height - style['gene_spacing']

            self._render_gene(ax, gene, y_base, gene_height)

        # Set axis limits
        ax.set_xlim(regions[0].start, regions[0].end)
        ax.set_ylim(0, 1)
        ax.set_yticks([])

    def _calculate_rows(self, genes: list[Gene]) -> tuple[list[int], int]:
        """Calculate row assignments to avoid overlapping genes."""
        # Sort by start position
        sorted_genes = sorted(enumerate(genes), key=lambda x: x[1].start)

        row_assignments = [0] * len(genes)
        row_ends = []  # Track end position of each row

        for orig_idx, gene in sorted_genes:
            # Find first row where gene fits
            assigned = False
            for row_idx, row_end in enumerate(row_ends):
                if gene.start >= row_end:
                    row_assignments[orig_idx] = row_idx
                    row_ends[row_idx] = gene.end
                    assigned = True
                    break

            if not assigned:
                # Need new row
                row_assignments[orig_idx] = len(row_ends)
                row_ends.append(gene.end)

        return row_assignments, len(row_ends)

    def _render_gene(
        self,
        ax: plt.Axes,
        gene: Gene,
        y_base: float,
        height: float
    ) -> None:
        """Render a single gene."""
        style = self.style
        y_center = y_base + height / 2

        # If no transcripts, render as simple box
        if not gene.transcripts:
            self._render_simple_gene(ax, gene, y_base, height)
            return

        # Use first transcript for now (could show all in 'full' mode)
        transcript = gene.transcripts[0]

        # Sort exons and CDS
        exons = sorted(transcript.exons, key=lambda x: x[0])
        cds_regions = sorted(transcript.cds, key=lambda x: x[0]) if transcript.cds else []

        # Draw intron line first (background)
        if len(exons) > 1:
            intron_y = y_center
            ax.plot(
                [gene.start, gene.end],
                [intron_y, intron_y],
                color=style['intron_color'],
                linewidth=1,
                zorder=1,
            )

            # Draw intron connectors (hat style)
            if style['intron_style'] == 'hat':
                for i in range(len(exons) - 1):
                    intron_start = exons[i][1]
                    intron_end = exons[i + 1][0]
                    mid = (intron_start + intron_end) / 2
                    hat_height = height * 0.15

                    ax.plot(
                        [intron_start, mid, intron_end],
                        [intron_y, intron_y + hat_height, intron_y],
                        color=style['intron_color'],
                        linewidth=1,
                        zorder=1,
                    )

        # Draw exons
        exon_height = height * style['exon_height']
        exon_y = y_center - exon_height / 2

        for exon_start, exon_end in exons:
            # Check if this exon overlaps with CDS
            is_coding = any(
                cds_start < exon_end and cds_end > exon_start
                for cds_start, cds_end in cds_regions
            )

            if is_coding and cds_regions:
                # Draw UTR and CDS separately
                self._render_exon_with_cds(
                    ax, exon_start, exon_end, cds_regions,
                    exon_y, exon_height, y_center, height
                )
            else:
                # Draw as UTR (non-coding exon)
                utr_height = height * style['utr_height']
                utr_y = y_center - utr_height / 2
                rect = mpatches.Rectangle(
                    (exon_start, utr_y),
                    exon_end - exon_start,
                    utr_height,
                    facecolor=style['utr_color'],
                    edgecolor='none',
                    zorder=2,
                )
                ax.add_patch(rect)

        # Draw direction arrow
        if style['show_direction']:
            self._render_direction(ax, gene, y_center, height)

        # Draw label
        if style['show_labels'] and gene.name:
            self._render_label(ax, gene, y_base, height)

    def _render_exon_with_cds(
        self,
        ax: plt.Axes,
        exon_start: int,
        exon_end: int,
        cds_regions: list[tuple[int, int]],
        exon_y: float,
        exon_height: float,
        y_center: float,
        total_height: float,
    ) -> None:
        """Render exon with CDS and UTR regions."""
        style = self.style

        # Find CDS overlap
        for cds_start, cds_end in cds_regions:
            if cds_start >= exon_end or cds_end <= exon_start:
                continue

            # CDS portion
            overlap_start = max(exon_start, cds_start)
            overlap_end = min(exon_end, cds_end)

            cds_height = total_height * style['cds_height']
            cds_y = y_center - cds_height / 2

            rect = mpatches.Rectangle(
                (overlap_start, cds_y),
                overlap_end - overlap_start,
                cds_height,
                facecolor=style['cds_color'],
                edgecolor='none',
                zorder=3,
            )
            ax.add_patch(rect)

            # 5' UTR
            if exon_start < cds_start:
                utr_height = total_height * style['utr_height']
                utr_y = y_center - utr_height / 2
                rect = mpatches.Rectangle(
                    (exon_start, utr_y),
                    cds_start - exon_start,
                    utr_height,
                    facecolor=style['utr_color'],
                    edgecolor='none',
                    zorder=2,
                )
                ax.add_patch(rect)

            # 3' UTR
            if exon_end > cds_end:
                utr_height = total_height * style['utr_height']
                utr_y = y_center - utr_height / 2
                rect = mpatches.Rectangle(
                    (cds_end, utr_y),
                    exon_end - cds_end,
                    utr_height,
                    facecolor=style['utr_color'],
                    edgecolor='none',
                    zorder=2,
                )
                ax.add_patch(rect)

    def _render_simple_gene(
        self,
        ax: plt.Axes,
        gene: Gene,
        y_base: float,
        height: float
    ) -> None:
        """Render gene as simple rectangle."""
        style = self.style

        rect_height = height * style['exon_height']
        rect_y = y_base + (height - rect_height) / 2

        rect = mpatches.Rectangle(
            (gene.start, rect_y),
            gene.end - gene.start,
            rect_height,
            facecolor=style['exon_color'],
            edgecolor='none',
        )
        ax.add_patch(rect)

        if style['show_labels'] and gene.name:
            self._render_label(ax, gene, y_base, height)

    def _render_direction(
        self,
        ax: plt.Axes,
        gene: Gene,
        y_center: float,
        height: float
    ) -> None:
        """Render strand direction indicator."""
        style = self.style

        arrow_size = min((gene.end - gene.start) * 0.1, height * 0.3)

        if gene.strand == '+':
            arrow_x = gene.end - arrow_size
            dx = arrow_size
        else:
            arrow_x = gene.start + arrow_size
            dx = -arrow_size

        ax.annotate(
            '',
            xy=(arrow_x + dx, y_center),
            xytext=(arrow_x, y_center),
            arrowprops=dict(
                arrowstyle='->',
                color=style['cds_color'],
                lw=1.5,
            ),
            zorder=4,
        )

    def _render_label(
        self,
        ax: plt.Axes,
        gene: Gene,
        y_base: float,
        height: float
    ) -> None:
        """Render gene label."""
        style = self.style

        label_x = (gene.start + gene.end) / 2

        if style['label_position'] == 'top':
            label_y = y_base + height + 0.02
            va = 'bottom'
        elif style['label_position'] == 'inside':
            label_y = y_base + height / 2
            va = 'center'
        else:
            return

        ax.text(
            label_x,
            label_y,
            gene.name,
            ha='center',
            va=va,
            fontsize=style['label_fontsize'],
            style='italic',
        )

    def clear_data(self) -> None:
        """Clear cached data."""
        super().clear_data()
        self._genes = []
