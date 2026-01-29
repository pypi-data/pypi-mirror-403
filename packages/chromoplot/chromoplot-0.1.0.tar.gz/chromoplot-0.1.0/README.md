# Chromoplot

Flexible genome visualization toolkit for publication-ready figures.

## Features

- **Track-based composition**: Stack multiple data types vertically
- **Format-agnostic**: BED, GFF, PAF, BAM, VCF, bedGraph, bigWig
- **Multiple layouts**: Single region, whole genome, comparative synteny
- **Publication-ready**: Clean defaults optimized for print
- **Fully customizable**: Themes, colors, and per-track styling

## Installation

```bash
pip install chromoplot

# With optional dependencies for BAM/bigWig support
pip install chromoplot[full]
```

## Quick Start

### Single Region

```python
import chromoplot as cp

fig = cp.GenomeFigure("genome.fa.fai", region="chr1:1-10000000")
fig.add_track(cp.IdeogramTrack())
fig.add_track(cp.GeneTrack("genes.gff3", label="Genes"))
fig.add_track(cp.HaplotypeTrack("haplotypes.bed", label="Haplotypes"))
fig.add_track(cp.ScaleBarTrack())
fig.save("figure.pdf")
```

### Whole Genome

```python
import chromoplot as cp

coords = cp.GenomeCoordinates.from_fai("genome.fa.fai")
layout = cp.GenomeLayout(coords, arrangement='grid', n_cols=5)
layout.add_track(cp.IdeogramTrack())
layout.add_track(cp.HaplotypeTrack("haplotypes.bed"))
layout.save("genome_wide.pdf")
```

### Comparative Synteny

```python
import chromoplot as cp

ref_coords = cp.GenomeCoordinates.from_fai("ref.fa.fai")
query_coords = cp.GenomeCoordinates.from_fai("query.fa.fai")

layout = cp.ComparativeLayout(
    ref_coords, query_coords,
    ref_region="chr1", query_region="chr1"
)
layout.add_ref_track(cp.IdeogramTrack())
layout.add_ref_track(cp.GeneTrack("ref_genes.gff3"))
layout.add_synteny_track(cp.SyntenyTrack("alignment.paf"))
layout.add_query_track(cp.GeneTrack("query_genes.gff3"))
layout.add_query_track(cp.IdeogramTrack())
layout.save("synteny.pdf")
```

## Command Line

```bash
# Single region plot
chromoplot plot -r genome.fa.fai --region chr1:1-10000000 \
    --gff genes.gff3 --haplotypes haplotypes.bed -o figure.pdf

# Whole genome plot
chromoplot genome -r genome.fa.fai --haplotypes haplotypes.bed -o genome.pdf

# Comparative synteny plot
chromoplot comparative --ref-fai ref.fa.fai --query-fai query.fa.fai \
    --synteny alignment.paf --ref-region chr1 --query-region chr1 -o synteny.pdf

# From YAML config
chromoplot from-config config.yaml -o figure.pdf
```

## Available Tracks

| Track | Description | Input Formats |
|-------|-------------|---------------|
| `IdeogramTrack` | Chromosome backbone | (none) |
| `GeneTrack` | Gene models with exons | GFF3, GTF |
| `FeatureTrack` | Generic features | BED |
| `HaplotypeTrack` | Haplotype blocks | BED (phaser output) |
| `AlignmentTrack` | Sequence alignments | PAF |
| `DepthTrack` | Read coverage | BAM, bedGraph, bigWig |
| `SignalTrack` | Continuous signal | bedGraph, bigWig |
| `VariantTrack` | Variant positions | VCF |
| `SyntenyTrack` | Synteny ribbons | PAF, SyRI, MCScanX |
| `ScaleBarTrack` | Scale reference | (none) |
| `AnnotationTrack` | Text labels | TSV |

## Themes

```python
# Built-in themes
fig = cp.GenomeFigure(..., theme='publication')  # Default
fig = cp.GenomeFigure(..., theme='presentation')
fig = cp.GenomeFigure(..., theme='minimal')
fig = cp.GenomeFigure(..., theme='dark')

# Custom theme
my_theme = cp.Theme(
    figure_facecolor='white',
    title_fontsize=14,
    label_fontsize=10,
)
cp.register_theme('my_theme', my_theme)
```

## Color Palettes

```python
# Get palette
colors = cp.get_palette('categorical', n=5)
colors = cp.get_palette('founder_default')
colors = cp.get_palette('maize_heterotic')

# Founder colors for haplotype tracks
color_map = cp.founder_colors(['B73', 'Mo17', 'W22'])

# Maize NAM colors (by heterotic group)
color_map = cp.maize_nam_colors(['B73', 'Mo17', 'CML247'])
```

## License

MIT License
