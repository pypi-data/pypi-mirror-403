"""Command-line interface for chromoplot."""

from __future__ import annotations

from pathlib import Path

import click


@click.group()
@click.version_option()
def cli():
    """Chromoplot - Flexible genome visualization toolkit."""
    pass


@cli.command()
@click.option('--reference', '-r', required=True, help='FASTA index or chrom.sizes file')
@click.option('--region', help='Region to plot (e.g., chr1:1000000-2000000)')
@click.option('--bed', multiple=True, help='BED file(s) to plot as feature tracks')
@click.option('--gff', help='GFF3 file for gene track')
@click.option('--haplotypes', help='Haplotype BED file (phaser output)')
@click.option('--bam', help='BAM file for coverage track')
@click.option('--paf', help='PAF file for alignment track')
@click.option('--vcf', help='VCF file for variant track')
@click.option('--output', '-o', required=True, help='Output file (PDF/PNG/SVG)')
@click.option('--width', type=float, default=12, help='Figure width in inches')
@click.option('--height', type=float, default=None, help='Figure height (auto if not set)')
@click.option('--theme', default='publication', help='Color theme')
@click.option('--title', help='Figure title')
def plot(reference, region, bed, gff, haplotypes, bam, paf, vcf, output, width, height, theme, title):
    """
    Create genome visualization.

    Examples:

        chromoplot plot -r genome.fa.fai --bed features.bed -o figure.pdf

        chromoplot plot -r genome.fa.fai --region chr1:1-10000000 \\
            --gff genes.gff3 --haplotypes haplotypes.bed -o figure.pdf
    """
    from ..core.figure import GenomeFigure
    from ..tracks.ideogram import IdeogramTrack
    from ..tracks.feature import FeatureTrack
    from ..tracks.haplotype import HaplotypeTrack
    from ..tracks.gene import GeneTrack
    from ..tracks.alignment import AlignmentTrack
    from ..tracks.depth import DepthTrack
    from ..tracks.variant import VariantTrack
    from ..tracks.scale import ScaleBarTrack

    # Count tracks for height calculation
    n_tracks = 1  # Ideogram
    if bed:
        n_tracks += len(bed)
    if gff:
        n_tracks += 1
    if haplotypes:
        n_tracks += 1
    if bam:
        n_tracks += 1
    if paf:
        n_tracks += 1
    if vcf:
        n_tracks += 1
    n_tracks += 1  # Scale bar

    if height is None:
        height = max(4, n_tracks * 0.8)

    # Create figure
    fig = GenomeFigure(
        reference=reference,
        region=region,
        figsize=(width, height),
        theme=theme,
        title=title,
    )

    # Add tracks in order
    fig.add_track(IdeogramTrack())

    if gff:
        fig.add_track(GeneTrack(gff, label='Genes'))

    for bed_file in bed:
        label = Path(bed_file).stem
        fig.add_track(FeatureTrack(bed_file, label=label))

    if paf:
        fig.add_track(AlignmentTrack(paf, label='Alignments'))

    if bam:
        fig.add_track(DepthTrack(bam, label='Coverage'))

    if haplotypes:
        fig.add_track(HaplotypeTrack(haplotypes, label='Haplotypes'))

    if vcf:
        fig.add_track(VariantTrack(vcf, label='Variants'))

    fig.add_track(ScaleBarTrack())

    # Render and save
    fig.save(output)
    click.echo(f"Saved figure to {output}")


@cli.command()
@click.option('--reference', '-r', required=True, help='FASTA index file')
@click.option('--haplotypes', help='Haplotype BED file')
@click.option('--bed', multiple=True, help='Additional BED tracks')
@click.option('--output', '-o', required=True, help='Output file')
@click.option('--cols', type=int, default=5, help='Number of columns in grid')
@click.option('--width', type=float, default=16, help='Figure width')
@click.option('--height', type=float, default=None, help='Figure height (auto if not set)')
def genome(reference, haplotypes, bed, output, cols, width, height):
    """
    Create whole-genome visualization.

    Displays all chromosomes in a grid layout.

    Example:

        chromoplot genome -r genome.fa.fai --haplotypes haplotypes.bed -o genome.pdf
    """
    from ..core.coordinates import GenomeCoordinates
    from ..layouts.genome import GenomeLayout
    from ..tracks.ideogram import IdeogramTrack
    from ..tracks.haplotype import HaplotypeTrack
    from ..tracks.feature import FeatureTrack

    coords = GenomeCoordinates.from_fai(reference)

    # Calculate height
    n_chroms = coords.n_chromosomes
    n_rows = (n_chroms + cols - 1) // cols
    n_tracks = 1 + (1 if haplotypes else 0) + len(bed)

    if height is None:
        height = n_rows * n_tracks * 0.8

    layout = GenomeLayout(
        coords,
        arrangement='grid',
        n_cols=cols,
        figsize=(width, height),
    )

    layout.add_track(IdeogramTrack())

    for bed_file in bed:
        layout.add_track(FeatureTrack(bed_file, label=Path(bed_file).stem))

    if haplotypes:
        layout.add_track(HaplotypeTrack(haplotypes, label='Haplotypes'))

    layout.save(output)
    click.echo(f"Saved whole-genome figure to {output}")


@cli.command()
@click.option('--ref-fai', required=True, help='Reference genome FASTA index')
@click.option('--query-fai', required=True, help='Query genome FASTA index')
@click.option('--synteny', required=True, help='Synteny file (PAF, SyRI, etc.)')
@click.option('--ref-region', help='Reference region')
@click.option('--query-region', help='Query region')
@click.option('--ref-gff', help='Reference genes GFF3')
@click.option('--query-gff', help='Query genes GFF3')
@click.option('--format', 'syn_format', default='auto', help='Synteny file format')
@click.option('--output', '-o', required=True, help='Output file')
@click.option('--width', type=float, default=14, help='Figure width')
@click.option('--height', type=float, default=10, help='Figure height')
def comparative(ref_fai, query_fai, synteny, ref_region, query_region,
                ref_gff, query_gff, syn_format, output, width, height):
    """
    Create comparative synteny visualization.

    Shows synteny between two genomes with ribbons connecting
    corresponding regions.

    Example:

        chromoplot comparative --ref-fai ref.fa.fai --query-fai query.fa.fai \\
            --synteny alignment.paf --ref-region chr1 --query-region chr1 \\
            -o synteny.pdf
    """
    from ..core.coordinates import GenomeCoordinates
    from ..layouts.comparative import ComparativeLayout
    from ..tracks.ideogram import IdeogramTrack
    from ..tracks.gene import GeneTrack
    from ..tracks.synteny import SyntenyTrack

    ref_coords = GenomeCoordinates.from_fai(ref_fai)
    query_coords = GenomeCoordinates.from_fai(query_fai)

    layout = ComparativeLayout(
        ref_coords,
        query_coords,
        ref_region=ref_region,
        query_region=query_region,
        figsize=(width, height),
    )

    # Reference tracks (top)
    layout.add_ref_track(IdeogramTrack())
    if ref_gff:
        layout.add_ref_track(GeneTrack(ref_gff, label='Genes'))

    # Synteny (middle)
    layout.add_synteny_track(SyntenyTrack(synteny, format=syn_format))

    # Query tracks (bottom)
    if query_gff:
        layout.add_query_track(GeneTrack(query_gff, label='Genes'))
    layout.add_query_track(IdeogramTrack())

    layout.save(output)
    click.echo(f"Saved comparative figure to {output}")


@cli.command()
@click.argument('config', type=click.Path(exists=True))
@click.option('--output', '-o', required=True, help='Output file')
def from_config(config, output):
    """
    Create figure from YAML configuration.

    Example config (config.yaml):

    \b
        type: figure
        reference: genome.fa.fai
        region: chr1:1-10000000
        tracks:
          - type: ideogram
          - type: gene
            path: genes.gff3
            label: Genes
          - type: haplotype
            path: haplotypes.bed

    Usage:

        chromoplot from-config config.yaml -o figure.pdf
    """
    import yaml

    with open(config) as f:
        cfg = yaml.safe_load(f)

    fig_type = cfg.get('type', 'figure')

    if fig_type == 'figure':
        _render_figure_config(cfg, output)
    elif fig_type == 'genome':
        _render_genome_config(cfg, output)
    elif fig_type == 'comparative':
        _render_comparative_config(cfg, output)
    else:
        raise click.ClickException(f"Unknown figure type: {fig_type}")

    click.echo(f"Saved figure to {output}")


def _render_figure_config(cfg: dict, output: str) -> None:
    """Render single-region figure from config."""
    from ..core.figure import GenomeFigure

    fig = GenomeFigure(
        reference=cfg['reference'],
        region=cfg.get('region'),
        figsize=tuple(cfg['figsize']) if 'figsize' in cfg else None,
        theme=cfg.get('theme', 'publication'),
        title=cfg.get('title'),
    )

    for track_cfg in cfg.get('tracks', []):
        track = _create_track(track_cfg)
        fig.add_track(track)

    fig.save(output)


def _render_genome_config(cfg: dict, output: str) -> None:
    """Render whole-genome figure from config."""
    from ..core.coordinates import GenomeCoordinates
    from ..layouts.genome import GenomeLayout

    coords = GenomeCoordinates.from_fai(cfg['reference'])

    layout = GenomeLayout(
        coords,
        arrangement=cfg.get('arrangement', 'grid'),
        n_cols=cfg.get('columns'),
        figsize=tuple(cfg['figsize']) if 'figsize' in cfg else None,
    )

    for track_cfg in cfg.get('tracks', []):
        track = _create_track(track_cfg)
        layout.add_track(track)

    layout.save(output)


def _render_comparative_config(cfg: dict, output: str) -> None:
    """Render comparative figure from config."""
    from ..core.coordinates import GenomeCoordinates
    from ..layouts.comparative import ComparativeLayout

    ref_coords = GenomeCoordinates.from_fai(cfg['reference'])
    query_coords = GenomeCoordinates.from_fai(cfg['query'])

    layout = ComparativeLayout(
        ref_coords,
        query_coords,
        ref_region=cfg.get('ref_region'),
        query_region=cfg.get('query_region'),
        figsize=tuple(cfg['figsize']) if 'figsize' in cfg else None,
    )

    for track_cfg in cfg.get('ref_tracks', []):
        track = _create_track(track_cfg)
        layout.add_ref_track(track)

    if 'synteny' in cfg:
        from ..tracks.synteny import SyntenyTrack
        syn_cfg = cfg['synteny']
        track = SyntenyTrack(
            syn_cfg['path'],
            format=syn_cfg.get('format', 'auto'),
            style=syn_cfg.get('style'),
        )
        layout.add_synteny_track(track)

    for track_cfg in cfg.get('query_tracks', []):
        track = _create_track(track_cfg)
        layout.add_query_track(track)

    layout.save(output)


def _create_track(cfg: dict) -> 'BaseTrack':
    """Create track from config dict."""
    from ..tracks.ideogram import IdeogramTrack
    from ..tracks.feature import FeatureTrack
    from ..tracks.haplotype import HaplotypeTrack
    from ..tracks.gene import GeneTrack
    from ..tracks.alignment import AlignmentTrack
    from ..tracks.depth import DepthTrack
    from ..tracks.signal import SignalTrack
    from ..tracks.variant import VariantTrack
    from ..tracks.scale import ScaleBarTrack
    from ..tracks.annotation import AnnotationTrack

    track_classes = {
        'ideogram': IdeogramTrack,
        'feature': FeatureTrack,
        'haplotype': HaplotypeTrack,
        'gene': GeneTrack,
        'alignment': AlignmentTrack,
        'depth': DepthTrack,
        'signal': SignalTrack,
        'variant': VariantTrack,
        'scale': ScaleBarTrack,
        'annotation': AnnotationTrack,
    }

    # Make a copy to avoid modifying the original
    cfg = dict(cfg)
    track_type = cfg.pop('type')

    if track_type not in track_classes:
        raise ValueError(f"Unknown track type: {track_type}")

    track_class = track_classes[track_type]

    # Handle path -> data_source
    if 'path' in cfg:
        cfg['data_source'] = cfg.pop('path')

    return track_class(**cfg)


if __name__ == '__main__':
    cli()
