"""GFF3 file parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from ..core.regions import Region


@dataclass
class GFFRecord:
    """Single GFF3 record."""
    chrom: str
    source: str
    feature_type: str
    start: int          # 1-based in file, converted to 0-based
    end: int
    score: float | None
    strand: str
    phase: str | None
    attributes: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return self.end - self.start

    def get_attribute(self, key: str, default: str | None = None) -> str | None:
        return self.attributes.get(key, default)

    @property
    def id(self) -> str | None:
        return self.attributes.get('ID')

    @property
    def name(self) -> str | None:
        return self.attributes.get('Name') or self.attributes.get('ID')

    @property
    def parent(self) -> str | None:
        return self.attributes.get('Parent')


def _parse_attributes(attr_string: str) -> dict[str, str]:
    """Parse GFF3 attribute string."""
    attributes = {}
    if attr_string == '.':
        return attributes

    for item in attr_string.split(';'):
        if '=' in item:
            key, value = item.split('=', 1)
            # URL decode
            import urllib.parse
            attributes[key] = urllib.parse.unquote(value)

    return attributes


def read_gff(
    path: str | Path,
    region: Region | None = None,
    feature_types: list[str] | None = None,
) -> Iterator[GFFRecord]:
    """
    Read GFF3 file as iterator.

    Parameters
    ----------
    path : str or Path
        Path to GFF3 file
    region : Region, optional
        Filter to this region
    feature_types : list[str], optional
        Only return these feature types

    Yields
    ------
    GFFRecord
    """
    import gzip

    opener = gzip.open if str(path).endswith('.gz') else open

    with opener(path, 'rt') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) != 9:
                continue

            chrom = parts[0]
            feature_type = parts[2]
            start = int(parts[3]) - 1  # Convert to 0-based
            end = int(parts[4])

            # Filter by feature type
            if feature_types is not None and feature_type not in feature_types:
                continue

            # Filter by region
            if region is not None:
                if chrom != region.chrom:
                    continue
                if end <= region.start or start >= region.end:
                    continue

            yield GFFRecord(
                chrom=chrom,
                source=parts[1],
                feature_type=feature_type,
                start=start,
                end=end,
                score=float(parts[5]) if parts[5] != '.' else None,
                strand=parts[6],
                phase=parts[7] if parts[7] != '.' else None,
                attributes=_parse_attributes(parts[8]),
            )


@dataclass
class Gene:
    """Gene with transcript structure."""
    id: str
    chrom: str
    start: int
    end: int
    strand: str
    name: str | None = None
    transcripts: list[Transcript] = field(default_factory=list)


@dataclass
class Transcript:
    """Transcript with exon/CDS structure."""
    id: str
    parent_gene: str
    exons: list[tuple[int, int]] = field(default_factory=list)
    cds: list[tuple[int, int]] = field(default_factory=list)


def read_genes(
    path: str | Path,
    region: Region | None = None,
) -> list[Gene]:
    """
    Parse GFF3 into Gene objects with structure.

    Parameters
    ----------
    path : str or Path
        Path to GFF3 file
    region : Region, optional
        Filter to this region

    Returns
    -------
    list[Gene]
    """
    genes: dict[str, Gene] = {}
    transcripts: dict[str, Transcript] = {}

    for record in read_gff(path, region):
        if record.feature_type == 'gene':
            gene = Gene(
                id=record.id or f"gene_{record.start}",
                chrom=record.chrom,
                start=record.start,
                end=record.end,
                strand=record.strand,
                name=record.name,
            )
            genes[gene.id] = gene

        elif record.feature_type in ('mRNA', 'transcript'):
            transcript = Transcript(
                id=record.id or f"tx_{record.start}",
                parent_gene=record.parent or '',
            )
            transcripts[transcript.id] = transcript

        elif record.feature_type == 'exon':
            parent = record.parent
            if parent and parent in transcripts:
                transcripts[parent].exons.append((record.start, record.end))

        elif record.feature_type == 'CDS':
            parent = record.parent
            if parent and parent in transcripts:
                transcripts[parent].cds.append((record.start, record.end))

    # Link transcripts to genes
    for tx in transcripts.values():
        if tx.parent_gene in genes:
            genes[tx.parent_gene].transcripts.append(tx)

    return list(genes.values())
