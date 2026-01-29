"""Tests for GenomeFigure class."""

import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path

from chromoplot.core.figure import GenomeFigure
from chromoplot.core.coordinates import GenomeCoordinates
from chromoplot.tracks.ideogram import IdeogramTrack
from chromoplot.tracks.feature import FeatureTrack
from chromoplot.tracks.haplotype import HaplotypeTrack


class TestGenomeFigure:

    def test_init_with_fai(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        assert fig.coordinates.n_chromosomes == 3
        assert len(fig.regions) == 1

    def test_init_with_dict(self):
        fig = GenomeFigure({'chr1': 1000000}, region="chr1:0-500000")
        assert fig.coordinates.n_chromosomes == 1

    def test_init_with_coordinates(self, test_fai):
        coords = GenomeCoordinates.from_fai(test_fai)
        fig = GenomeFigure(coords, region="chr1:0-1000000")
        assert fig.coordinates is coords

    def test_init_whole_genome(self, test_fai):
        fig = GenomeFigure(test_fai)
        assert fig.is_whole_genome is True
        assert len(fig.regions) == 3

    def test_init_single_region(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        assert fig.is_whole_genome is False
        assert len(fig.regions) == 1

    def test_default_figsize(self, test_fai):
        # Whole genome gets wider figure
        fig_whole = GenomeFigure(test_fai)
        assert fig_whole.figsize[0] == 14

        # Single region gets narrower figure
        fig_region = GenomeFigure(test_fai, region="chr1:0-1000000")
        assert fig_region.figsize[0] == 12

    def test_custom_figsize(self, test_fai):
        fig = GenomeFigure(test_fai, figsize=(10, 5))
        assert fig.figsize == (10, 5)

    def test_add_track(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        track = IdeogramTrack()
        result = fig.add_track(track)

        assert fig.n_tracks == 1
        assert result is fig  # Method chaining

    def test_add_multiple_tracks(self, test_fai, test_bed):
        fig = GenomeFigure(test_fai, region="chr1:0-2000000")
        fig.add_track(IdeogramTrack())
        fig.add_track(FeatureTrack(test_bed))

        assert fig.n_tracks == 2

    def test_remove_track(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        track1 = IdeogramTrack()
        track2 = IdeogramTrack(label="Second")
        fig.add_track(track1)
        fig.add_track(track2)

        removed = fig.remove_track(0)
        assert removed is track1
        assert fig.n_tracks == 1

    def test_method_chaining(self, test_fai, test_bed):
        fig = (GenomeFigure(test_fai, region="chr1:0-2000000")
               .add_track(IdeogramTrack())
               .add_track(FeatureTrack(test_bed)))

        assert fig.n_tracks == 2

    def test_render(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        fig.add_track(IdeogramTrack())

        mpl_fig = fig.render()
        assert mpl_fig is not None
        assert isinstance(mpl_fig, plt.Figure)

        fig.close()

    def test_render_with_title(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000", title="Test Figure")
        fig.add_track(IdeogramTrack())

        mpl_fig = fig.render()
        assert fig.title == "Test Figure"

        fig.close()

    def test_save_pdf(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        fig.add_track(IdeogramTrack())

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            fig.save(temp_path)
            assert Path(temp_path).exists()
            assert Path(temp_path).stat().st_size > 0
        finally:
            Path(temp_path).unlink()
            fig.close()

    def test_save_png(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        fig.add_track(IdeogramTrack())

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            fig.save(temp_path, dpi=100)
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink()
            fig.close()

    def test_theme_selection(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000", theme='presentation')
        assert fig.theme.title_fontsize == 18

        fig2 = GenomeFigure(test_fai, region="chr1:0-1000000", theme='publication')
        assert fig2.theme.title_fontsize == 12

    def test_close(self, test_fai):
        fig = GenomeFigure(test_fai, region="chr1:0-1000000")
        fig.add_track(IdeogramTrack())
        fig.render()

        fig.close()
        assert fig._fig is None
        assert fig._axes == []


class TestIntegration:
    """Integration tests for complete figure creation."""

    def test_complete_figure(self, test_fai, test_bed, test_haplotypes):
        """Test creating a complete figure with multiple tracks."""
        fig = GenomeFigure(
            test_fai,
            region="chr1:0-10000000",
            title="Complete Test Figure"
        )

        fig.add_track(IdeogramTrack())
        fig.add_track(FeatureTrack(test_bed, label="Features"))
        fig.add_track(HaplotypeTrack(test_haplotypes, label="Haplotypes"))

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            fig.save(temp_path)
            assert Path(temp_path).exists()
        finally:
            Path(temp_path).unlink()
            fig.close()
