"""Tests for comparative visualization components."""

import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

from chromoplot.io.synteny import (
    read_synteny, write_synteny_bed, SyntenyBlock,
    _read_bed_synteny, _read_paf_synteny
)
from chromoplot.tracks.synteny import SyntenyTrack
from chromoplot.tracks.scale import ScaleBarTrack
from chromoplot.tracks.annotation import AnnotationTrack, Annotation
from chromoplot.layouts.comparative import ComparativeLayout
from chromoplot.core.regions import Region
from chromoplot.core.coordinates import GenomeCoordinates


class TestSyntenyBlock:

    def test_init(self):
        block = SyntenyBlock(
            ref_chrom="chr1",
            ref_start=1000,
            ref_end=2000,
            query_chrom="chr1",
            query_start=1000,
            query_end=2000,
        )
        assert block.ref_chrom == "chr1"
        assert block.ref_length == 1000
        assert block.query_length == 1000
        assert block.orientation == '+'

    def test_inverted_block(self):
        block = SyntenyBlock(
            ref_chrom="chr1",
            ref_start=1000,
            ref_end=2000,
            query_chrom="chr1",
            query_start=3000,
            query_end=2000,
            orientation='-',
        )
        assert block.orientation == '-'
        assert block.query_length == -1000


class TestReadSynteny:

    def test_read_bed_format(self, test_synteny):
        blocks = read_synteny(test_synteny, format='bed')
        assert len(blocks) == 4
        assert blocks[0].ref_chrom == "chr1"
        assert blocks[0].ref_start == 1000000
        assert blocks[0].ref_end == 2000000

    def test_read_auto_detect(self, test_synteny):
        blocks = read_synteny(test_synteny)
        assert len(blocks) == 4

    def test_read_with_min_length(self, test_synteny):
        blocks = read_synteny(test_synteny, min_length=500000)
        # All test blocks are 1000000 bp
        assert len(blocks) == 4

    def test_read_with_min_length_filter(self, test_synteny):
        blocks = read_synteny(test_synteny, min_length=2000000)
        # No blocks are 2Mb
        assert len(blocks) == 0

    def test_read_paf_format(self, test_paf):
        blocks = read_synteny(test_paf, format='paf')
        assert len(blocks) > 0
        # PAF uses target as ref
        block = blocks[0]
        assert block.ref_chrom == "chr1"


class TestWriteSynteny:

    def test_write_bed(self, test_synteny, tmp_path):
        blocks = read_synteny(test_synteny)
        output = tmp_path / "output.bed"
        write_synteny_bed(blocks, output)

        # Read back
        reloaded = read_synteny(output, format='bed')
        assert len(reloaded) == len(blocks)


class TestSyntenyTrack:

    def test_init(self, test_synteny):
        track = SyntenyTrack(test_synteny)
        assert track.height == 2.0
        assert track.format == 'auto'

    def test_default_style(self, test_synteny):
        track = SyntenyTrack(test_synteny)
        assert 'forward_color' in track.style
        assert 'reverse_color' in track.style
        assert 'ribbon_style' in track.style

    def test_load_data(self, test_synteny, test_fai):
        track = SyntenyTrack(test_synteny)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)
        assert len(track._blocks) == 4

    def test_render_between(self, test_synteny, test_fai):
        track = SyntenyTrack(test_synteny)
        coords = GenomeCoordinates.from_fai(test_fai)
        ref_region = Region("chr1", 0, 10000000)
        query_region = Region("chr1", 0, 10000000)

        track.load_data(ref_region)

        fig, ax = plt.subplots()
        track.render_between(
            ax, ref_region, query_region,
            ref_y=1.0, query_y=0.0,
            ref_coords=coords, query_coords=coords
        )
        plt.close(fig)

    def test_ribbon_styles(self, test_synteny, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        ref_region = Region("chr1", 0, 10000000)
        query_region = Region("chr1", 0, 10000000)

        for style in ['straight', 'bezier', 'arc']:
            track = SyntenyTrack(test_synteny, style={'ribbon_style': style})
            track.load_data(ref_region)

            fig, ax = plt.subplots()
            track.render_between(
                ax, ref_region, query_region,
                ref_y=1.0, query_y=0.0,
                ref_coords=coords, query_coords=coords
            )
            plt.close(fig)


class TestScaleBarTrack:

    def test_init(self):
        track = ScaleBarTrack()
        assert track.height == 0.3
        assert track.bar_length is None

    def test_init_with_length(self):
        track = ScaleBarTrack(length=1000000)
        assert track.bar_length == 1000000

    def test_default_style(self):
        track = ScaleBarTrack()
        assert 'bar_color' in track.style
        assert 'bar_linewidth' in track.style

    def test_load_data_auto_length(self):
        track = ScaleBarTrack()
        region = Region("chr1", 0, 10000000)
        track.load_data(region)
        # Should auto-calculate
        assert track.bar_length == 1000000  # 15% of 10Mb -> rounds to 1Mb

    def test_render(self, test_fai):
        track = ScaleBarTrack()
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)

        fig, ax = plt.subplots()
        track.render(ax, [region], coords)
        plt.close(fig)

    def test_format_length(self):
        track = ScaleBarTrack()
        assert track._format_length(1000000) == "1 Mb"
        assert track._format_length(500000) == "500 kb"
        assert track._format_length(500) == "500 bp"


class TestAnnotationTrack:

    def test_init_from_list(self):
        annotations = [
            Annotation(chrom="chr1", position=1000, label="A"),
            Annotation(chrom="chr1", position=2000, label="B"),
        ]
        track = AnnotationTrack(annotations)
        assert track.height == 0.5

    def test_init_from_file(self, test_annotations):
        track = AnnotationTrack(test_annotations)
        assert track.height == 0.5

    def test_default_style(self, test_annotations):
        track = AnnotationTrack(test_annotations)
        assert 'text_color' in track.style
        assert 'marker' in track.style
        assert 'show_line' in track.style

    def test_load_data_from_list(self):
        annotations = [
            Annotation(chrom="chr1", position=1000, label="A"),
            Annotation(chrom="chr1", position=2000, label="B"),
            Annotation(chrom="chr2", position=1000, label="C"),
        ]
        track = AnnotationTrack(annotations)
        region = Region("chr1", 0, 10000)
        track.load_data(region)
        assert len(track._annotations) == 2

    def test_load_data_from_file(self, test_annotations):
        track = AnnotationTrack(test_annotations)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)
        assert len(track._annotations) == 3

    def test_render(self, test_annotations, test_fai):
        track = AnnotationTrack(test_annotations)
        coords = GenomeCoordinates.from_fai(test_fai)
        region = Region("chr1", 0, 10000000)
        track.load_data(region)

        fig, ax = plt.subplots()
        track.render(ax, [region], coords)
        plt.close(fig)


class TestComparativeLayout:

    def test_init(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        layout = ComparativeLayout(coords, coords)
        assert layout.figsize == (14, 10)

    def test_init_with_regions(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        layout = ComparativeLayout(
            coords, coords,
            ref_region="chr1:0-5000000",
            query_region="chr1:0-5000000"
        )
        assert layout.ref_region.end == 5000000

    def test_add_tracks(self, test_fai, test_synteny):
        from chromoplot.tracks.ideogram import IdeogramTrack

        coords = GenomeCoordinates.from_fai(test_fai)
        layout = ComparativeLayout(coords, coords)

        layout.add_ref_track(IdeogramTrack())
        layout.add_synteny_track(SyntenyTrack(test_synteny))
        layout.add_query_track(IdeogramTrack())

        assert len(layout._ref_tracks) == 1
        assert layout._synteny_track is not None
        assert len(layout._query_tracks) == 1

    def test_render(self, test_fai, test_synteny):
        from chromoplot.tracks.ideogram import IdeogramTrack

        coords = GenomeCoordinates.from_fai(test_fai)
        layout = ComparativeLayout(
            coords, coords,
            ref_region="chr1",
            query_region="chr1"
        )

        layout.add_ref_track(IdeogramTrack())
        layout.add_synteny_track(SyntenyTrack(test_synteny))
        layout.add_query_track(IdeogramTrack())

        fig = layout.render()
        assert fig is not None
        plt.close(fig)

    def test_save(self, test_fai, test_synteny, tmp_path):
        from chromoplot.tracks.ideogram import IdeogramTrack

        coords = GenomeCoordinates.from_fai(test_fai)
        layout = ComparativeLayout(coords, coords)

        layout.add_ref_track(IdeogramTrack())
        layout.add_synteny_track(SyntenyTrack(test_synteny))
        layout.add_query_track(IdeogramTrack())

        output = tmp_path / "test.png"
        layout.save(str(output))
        assert output.exists()
