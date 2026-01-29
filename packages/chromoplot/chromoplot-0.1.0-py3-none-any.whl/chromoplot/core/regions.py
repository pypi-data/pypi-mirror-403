"""Genomic region specification and parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

from .coordinates import GenomeCoordinates


@dataclass(frozen=True)
class Region:
    """
    Represents a genomic region.

    Parameters
    ----------
    chrom : str
        Chromosome name
    start : int
        Start position (0-based, inclusive)
    end : int
        End position (0-based, exclusive)

    Examples
    --------
    >>> region = Region.parse("chr1:1000000-2000000")
    >>> region
    Region(chrom='chr1', start=1000000, end=2000000)
    >>> len(region)
    1000000
    """

    chrom: str
    start: int
    end: int

    def __post_init__(self):
        """Validate region."""
        if self.start < 0:
            raise ValueError(f"Start position cannot be negative: {self.start}")
        if self.end < self.start:
            raise ValueError(f"End ({self.end}) must be >= start ({self.start})")

    @classmethod
    def parse(cls, region_str: str, coordinates: GenomeCoordinates | None = None) -> Region:
        """
        Parse region from string.

        Supports formats:
        - "chr1" (whole chromosome, requires coordinates)
        - "chr1:1000-2000"
        - "chr1:1,000-2,000" (with commas)
        - "chr1:1000000-2000000"

        Parameters
        ----------
        region_str : str
            Region string
        coordinates : GenomeCoordinates, optional
            Required for whole-chromosome regions

        Returns
        -------
        Region
        """
        # Remove whitespace
        region_str = region_str.strip()

        # Try "chrom:start-end" format
        match = re.match(r'^([^:]+):([0-9,]+)-([0-9,]+)$', region_str)
        if match:
            chrom = match.group(1)
            start = int(match.group(2).replace(',', ''))
            end = int(match.group(3).replace(',', ''))
            return cls(chrom, start, end)

        # Try whole chromosome
        if ':' not in region_str and '-' not in region_str:
            chrom = region_str
            if coordinates is None:
                raise ValueError(
                    f"Coordinates required for whole-chromosome region: {region_str}"
                )
            if chrom not in coordinates.chromosomes:
                raise ValueError(f"Chromosome '{chrom}' not found in coordinates")
            return cls(chrom, 0, coordinates.chromosomes[chrom])

        raise ValueError(f"Cannot parse region: {region_str}")

    @classmethod
    def whole_chromosome(cls, chrom: str, coordinates: GenomeCoordinates) -> Region:
        """
        Create region for entire chromosome.

        Parameters
        ----------
        chrom : str
            Chromosome name
        coordinates : GenomeCoordinates
            Genome coordinates

        Returns
        -------
        Region
        """
        return cls(chrom, 0, coordinates.get_size(chrom))

    @classmethod
    def from_bed_line(cls, line: str) -> Region:
        """
        Create region from BED line.

        Parameters
        ----------
        line : str
            BED format line

        Returns
        -------
        Region
        """
        parts = line.strip().split('\t')
        return cls(parts[0], int(parts[1]), int(parts[2]))

    def __len__(self) -> int:
        """Return region length in base pairs."""
        return self.end - self.start

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.chrom}:{self.start}-{self.end}"

    def __contains__(self, pos: int | tuple[str, int]) -> bool:
        """
        Check if position is within region.

        Parameters
        ----------
        pos : int or tuple
            Position (int) or (chrom, pos) tuple

        Returns
        -------
        bool
        """
        if isinstance(pos, tuple):
            chrom, pos = pos
            if chrom != self.chrom:
                return False
        return self.start <= pos < self.end

    def overlaps(self, other: Region) -> bool:
        """
        Check if this region overlaps another.

        Parameters
        ----------
        other : Region
            Other region

        Returns
        -------
        bool
        """
        if self.chrom != other.chrom:
            return False
        return self.start < other.end and self.end > other.start

    def intersect(self, other: Region) -> Region | None:
        """
        Return intersection with another region.

        Parameters
        ----------
        other : Region
            Other region

        Returns
        -------
        Region or None
            Intersection, or None if no overlap
        """
        if not self.overlaps(other):
            return None
        return Region(
            self.chrom,
            max(self.start, other.start),
            min(self.end, other.end)
        )

    def union(self, other: Region) -> Region:
        """
        Return union with another region (must overlap or be adjacent).

        Parameters
        ----------
        other : Region
            Other region

        Returns
        -------
        Region

        Raises
        ------
        ValueError
            If regions don't overlap and aren't adjacent
        """
        if self.chrom != other.chrom:
            raise ValueError("Cannot union regions on different chromosomes")
        if not (self.overlaps(other) or self.end == other.start or other.end == self.start):
            raise ValueError("Regions must overlap or be adjacent to union")
        return Region(
            self.chrom,
            min(self.start, other.start),
            max(self.end, other.end)
        )

    def expand(self, bp: int) -> Region:
        """
        Expand region by given base pairs on each side.

        Parameters
        ----------
        bp : int
            Base pairs to expand (can be negative to shrink)

        Returns
        -------
        Region
        """
        new_start = max(0, self.start - bp)
        new_end = self.end + bp
        return Region(self.chrom, new_start, new_end)

    def to_bed(self) -> str:
        """Return BED format string."""
        return f"{self.chrom}\t{self.start}\t{self.end}"

    def split(self, n_parts: int) -> list[Region]:
        """
        Split region into n equal parts.

        Parameters
        ----------
        n_parts : int
            Number of parts

        Returns
        -------
        list[Region]
        """
        part_size = len(self) // n_parts
        regions = []
        for i in range(n_parts):
            start = self.start + i * part_size
            end = start + part_size if i < n_parts - 1 else self.end
            regions.append(Region(self.chrom, start, end))
        return regions

    def windows(self, size: int, step: int | None = None) -> Iterator[Region]:
        """
        Generate sliding windows across region.

        Parameters
        ----------
        size : int
            Window size
        step : int, optional
            Step size (default: window size, non-overlapping)

        Yields
        ------
        Region
            Window regions
        """
        if step is None:
            step = size

        pos = self.start
        while pos < self.end:
            window_end = min(pos + size, self.end)
            yield Region(self.chrom, pos, window_end)
            pos += step


def parse_regions(
    regions: str | list[str] | None,
    coordinates: GenomeCoordinates,
) -> list[Region]:
    """
    Parse multiple regions.

    Parameters
    ----------
    regions : str, list[str], or None
        Region specification(s). If None, returns all chromosomes.
    coordinates : GenomeCoordinates
        Genome coordinates

    Returns
    -------
    list[Region]
    """
    if regions is None:
        # All chromosomes
        return [
            Region.whole_chromosome(chrom, coordinates)
            for chrom in coordinates.chromosome_names
        ]

    if isinstance(regions, str):
        regions = [regions]

    return [Region.parse(r, coordinates) for r in regions]
