"""Tests for track classes."""

import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

from chromoplot.tracks.base import BaseTrack
from chromoplot.tracks.ideogram import IdeogramTrack
from chromoplot.tracks.feature import FeatureTrack
from chromoplot.tracks.haplotype import HaplotypeTrack
from chromoplot.core.regions import Region
from chromoplot.core.coordinates import GenomeCoordinates


class TestBaseTrack:

    def test_abstract_class(self):
        # Can't instantiate abstract class
        with pytest.raises(TypeError):
            BaseTrack()


class TestIdeogramTrack:

    def test_init(self):
        track = IdeogramTrack()
        assert track.height == 0.5
        assert track.label is None

    def test_init_with_label(self):
        track = IdeogramTrack(label="Chromosome")
        assert track.label == "Chromosome"

    def test_default_style(self):
        track = IdeogramTrack()
        assert 'backbone_color' in track.style
        assert 'backbone_height' in track.style

    def test_custom_style(self):
        track = IdeogramTrack(style={'backbone_color': 'blue'})
        assert track.style['backbone_color'] == 'blue'
        # Should still have other defaults
        assert 'backbone_height' in track.style

    def test_render(self, test_fai):
        track = IdeogramTrack()
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 10000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)

        plt.close(fig)


class TestFeatureTrack:

    def test_init(self, test_bed):
        track = FeatureTrack(test_bed, label="Features")
        assert track.label == "Features"
        assert track.height == 1.0

    def test_load_data(self, test_bed):
        track = FeatureTrack(test_bed)
        region = Region("chr1", 0, 2000000)
        track.load_data(region)

        assert track._data is not None
        assert len(track._data) == 3

    def test_load_data_filtered(self, test_bed):
        track = FeatureTrack(test_bed)
        region = Region("chr1", 0, 300000)
        track.load_data(region)

        assert len(track._data) == 1

    def test_render(self, test_bed, test_fai):
        track = FeatureTrack(test_bed)
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 2000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)

        plt.close(fig)

    def test_custom_color(self, test_bed):
        track = FeatureTrack(test_bed, color="red")
        assert track.color == "red"


class TestHaplotypeTrack:

    def test_init(self, test_haplotypes):
        track = HaplotypeTrack(test_haplotypes, label="Haplotypes")
        assert track.label == "Haplotypes"

    def test_init_with_founders(self, test_haplotypes):
        track = HaplotypeTrack(test_haplotypes, founders=["B73", "Mo17"])
        assert track.founders == ["B73", "Mo17"]

    def test_load_data(self, test_haplotypes):
        track = HaplotypeTrack(test_haplotypes)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)

        assert track._data is not None
        assert len(track._data) == 3
        assert track._color_map is not None

    def test_color_map_built(self, test_haplotypes):
        track = HaplotypeTrack(test_haplotypes)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)

        assert 'B73' in track._color_map
        assert 'Mo17' in track._color_map

    def test_render(self, test_haplotypes, test_fai):
        track = HaplotypeTrack(test_haplotypes)
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 10000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)

        plt.close(fig)

    def test_default_style(self, test_haplotypes):
        track = HaplotypeTrack(test_haplotypes)
        assert 'block_height' in track.style
        assert 'show_legend' in track.style
        assert track.style['show_legend'] is True


# Tests for advanced tracks

from chromoplot.tracks.gene import GeneTrack
from chromoplot.tracks.alignment import AlignmentTrack
from chromoplot.tracks.depth import DepthTrack
from chromoplot.tracks.signal import SignalTrack
from chromoplot.tracks.variant import VariantTrack


class TestGeneTrack:

    def test_init(self, test_gff):
        track = GeneTrack(test_gff)
        assert track.height == 1.5
        assert track.mode == 'squish'

    def test_default_style(self, test_gff):
        track = GeneTrack(test_gff)
        style = track.default_style()
        assert 'exon_color' in style
        assert 'cds_color' in style
        assert 'utr_color' in style

    def test_custom_style(self, test_gff):
        track = GeneTrack(test_gff, style={'exon_color': 'red'})
        assert track.style['exon_color'] == 'red'
        assert 'cds_color' in track.style

    def test_load_data(self, test_gff):
        track = GeneTrack(test_gff)
        region = Region("chr1", 0, 2000000)
        track.load_data(region)
        # May have genes loaded depending on test data
        assert isinstance(track._genes, list)

    def test_render_empty(self, test_gff, test_fai):
        track = GeneTrack(test_gff)
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 90000000, 100000000)  # Region with no genes

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)


class TestAlignmentTrack:

    def test_init(self, test_paf):
        track = AlignmentTrack(test_paf)
        assert track.height == 1.5
        assert track.color_by == 'identity'

    def test_default_style(self, test_paf):
        track = AlignmentTrack(test_paf)
        style = track.default_style()
        assert 'forward_color' in style
        assert 'reverse_color' in style
        assert 'identity_cmap' in style

    def test_color_by_options(self, test_paf):
        track = AlignmentTrack(test_paf, color_by='strand')
        assert track.color_by == 'strand'

        track = AlignmentTrack(test_paf, color_by='query')
        assert track.color_by == 'query'

    def test_load_data(self, test_paf):
        track = AlignmentTrack(test_paf, min_length=0)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)
        assert len(track._alignments) == 3

    def test_render(self, test_paf, test_fai):
        track = AlignmentTrack(test_paf, min_length=0)
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 10000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)


class TestSignalTrack:

    def test_init(self, test_bedgraph):
        track = SignalTrack(test_bedgraph)
        assert track.height == 1.0
        assert track.plot_type == 'fill'

    def test_default_style(self, test_bedgraph):
        track = SignalTrack(test_bedgraph)
        style = track.default_style()
        assert 'fill_color' in style
        assert 'cmap' in style

    def test_load_data(self, test_bedgraph):
        track = SignalTrack(test_bedgraph)
        region = Region("chr1", 0, 1000000)
        track.load_data(region)
        assert track._positions is not None
        assert track._values is not None
        assert len(track._positions) == 10

    def test_render_fill(self, test_bedgraph, test_fai):
        track = SignalTrack(test_bedgraph, plot_type='fill')
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 1000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)

    def test_render_line(self, test_bedgraph, test_fai):
        track = SignalTrack(test_bedgraph, plot_type='line')
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 1000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)


class TestVariantTrack:

    def test_init(self, test_vcf):
        track = VariantTrack(test_vcf)
        assert track.height == 0.5
        assert track.plot_type == 'ticks'

    def test_default_style(self, test_vcf):
        track = VariantTrack(test_vcf)
        style = track.default_style()
        assert 'snp_color' in style
        assert 'indel_color' in style

    def test_load_data(self, test_vcf):
        track = VariantTrack(test_vcf)
        region = Region("chr1", 0, 1000000)
        track.load_data(region)
        assert len(track._positions) == 8
        assert 'snp' in track._variant_types
        assert 'indel' in track._variant_types

    def test_render_ticks(self, test_vcf, test_fai):
        track = VariantTrack(test_vcf, plot_type='ticks')
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 1000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)

    def test_render_density(self, test_vcf, test_fai):
        track = VariantTrack(test_vcf, plot_type='density')
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 1000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)

    def test_render_lollipop(self, test_vcf, test_fai):
        track = VariantTrack(test_vcf, plot_type='lollipop')
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 1000000)

        fig, ax = plt.subplots()
        track.load_data(region)
        track.render(ax, [region], coords)
        plt.close(fig)


class TestGenomeLayout:

    def test_creation(self, test_fai):
        from chromoplot.layouts.genome import GenomeLayout

        coords = GenomeCoordinates.from_fai(test_fai)
        layout = GenomeLayout(coords)
        assert layout.n_cols > 0
        assert layout.arrangement == 'grid'

    def test_add_track(self, test_fai):
        from chromoplot.layouts.genome import GenomeLayout

        coords = GenomeCoordinates.from_fai(test_fai)
        layout = GenomeLayout(coords)
        layout.add_track(IdeogramTrack())
        assert len(layout._tracks) == 1

    def test_render(self, test_fai):
        from chromoplot.layouts.genome import GenomeLayout

        coords = GenomeCoordinates.from_fai(test_fai)
        layout = GenomeLayout(coords, n_cols=2)
        layout.add_track(IdeogramTrack())

        fig = layout.render()
        assert fig is not None
        plt.close(fig)
