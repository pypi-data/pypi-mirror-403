# Changelog

All notable changes to Chromoplot will be documented in this file.

## [0.1.0] - 2025-01-26

### Added

- Core visualization framework with GenomeFigure class
- Coordinate system and region handling
- Track types:
  - IdeogramTrack - chromosome backbone
  - FeatureTrack - BED features
  - GeneTrack - gene models with exon/intron structure
  - HaplotypeTrack - haplotype blocks
  - AlignmentTrack - PAF alignments
  - DepthTrack - BAM/bedGraph coverage
  - SignalTrack - continuous data
  - VariantTrack - VCF visualization
  - SyntenyTrack - synteny ribbons
  - ScaleBarTrack - scale reference
  - AnnotationTrack - text labels
- Layouts:
  - GenomeLayout - whole-genome grid
  - ComparativeLayout - two-genome synteny
- Theme system with publication/presentation presets
- Color palettes including maize NAM heterotic groups
- CLI commands: plot, genome, comparative, from-config
- I/O parsers: FAI, BED, GFF, PAF, synteny formats
