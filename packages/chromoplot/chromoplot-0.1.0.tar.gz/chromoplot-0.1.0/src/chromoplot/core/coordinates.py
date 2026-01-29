"""Genomic coordinate handling and transformations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np


@dataclass
class GenomeCoordinates:
    """
    Manages genomic coordinate system and transformations.

    Handles conversion between genomic positions and figure coordinates,
    supports whole-genome linearization for multi-chromosome plots.

    Parameters
    ----------
    chromosomes : dict[str, int]
        Mapping of chromosome names to sizes in base pairs

    Examples
    --------
    >>> coords = GenomeCoordinates.from_fai("genome.fa.fai")
    >>> coords.total_size
    2300000000
    >>> coords.linearize("chr2", 1000000)
    301000000
    """

    chromosomes: dict[str, int]
    _cumulative: dict[str, int] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Calculate cumulative positions for linearization."""
        cumsum = 0
        for chrom, size in self.chromosomes.items():
            self._cumulative[chrom] = cumsum
            cumsum += size

    @classmethod
    def from_fai(cls, path: str | Path) -> GenomeCoordinates:
        """
        Create from FASTA index file.

        Parameters
        ----------
        path : str or Path
            Path to .fai file

        Returns
        -------
        GenomeCoordinates
        """
        chromosomes = {}
        with open(path) as f:
            for line in f:
                parts = line.strip().split('\t')
                chrom = parts[0]
                size = int(parts[1])
                chromosomes[chrom] = size
        return cls(chromosomes)

    @classmethod
    def from_chrom_sizes(cls, path: str | Path) -> GenomeCoordinates:
        """
        Create from UCSC chrom.sizes file.

        Parameters
        ----------
        path : str or Path
            Path to chrom.sizes file

        Returns
        -------
        GenomeCoordinates
        """
        chromosomes = {}
        with open(path) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    chrom = parts[0]
                    size = int(parts[1])
                    chromosomes[chrom] = size
        return cls(chromosomes)

    @classmethod
    def from_dict(cls, chromosomes: dict[str, int]) -> GenomeCoordinates:
        """
        Create from dictionary.

        Parameters
        ----------
        chromosomes : dict
            Mapping of chromosome names to sizes

        Returns
        -------
        GenomeCoordinates
        """
        return cls(chromosomes)

    @property
    def total_size(self) -> int:
        """Total genome size in base pairs."""
        return sum(self.chromosomes.values())

    @property
    def n_chromosomes(self) -> int:
        """Number of chromosomes."""
        return len(self.chromosomes)

    @property
    def chromosome_names(self) -> list[str]:
        """List of chromosome names in order."""
        return list(self.chromosomes.keys())

    def get_size(self, chrom: str) -> int:
        """
        Get size of a chromosome.

        Parameters
        ----------
        chrom : str
            Chromosome name

        Returns
        -------
        int
            Chromosome size in bp

        Raises
        ------
        KeyError
            If chromosome not found
        """
        if chrom not in self.chromosomes:
            raise KeyError(f"Chromosome '{chrom}' not found. "
                          f"Available: {list(self.chromosomes.keys())[:5]}...")
        return self.chromosomes[chrom]

    def linearize(self, chrom: str, pos: int) -> int:
        """
        Convert chromosome position to linear genome position.

        Parameters
        ----------
        chrom : str
            Chromosome name
        pos : int
            Position on chromosome (0-based)

        Returns
        -------
        int
            Linear position across whole genome
        """
        return self._cumulative[chrom] + pos

    def delinearize(self, linear_pos: int) -> tuple[str, int]:
        """
        Convert linear position back to chromosome coordinates.

        Parameters
        ----------
        linear_pos : int
            Linear genome position

        Returns
        -------
        tuple[str, int]
            (chromosome, position)
        """
        for chrom, cumul in self._cumulative.items():
            chrom_size = self.chromosomes[chrom]
            if cumul <= linear_pos < cumul + chrom_size:
                return chrom, linear_pos - cumul
        raise ValueError(f"Position {linear_pos} out of genome bounds")

    def validate_region(self, chrom: str, start: int, end: int) -> bool:
        """
        Check if region is valid.

        Parameters
        ----------
        chrom : str
            Chromosome name
        start : int
            Start position (0-based)
        end : int
            End position

        Returns
        -------
        bool
            True if valid
        """
        if chrom not in self.chromosomes:
            return False
        if start < 0 or end < 0:
            return False
        if start >= end:
            return False
        if end > self.chromosomes[chrom]:
            return False
        return True

    def iter_chromosomes(self) -> Iterator[tuple[str, int]]:
        """
        Iterate over chromosomes.

        Yields
        ------
        tuple[str, int]
            (chromosome_name, size)
        """
        for chrom, size in self.chromosomes.items():
            yield chrom, size

    def filter_chromosomes(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        min_size: int | None = None,
        pattern: str | None = None,
    ) -> GenomeCoordinates:
        """
        Create new GenomeCoordinates with filtered chromosomes.

        Parameters
        ----------
        include : list[str], optional
            Only include these chromosomes
        exclude : list[str], optional
            Exclude these chromosomes
        min_size : int, optional
            Minimum chromosome size
        pattern : str, optional
            Regex pattern for chromosome names

        Returns
        -------
        GenomeCoordinates
            Filtered coordinates
        """
        import re

        filtered = {}
        for chrom, size in self.chromosomes.items():
            # Apply filters
            if include is not None and chrom not in include:
                continue
            if exclude is not None and chrom in exclude:
                continue
            if min_size is not None and size < min_size:
                continue
            if pattern is not None and not re.match(pattern, chrom):
                continue
            filtered[chrom] = size

        return GenomeCoordinates(filtered)
