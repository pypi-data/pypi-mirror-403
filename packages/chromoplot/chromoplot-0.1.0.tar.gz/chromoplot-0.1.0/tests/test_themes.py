"""Tests for theme and color system."""

import pytest
from chromoplot.themes.colors import (
    get_palette,
    founder_colors,
    maize_nam_colors,
    lighten,
    darken,
    MAIZE_NAM_COLORS,
)
from chromoplot.themes.theme import Theme, get_theme, register_theme


class TestColors:

    def test_get_palette(self):
        palette = get_palette('categorical')
        assert len(palette) == 10
        assert all(c.startswith('#') for c in palette)

    def test_get_palette_with_n(self):
        palette = get_palette('categorical', n=5)
        assert len(palette) == 5

    def test_get_palette_interpolate(self):
        palette = get_palette('categorical', n=20)
        assert len(palette) == 20

    def test_get_palette_unknown(self):
        with pytest.raises(ValueError):
            get_palette('unknown_palette')

    def test_founder_colors(self):
        founders = ['A', 'B', 'C']
        colors = founder_colors(founders)
        assert len(colors) == 3
        assert 'A' in colors
        assert all(c.startswith('#') for c in colors.values())

    def test_maize_nam_colors_known(self):
        founders = ['B73', 'Mo17', 'CML103']
        colors = maize_nam_colors(founders)
        assert colors['B73'] == MAIZE_NAM_COLORS['B73']

    def test_maize_nam_colors_unknown(self):
        founders = ['B73', 'UnknownFounder']
        colors = maize_nam_colors(founders)
        assert 'B73' in colors
        assert 'UnknownFounder' in colors
        # Unknown should get a fallback color
        assert colors['UnknownFounder'].startswith('#')

    def test_lighten(self):
        color = '#000000'
        lightened = lighten(color, 0.5)
        assert lightened != color
        # Should be lighter (higher values)
        assert lightened == '#7f7f7f'

    def test_darken(self):
        color = '#ffffff'
        darkened = darken(color, 0.5)
        assert darkened != color
        # Should be darker (lower values)
        assert darkened == '#7f7f7f'


class TestTheme:

    def test_default_theme(self):
        theme = Theme()
        assert theme.figure_facecolor == 'white'
        assert theme.font_family == 'sans-serif'

    def test_custom_theme(self):
        theme = Theme(figure_facecolor='black', title_fontsize=20)
        assert theme.figure_facecolor == 'black'
        assert theme.title_fontsize == 20

    def test_get_theme(self):
        theme = get_theme('publication')
        assert theme.figure_facecolor == 'white'

        theme = get_theme('dark')
        assert theme.figure_facecolor == '#1a1a1a'

    def test_get_theme_unknown(self):
        with pytest.raises(ValueError):
            get_theme('unknown_theme')

    def test_register_theme(self):
        custom = Theme(figure_facecolor='pink')
        register_theme('pink_theme', custom)

        retrieved = get_theme('pink_theme')
        assert retrieved.figure_facecolor == 'pink'

    def test_presentation_theme(self):
        theme = get_theme('presentation')
        # Should have larger fonts than publication
        pub = get_theme('publication')
        assert theme.title_fontsize > pub.title_fontsize
        assert theme.label_fontsize > pub.label_fontsize
