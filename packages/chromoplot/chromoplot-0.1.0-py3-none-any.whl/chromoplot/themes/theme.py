"""Theme definitions for consistent styling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Theme:
    """
    Complete theme specification.

    Controls all visual aspects of the figure for consistent styling.
    """
    # Figure
    figure_facecolor: str = 'white'

    # Fonts
    font_family: str = 'sans-serif'
    title_fontsize: int = 14
    label_fontsize: int = 10
    tick_fontsize: int = 8

    # Axes
    spine_color: str = '#333333'
    spine_width: float = 0.5

    # Grid
    grid_color: str = '#eeeeee'
    grid_width: float = 0.5
    show_grid: bool = False

    # Tracks
    default_track_height: float = 1.0
    track_spacing: float = 0.1


# Built-in themes
THEMES = {
    'publication': Theme(
        figure_facecolor='white',
        font_family='sans-serif',
        title_fontsize=12,
        label_fontsize=10,
        tick_fontsize=8,
        spine_color='#333333',
        spine_width=0.5,
    ),

    'presentation': Theme(
        figure_facecolor='white',
        font_family='sans-serif',
        title_fontsize=18,
        label_fontsize=14,
        tick_fontsize=12,
        spine_color='#333333',
        spine_width=1.0,
    ),

    'minimal': Theme(
        figure_facecolor='white',
        spine_color='#cccccc',
        spine_width=0.25,
        show_grid=False,
    ),

    'dark': Theme(
        figure_facecolor='#1a1a1a',
        font_family='sans-serif',
        spine_color='#666666',
        grid_color='#333333',
    ),
}


def get_theme(name: str) -> Theme:
    """
    Get theme by name.

    Parameters
    ----------
    name : str
        Theme name

    Returns
    -------
    Theme
    """
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}. Available: {list(THEMES.keys())}")
    return THEMES[name]


def register_theme(name: str, theme: Theme) -> None:
    """
    Register a custom theme.

    Parameters
    ----------
    name : str
        Theme name
    theme : Theme
        Theme object
    """
    THEMES[name] = theme
