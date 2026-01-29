"""BAM file handling for coverage extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import numpy as np

from ..core.regions import Region


def get_coverage(
    path: str | Path,
    region: Region,
    bin_size: int = 1000,
    min_mapq: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract coverage from BAM file.

    Parameters
    ----------
    path : str or Path
        Path to BAM file (must be indexed)
    region : Region
        Region to extract coverage for
    bin_size : int
        Bin size for coverage calculation
    min_mapq : int
        Minimum mapping quality

    Returns
    -------
    positions : np.ndarray
        Bin positions (centers)
    coverage : np.ndarray
        Coverage values per bin
    """
    try:
        import pysam
    except ImportError:
        raise ImportError("pysam required for BAM support: pip install pysam")

    # Open BAM file
    bam = pysam.AlignmentFile(str(path), "rb")

    # Calculate bins
    n_bins = (len(region) + bin_size - 1) // bin_size
    coverage = np.zeros(n_bins)
    positions = np.array([
        region.start + i * bin_size + bin_size // 2
        for i in range(n_bins)
    ])

    # Count coverage per bin
    for read in bam.fetch(region.chrom, region.start, region.end):
        if read.mapping_quality < min_mapq:
            continue
        if read.is_unmapped or read.is_secondary or read.is_supplementary:
            continue

        # Find overlapping bins
        read_start = max(read.reference_start, region.start)
        read_end = min(read.reference_end or read.reference_start + 1, region.end)

        start_bin = (read_start - region.start) // bin_size
        end_bin = (read_end - region.start) // bin_size

        for bin_idx in range(start_bin, min(end_bin + 1, n_bins)):
            coverage[bin_idx] += 1

    bam.close()

    return positions, coverage


def get_coverage_pileup(
    path: str | Path,
    region: Region,
    min_mapq: int = 0,
    max_depth: int = 100000,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Get per-base coverage using pileup.

    Parameters
    ----------
    path : str or Path
        Path to BAM file
    region : Region
        Region to extract
    min_mapq : int
        Minimum mapping quality
    max_depth : int
        Maximum depth to report

    Returns
    -------
    positions : np.ndarray
        Positions
    coverage : np.ndarray
        Per-base coverage
    """
    try:
        import pysam
    except ImportError:
        raise ImportError("pysam required for BAM support")

    bam = pysam.AlignmentFile(str(path), "rb")

    positions = []
    coverage = []

    for pileup in bam.pileup(
        region.chrom,
        region.start,
        region.end,
        min_mapping_quality=min_mapq,
        max_depth=max_depth,
        truncate=True,
    ):
        if region.start <= pileup.reference_pos < region.end:
            positions.append(pileup.reference_pos)
            coverage.append(pileup.nsegments)

    bam.close()

    return np.array(positions), np.array(coverage)
