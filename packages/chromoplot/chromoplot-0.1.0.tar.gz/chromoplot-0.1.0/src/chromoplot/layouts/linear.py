"""Linear layout for single region visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from .base import BaseLayout

if TYPE_CHECKING:
    from ..core.coordinates import GenomeCoordinates
    from ..core.regions import Region


class LinearLayout(BaseLayout):
    """
    Simple linear layout for a single region.

    All tracks are stacked vertically with the same x-axis range.
    """

    def __init__(
        self,
        height_ratios: list[float] | None = None,
        spacing: float = 0.1,
    ):
        """
        Initialize linear layout.

        Parameters
        ----------
        height_ratios : list[float], optional
            Relative heights for each track
        spacing : float
            Vertical spacing between tracks
        """
        self.height_ratios = height_ratios
        self.spacing = spacing

    def setup_axes(
        self,
        fig: plt.Figure,
        regions: list[Region],
        n_tracks: int,
    ) -> list[list[plt.Axes]]:
        """Create stacked axes for single region."""
        if len(regions) != 1:
            raise ValueError("LinearLayout only supports a single region")

        height_ratios = self.height_ratios or [1.0] * n_tracks

        axes = fig.subplots(
            nrows=n_tracks,
            ncols=1,
            gridspec_kw={
                'height_ratios': height_ratios,
                'hspace': self.spacing,
            },
            squeeze=False,
        )

        # Return as 2D list [track][region]
        return [[ax[0]] for ax in axes]

    def transform_position(
        self,
        chrom: str,
        pos: int,
        coordinates: GenomeCoordinates,
    ) -> float:
        """Identity transform for linear layout."""
        return float(pos)
