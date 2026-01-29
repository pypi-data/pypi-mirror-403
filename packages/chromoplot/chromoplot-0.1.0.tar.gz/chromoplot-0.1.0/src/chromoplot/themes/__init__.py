"""Theme and color management for consistent styling."""

from .colors import get_palette, founder_colors, maize_nam_colors, lighten, darken
from .theme import Theme, get_theme, register_theme

__all__ = [
    'get_palette',
    'founder_colors',
    'maize_nam_colors',
    'lighten',
    'darken',
    'Theme',
    'get_theme',
    'register_theme',
]
