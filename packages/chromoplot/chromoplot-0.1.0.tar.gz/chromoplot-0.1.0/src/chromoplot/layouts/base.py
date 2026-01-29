"""Base layout class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from ..core.coordinates import GenomeCoordinates
    from ..core.regions import Region


class BaseLayout(ABC):
    """
    Abstract base class for layout managers.

    Layouts control how multiple regions/chromosomes are arranged
    in the figure space.
    """

    @abstractmethod
    def setup_axes(
        self,
        fig: plt.Figure,
        regions: list[Region],
        n_tracks: int,
    ) -> list[list[plt.Axes]]:
        """
        Create and arrange axes for the figure.

        Parameters
        ----------
        fig : matplotlib.Figure
            Figure to add axes to
        regions : list[Region]
            Regions to display
        n_tracks : int
            Number of tracks

        Returns
        -------
        list[list[Axes]]
            2D list of axes [track_idx][region_idx]
        """
        pass

    @abstractmethod
    def transform_position(
        self,
        chrom: str,
        pos: int,
        coordinates: GenomeCoordinates,
    ) -> float:
        """
        Transform genomic position to figure coordinate.

        Parameters
        ----------
        chrom : str
            Chromosome name
        pos : int
            Position on chromosome
        coordinates : GenomeCoordinates
            Genome coordinates

        Returns
        -------
        float
            Figure x-coordinate
        """
        pass
