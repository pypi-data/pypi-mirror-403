"""PAF (Pairwise mApping Format) parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..core.regions import Region


@dataclass
class PAFRecord:
    """
    PAF alignment record.

    Attributes
    ----------
    query_name : str
        Query sequence name
    query_length : int
        Query sequence length
    query_start : int
        Query start (0-based)
    query_end : int
        Query end
    strand : str
        '+' or '-'
    target_name : str
        Target sequence name
    target_length : int
        Target sequence length
    target_start : int
        Target start (0-based)
    target_end : int
        Target end
    matches : int
        Number of matches
    block_length : int
        Alignment block length
    mapq : int
        Mapping quality
    tags : dict
        Optional tags (tp, cm, etc.)
    """
    query_name: str
    query_length: int
    query_start: int
    query_end: int
    strand: str
    target_name: str
    target_length: int
    target_start: int
    target_end: int
    matches: int
    block_length: int
    mapq: int
    tags: dict = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

    @property
    def identity(self) -> float:
        """Alignment identity (matches / block_length)."""
        if self.block_length == 0:
            return 0.0
        return self.matches / self.block_length

    @property
    def query_coverage(self) -> float:
        """Query coverage fraction."""
        if self.query_length == 0:
            return 0.0
        return (self.query_end - self.query_start) / self.query_length

    @property
    def target_span(self) -> int:
        """Target alignment span."""
        return self.target_end - self.target_start


def read_paf(
    path: str | Path,
    target_region: Region | None = None,
    min_mapq: int = 0,
    min_length: int = 0,
) -> Iterator[PAFRecord]:
    """
    Read PAF file.

    Parameters
    ----------
    path : str or Path
        Path to PAF file
    target_region : Region, optional
        Filter to alignments overlapping this target region
    min_mapq : int
        Minimum mapping quality
    min_length : int
        Minimum alignment length

    Yields
    ------
    PAFRecord
    """
    import gzip

    opener = gzip.open if str(path).endswith('.gz') else open

    with opener(path, 'rt') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 12:
                continue

            record = PAFRecord(
                query_name=parts[0],
                query_length=int(parts[1]),
                query_start=int(parts[2]),
                query_end=int(parts[3]),
                strand=parts[4],
                target_name=parts[5],
                target_length=int(parts[6]),
                target_start=int(parts[7]),
                target_end=int(parts[8]),
                matches=int(parts[9]),
                block_length=int(parts[10]),
                mapq=int(parts[11]),
            )

            # Parse tags
            if len(parts) > 12:
                for tag in parts[12:]:
                    if ':' in tag:
                        tag_parts = tag.split(':')
                        if len(tag_parts) >= 3:
                            record.tags[tag_parts[0]] = tag_parts[2]

            # Apply filters
            if record.mapq < min_mapq:
                continue
            if record.block_length < min_length:
                continue

            # Filter by region
            if target_region is not None:
                if record.target_name != target_region.chrom:
                    continue
                if record.target_end <= target_region.start:
                    continue
                if record.target_start >= target_region.end:
                    continue

            yield record


def read_paf_to_dataframe(
    path: str | Path,
    target_region: Region | None = None,
    min_mapq: int = 0,
    min_length: int = 0,
) -> 'pd.DataFrame':
    """Read PAF to DataFrame."""
    import pandas as pd

    records = list(read_paf(path, target_region, min_mapq, min_length))

    if not records:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            'query_name': r.query_name,
            'query_length': r.query_length,
            'query_start': r.query_start,
            'query_end': r.query_end,
            'strand': r.strand,
            'target_name': r.target_name,
            'target_length': r.target_length,
            'target_start': r.target_start,
            'target_end': r.target_end,
            'matches': r.matches,
            'block_length': r.block_length,
            'mapq': r.mapq,
            'identity': r.identity,
        }
        for r in records
    ])
