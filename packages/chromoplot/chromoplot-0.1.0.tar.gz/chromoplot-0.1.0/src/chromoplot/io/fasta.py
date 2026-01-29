"""FASTA and related file parsing."""

from __future__ import annotations

from pathlib import Path


def read_fai(path: str | Path) -> dict[str, int]:
    """
    Read FASTA index file.

    Parameters
    ----------
    path : str or Path
        Path to .fai file

    Returns
    -------
    dict[str, int]
        Mapping of chromosome names to sizes
    """
    chromosomes = {}
    with open(path) as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                chrom = parts[0]
                size = int(parts[1])
                chromosomes[chrom] = size
    return chromosomes


def read_chrom_sizes(path: str | Path) -> dict[str, int]:
    """
    Read UCSC chrom.sizes format.

    Parameters
    ----------
    path : str or Path
        Path to chrom.sizes file

    Returns
    -------
    dict[str, int]
        Mapping of chromosome names to sizes
    """
    chromosomes = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                chrom = parts[0]
                size = int(parts[1])
                chromosomes[chrom] = size
    return chromosomes
