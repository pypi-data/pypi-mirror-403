"""
Chromoplot - Flexible genome visualization toolkit.

Examples
--------
>>> import chromoplot as cp

# Single region figure
>>> fig = cp.GenomeFigure("genome.fa.fai", region="chr1:1-10000000")
>>> fig.add_track(cp.IdeogramTrack())
>>> fig.add_track(cp.GeneTrack("genes.gff3"))
>>> fig.add_track(cp.HaplotypeTrack("haplotypes.bed"))
>>> fig.save("figure.pdf")

# Whole genome
>>> layout = cp.GenomeLayout(coords, arrangement='grid')
>>> layout.add_track(cp.IdeogramTrack())
>>> layout.add_track(cp.HaplotypeTrack("haplotypes.bed"))
>>> layout.save("genome.pdf")

# Comparative synteny
>>> layout = cp.ComparativeLayout(ref_coords, query_coords)
>>> layout.add_ref_track(cp.GeneTrack("ref_genes.gff3"))
>>> layout.add_synteny_track(cp.SyntenyTrack("synteny.paf"))
>>> layout.add_query_track(cp.GeneTrack("query_genes.gff3"))
>>> layout.save("synteny.pdf")
"""

from .core.figure import GenomeFigure
from .core.coordinates import GenomeCoordinates
from .core.regions import Region

# Tracks
from .tracks.ideogram import IdeogramTrack
from .tracks.feature import FeatureTrack
from .tracks.haplotype import HaplotypeTrack
from .tracks.gene import GeneTrack
from .tracks.alignment import AlignmentTrack
from .tracks.depth import DepthTrack
from .tracks.signal import SignalTrack
from .tracks.variant import VariantTrack
from .tracks.synteny import SyntenyTrack
from .tracks.scale import ScaleBarTrack
from .tracks.annotation import AnnotationTrack, Annotation

# Layouts
from .layouts.genome import GenomeLayout
from .layouts.comparative import ComparativeLayout

# Themes
from .themes.theme import Theme, get_theme, register_theme
from .themes.colors import get_palette, founder_colors, maize_nam_colors

__version__ = "0.1.0"

__all__ = [
    # Core
    'GenomeFigure',
    'GenomeCoordinates',
    'Region',
    # Tracks
    'IdeogramTrack',
    'FeatureTrack',
    'HaplotypeTrack',
    'GeneTrack',
    'AlignmentTrack',
    'DepthTrack',
    'SignalTrack',
    'VariantTrack',
    'SyntenyTrack',
    'ScaleBarTrack',
    'AnnotationTrack',
    'Annotation',
    # Layouts
    'GenomeLayout',
    'ComparativeLayout',
    # Themes
    'Theme',
    'get_theme',
    'register_theme',
    'get_palette',
    'founder_colors',
    'maize_nam_colors',
]
