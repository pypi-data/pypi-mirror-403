"""Synteny file parsing for various formats."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import pandas as pd


@dataclass
class SyntenyBlock:
    """
    Synteny block between two genomes.

    Attributes
    ----------
    ref_chrom : str
        Reference chromosome
    ref_start : int
        Reference start (0-based)
    ref_end : int
        Reference end
    query_chrom : str
        Query chromosome
    query_start : int
        Query start
    query_end : int
        Query end
    orientation : str
        '+' (same) or '-' (inverted)
    score : float, optional
        Alignment/synteny score
    identity : float, optional
        Sequence identity
    block_id : str, optional
        Block identifier
    """
    ref_chrom: str
    ref_start: int
    ref_end: int
    query_chrom: str
    query_start: int
    query_end: int
    orientation: str = '+'
    score: float | None = None
    identity: float | None = None
    block_id: str | None = None

    @property
    def ref_length(self) -> int:
        return self.ref_end - self.ref_start

    @property
    def query_length(self) -> int:
        return self.query_end - self.query_start


def read_synteny(
    path: str | Path,
    format: Literal['auto', 'paf', 'syri', 'mcscanx', 'genespace', 'bed'] = 'auto',
    min_length: int = 0,
) -> list[SyntenyBlock]:
    """
    Read synteny blocks from various formats.

    Parameters
    ----------
    path : str or Path
        Path to synteny file
    format : str
        File format (auto-detect if 'auto')
    min_length : int
        Minimum block length to include

    Returns
    -------
    list[SyntenyBlock]
    """
    path = Path(path)

    if format == 'auto':
        format = _detect_format(path)

    readers = {
        'paf': _read_paf_synteny,
        'syri': _read_syri,
        'mcscanx': _read_mcscanx,
        'genespace': _read_genespace,
        'bed': _read_bed_synteny,
        'links': _read_links,
    }

    if format not in readers:
        raise ValueError(f"Unknown format: {format}. Supported: {list(readers.keys())}")

    blocks = readers[format](path)

    # Apply minimum length filter
    if min_length > 0:
        blocks = [b for b in blocks if b.ref_length >= min_length]

    return blocks


def _detect_format(path: Path) -> str:
    """Auto-detect synteny file format."""
    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix == '.paf':
        return 'paf'
    elif 'syri' in name or suffix == '.syri':
        return 'syri'
    elif 'collinearity' in name:
        return 'mcscanx'
    elif suffix in ('.bed', '.bedpe'):
        return 'bed'
    elif suffix == '.links':
        return 'links'

    # Try to detect by content
    with open(path) as f:
        first_line = f.readline().strip()
        if first_line.startswith('#') and 'syri' in first_line.lower():
            return 'syri'
        parts = first_line.split('\t')
        if len(parts) >= 12:
            return 'paf'

    return 'bed'  # Default


def _read_paf_synteny(path: Path) -> list[SyntenyBlock]:
    """Read synteny from PAF alignment file."""
    from .paf import read_paf

    blocks = []
    for record in read_paf(path):
        blocks.append(SyntenyBlock(
            ref_chrom=record.target_name,
            ref_start=record.target_start,
            ref_end=record.target_end,
            query_chrom=record.query_name,
            query_start=record.query_start,
            query_end=record.query_end,
            orientation=record.strand,
            identity=record.identity,
        ))

    return blocks


def _read_syri(path: Path) -> list[SyntenyBlock]:
    """
    Read SyRI output format.

    SyRI output has columns:
    ref_chr, ref_start, ref_end, seq, query_chr, query_start, query_end, ...
    """
    blocks = []

    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 7:
                continue

            # SyRI marks synteny as 'SYN' and inversions as 'INV'
            if len(parts) > 10:
                block_type = parts[10] if len(parts) > 10 else ''
                if block_type not in ('SYN', 'SYNAL', 'INV', 'INVAL'):
                    continue
                orientation = '-' if 'INV' in block_type else '+'
            else:
                orientation = '+'

            blocks.append(SyntenyBlock(
                ref_chrom=parts[0],
                ref_start=int(parts[1]) - 1,  # Convert to 0-based
                ref_end=int(parts[2]),
                query_chrom=parts[4],
                query_start=int(parts[5]) - 1,
                query_end=int(parts[6]),
                orientation=orientation,
            ))

    return blocks


def _read_mcscanx(path: Path) -> list[SyntenyBlock]:
    """
    Read MCScanX collinearity format.

    Format:
    ## Alignment N: score=X ...
    N-  0: gene1 gene2 ...
    """
    blocks = []
    current_block_id = None
    current_ref_genes = []
    current_query_genes = []

    # Would need gene position file to convert gene names to coordinates
    # This is a simplified version that expects coordinate format

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('##'):
                # New alignment block
                if 'Alignment' in line:
                    current_block_id = line.split(':')[0].replace('##', '').strip()
            elif line.startswith('#'):
                continue
            elif line and current_block_id:
                # Parse gene pair line
                parts = line.split('\t')
                if len(parts) >= 2:
                    # Simplified - actual implementation needs gene->coord mapping
                    pass

    return blocks


def _read_genespace(path: Path) -> list[SyntenyBlock]:
    """Read GENESPACE synteny output."""
    blocks = []

    # GENESPACE outputs various formats, this handles the riparian format
    df = pd.read_csv(path, sep='\t')

    required_cols = ['chr1', 'start1', 'end1', 'chr2', 'start2', 'end2']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("GENESPACE file missing required columns")

    for _, row in df.iterrows():
        blocks.append(SyntenyBlock(
            ref_chrom=str(row['chr1']),
            ref_start=int(row['start1']),
            ref_end=int(row['end1']),
            query_chrom=str(row['chr2']),
            query_start=int(row['start2']),
            query_end=int(row['end2']),
            orientation=row.get('strand', '+'),
        ))

    return blocks


def _read_bed_synteny(path: Path) -> list[SyntenyBlock]:
    """
    Read synteny from BED-like format.

    Expected format (tab-separated):
    ref_chr  ref_start  ref_end  query_chr  query_start  query_end  [strand]
    """
    blocks = []

    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 6:
                continue

            blocks.append(SyntenyBlock(
                ref_chrom=parts[0],
                ref_start=int(parts[1]),
                ref_end=int(parts[2]),
                query_chrom=parts[3],
                query_start=int(parts[4]),
                query_end=int(parts[5]),
                orientation=parts[6] if len(parts) > 6 else '+',
            ))

    return blocks


def _read_links(path: Path) -> list[SyntenyBlock]:
    """
    Read Circos-style links format.

    Format:
    chr1 start1 end1 chr2 start2 end2 [options]
    """
    blocks = []

    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split()
            if len(parts) < 6:
                continue

            blocks.append(SyntenyBlock(
                ref_chrom=parts[0],
                ref_start=int(parts[1]),
                ref_end=int(parts[2]),
                query_chrom=parts[3],
                query_start=int(parts[4]),
                query_end=int(parts[5]),
            ))

    return blocks


def write_synteny_bed(blocks: list[SyntenyBlock], path: str | Path) -> None:
    """Write synteny blocks to BED-like format."""
    with open(path, 'w') as f:
        f.write("#ref_chr\tref_start\tref_end\tquery_chr\tquery_start\tquery_end\tstrand\n")
        for block in blocks:
            f.write(f"{block.ref_chrom}\t{block.ref_start}\t{block.ref_end}\t"
                   f"{block.query_chrom}\t{block.query_start}\t{block.query_end}\t"
                   f"{block.orientation}\n")
