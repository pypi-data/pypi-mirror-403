"""Base track class defining the track interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from ..core.coordinates import GenomeCoordinates
from ..core.regions import Region


class BaseTrack(ABC):
    """
    Abstract base class for all track types.

    Tracks are the core visualization units in chromoplot. Each track
    represents one type of genomic data and knows how to load and
    render that data.

    Parameters
    ----------
    data_source : str, Path, or object
        Data source (file path, URL, or data object)
    label : str, optional
        Track label shown on y-axis
    height : float
        Relative track height (default: 1.0)
    style : dict, optional
        Style overrides for this track

    Notes
    -----
    Subclasses must implement:
    - `load_data(region)`: Load data for the specified region
    - `render(ax, regions, coordinates)`: Render to matplotlib axes
    - `default_style()`: Return default style parameters
    """

    def __init__(
        self,
        data_source: str | Path | Any | None = None,
        label: str | None = None,
        height: float = 1.0,
        style: dict | None = None,
    ):
        self.data_source = Path(data_source) if isinstance(data_source, str) else data_source
        self.label = label
        self.height = height
        self.style = self._merge_style(style)

        # Data cache (populated by load_data)
        self._data: Any = None
        self._loaded_regions: list[Region] = []

    def _merge_style(self, style: dict | None) -> dict:
        """Merge user style with defaults."""
        defaults = self.default_style()
        if style:
            return {**defaults, **style}
        return defaults

    @abstractmethod
    def default_style(self) -> dict:
        """
        Return default style parameters for this track type.

        Returns
        -------
        dict
            Default style parameters
        """
        pass

    @abstractmethod
    def load_data(self, region: Region) -> None:
        """
        Load data for the specified region.

        Parameters
        ----------
        region : Region
            Genomic region to load
        """
        pass

    @abstractmethod
    def render(
        self,
        ax: plt.Axes,
        regions: list[Region],
        coordinates: GenomeCoordinates,
    ) -> None:
        """
        Render track to matplotlib axes.

        Parameters
        ----------
        ax : matplotlib.Axes
            Axes to render to
        regions : list[Region]
            Regions to display
        coordinates : GenomeCoordinates
            Genome coordinate system
        """
        pass

    def clear_data(self) -> None:
        """Clear cached data."""
        self._data = None
        self._loaded_regions = []

    def get_style(self, key: str, default: Any = None) -> Any:
        """
        Get style parameter.

        Parameters
        ----------
        key : str
            Style parameter name
        default : Any
            Default value if not found

        Returns
        -------
        Any
            Style value
        """
        return self.style.get(key, default)
