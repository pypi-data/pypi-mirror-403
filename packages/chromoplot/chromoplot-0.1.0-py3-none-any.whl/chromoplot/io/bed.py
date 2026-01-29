"""BED file parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import pandas as pd

from ..core.regions import Region


@dataclass
class BEDRecord:
    """
    Single BED record.

    Attributes
    ----------
    chrom : str
        Chromosome name
    start : int
        Start position (0-based)
    end : int
        End position
    name : str, optional
        Feature name
    score : float, optional
        Score value
    strand : str, optional
        Strand (+/-)
    extras : dict
        Additional fields
    """
    chrom: str
    start: int
    end: int
    name: str | None = None
    score: float | None = None
    strand: str | None = None
    extras: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return self.end - self.start

    def to_region(self) -> Region:
        return Region(self.chrom, self.start, self.end)


def read_bed(
    path: str | Path,
    region: Region | None = None,
) -> Iterator[BEDRecord]:
    """
    Read BED file as iterator.

    Parameters
    ----------
    path : str or Path
        Path to BED file
    region : Region, optional
        Filter to this region

    Yields
    ------
    BEDRecord
    """
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('track') or line.startswith('browser'):
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            chrom = parts[0]
            start = int(parts[1])
            end = int(parts[2])

            # Filter by region
            if region is not None:
                if chrom != region.chrom:
                    continue
                if end <= region.start or start >= region.end:
                    continue

            record = BEDRecord(
                chrom=chrom,
                start=start,
                end=end,
                name=parts[3] if len(parts) > 3 else None,
                score=float(parts[4]) if len(parts) > 4 and parts[4] != '.' else None,
                strand=parts[5] if len(parts) > 5 else None,
            )

            # Additional fields
            if len(parts) > 6:
                record.extras = {f'field_{i}': parts[i] for i in range(6, len(parts))}

            yield record


def read_bed_to_dataframe(
    path: str | Path,
    region: Region | None = None,
) -> pd.DataFrame:
    """
    Read BED file to DataFrame.

    Parameters
    ----------
    path : str or Path
        Path to BED file
    region : Region, optional
        Filter to this region

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: chrom, start, end, name, score, strand
    """
    records = list(read_bed(path, region))

    if not records:
        return pd.DataFrame(columns=['chrom', 'start', 'end', 'name', 'score', 'strand'])

    return pd.DataFrame([
        {
            'chrom': r.chrom,
            'start': r.start,
            'end': r.end,
            'name': r.name,
            'score': r.score,
            'strand': r.strand,
            **r.extras,
        }
        for r in records
    ])


def write_bed(
    records: list[BEDRecord] | pd.DataFrame,
    path: str | Path,
    header: str | None = None,
) -> None:
    """
    Write BED file.

    Parameters
    ----------
    records : list[BEDRecord] or DataFrame
        Records to write
    path : str or Path
        Output path
    header : str, optional
        Header line (e.g., track line)
    """
    with open(path, 'w') as f:
        if header:
            f.write(header + '\n')

        if isinstance(records, pd.DataFrame):
            for _, row in records.iterrows():
                fields = [
                    row['chrom'],
                    str(row['start']),
                    str(row['end']),
                ]
                if 'name' in row and row['name']:
                    fields.append(str(row['name']))
                    if 'score' in row:
                        fields.append(str(row['score']) if row['score'] is not None else '.')
                        if 'strand' in row and row['strand']:
                            fields.append(row['strand'])
                f.write('\t'.join(fields) + '\n')
        else:
            for record in records:
                fields = [record.chrom, str(record.start), str(record.end)]
                if record.name:
                    fields.append(record.name)
                    if record.score is not None:
                        fields.append(str(record.score))
                        if record.strand:
                            fields.append(record.strand)
                f.write('\t'.join(fields) + '\n')
