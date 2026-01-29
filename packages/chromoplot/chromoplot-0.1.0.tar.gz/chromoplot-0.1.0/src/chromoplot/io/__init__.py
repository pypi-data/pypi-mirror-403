"""I/O functions for reading genomic file formats."""

from .fasta import read_fai, read_chrom_sizes
from .bed import read_bed, read_bed_to_dataframe, write_bed, BEDRecord
from .gff import read_gff, read_genes, GFFRecord, Gene, Transcript
from .paf import read_paf, read_paf_to_dataframe, PAFRecord
from .bam import get_coverage, get_coverage_pileup
from .synteny import read_synteny, write_synteny_bed, SyntenyBlock

__all__ = [
    'read_fai',
    'read_chrom_sizes',
    'read_bed',
    'read_bed_to_dataframe',
    'write_bed',
    'BEDRecord',
    'read_gff',
    'read_genes',
    'GFFRecord',
    'Gene',
    'Transcript',
    'read_paf',
    'read_paf_to_dataframe',
    'PAFRecord',
    'get_coverage',
    'get_coverage_pileup',
    'read_synteny',
    'write_synteny_bed',
    'SyntenyBlock',
]
