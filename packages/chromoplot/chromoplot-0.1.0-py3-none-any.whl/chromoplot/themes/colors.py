"""Color palettes and utilities."""

from __future__ import annotations

# Built-in palettes
PALETTES = {
    # For founder/haplotype coloring
    'founder_default': [
        '#e41a1c',  # Red
        '#377eb8',  # Blue
        '#4daf4a',  # Green
        '#984ea3',  # Purple
        '#ff7f00',  # Orange
        '#ffff33',  # Yellow
        '#a65628',  # Brown
        '#f781bf',  # Pink
    ],

    # For subgenome coloring
    'subgenome': [
        '#1b9e77',  # Teal
        '#d95f02',  # Orange
        '#7570b3',  # Purple
    ],

    # General categorical
    'categorical': [
        '#4e79a7',
        '#f28e2b',
        '#e15759',
        '#76b7b2',
        '#59a14f',
        '#edc948',
        '#b07aa1',
        '#ff9da7',
        '#9c755f',
        '#bab0ac',
    ],

    # Sequential (for continuous data)
    'sequential_blue': [
        '#f7fbff',
        '#deebf7',
        '#c6dbef',
        '#9ecae1',
        '#6baed6',
        '#4292c6',
        '#2171b5',
        '#08519c',
        '#08306b',
    ],

    # Diverging (for bidirectional data)
    'diverging_rdbu': [
        '#67001f',
        '#b2182b',
        '#d6604d',
        '#f4a582',
        '#fddbc7',
        '#f7f7f7',
        '#d1e5f0',
        '#92c5de',
        '#4393c3',
        '#2166ac',
        '#053061',
    ],

    # Maize NAM founder palettes (heterotic groups)
    'maize_heterotic': [
        '#FFC125',  # StiffStalk (B73)
        '#4169E1',  # NonStiffStalk
        '#787878',  # Mixed
        '#DA70D6',  # PopCorn
        '#FF4500',  # SweetCorn
        '#32CD32',  # Tropical
    ],
}

# Detailed mapping for NAM founders
MAIZE_NAM_COLORS = {
    # StiffStalk
    'B73': '#FFC125',
    'B73Ab10': '#FFC125',
    # NonStiffStalk
    'B97': '#4169E1',
    'Ky21': '#4169E1',
    'M162W': '#4169E1',
    'MS71': '#4169E1',
    'Oh7b': '#4169E1',
    'Oh43': '#4169E1',
    # Mixed
    'M37W': '#787878',
    'Mo18W': '#787878',
    'Tx303': '#787878',
    # PopCorn
    'HP301': '#DA70D6',
    # SweetCorn
    'IL14H': '#FF4500',
    'P39': '#FF4500',
    # Tropical
    'CML52': '#32CD32',
    'CML69': '#32CD32',
    'CML103': '#32CD32',
    'CML228': '#32CD32',
    'CML247': '#32CD32',
    'CML277': '#32CD32',
    'CML322': '#32CD32',
    'CML333': '#32CD32',
    'Ki3': '#32CD32',
    'Ki11': '#32CD32',
    'NC350': '#32CD32',
    'NC358': '#32CD32',
    'Tzi8': '#32CD32',
}


def get_palette(name: str, n: int | None = None) -> list[str]:
    """
    Get color palette by name.

    Parameters
    ----------
    name : str
        Palette name
    n : int, optional
        Number of colors needed. If more than available,
        colors will be interpolated.

    Returns
    -------
    list[str]
        List of hex color codes
    """
    if name not in PALETTES:
        raise ValueError(f"Unknown palette: {name}. Available: {list(PALETTES.keys())}")

    palette = PALETTES[name]

    if n is None or n <= len(palette):
        return palette[:n] if n else palette

    # Interpolate if more colors needed
    return _interpolate_palette(palette, n)


def _interpolate_palette(colors: list[str], n: int) -> list[str]:
    """Interpolate palette to n colors."""
    import numpy as np

    # Convert to RGB
    rgb_colors = [_hex_to_rgb(c) for c in colors]

    # Interpolate
    indices = np.linspace(0, len(colors) - 1, n)
    result = []

    for idx in indices:
        lower = int(np.floor(idx))
        upper = min(lower + 1, len(colors) - 1)
        frac = idx - lower

        r = int(rgb_colors[lower][0] * (1 - frac) + rgb_colors[upper][0] * frac)
        g = int(rgb_colors[lower][1] * (1 - frac) + rgb_colors[upper][1] * frac)
        b = int(rgb_colors[lower][2] * (1 - frac) + rgb_colors[upper][2] * frac)

        result.append(_rgb_to_hex((r, g, b)))

    return result


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def founder_colors(founders: list[str]) -> dict[str, str]:
    """
    Assign consistent colors to founder names.

    Parameters
    ----------
    founders : list[str]
        List of founder names

    Returns
    -------
    dict[str, str]
        Mapping of founder names to colors
    """
    palette = get_palette('founder_default', n=len(founders))
    return dict(zip(founders, palette))


def maize_nam_colors(founders: list[str]) -> dict[str, str]:
    """
    Get colors for maize NAM founders based on heterotic group.

    Parameters
    ----------
    founders : list[str]
        List of NAM founder names

    Returns
    -------
    dict[str, str]
        Mapping of founder names to colors
    """
    colors = {}
    fallback_palette = get_palette('founder_default')
    fallback_idx = 0

    for founder in founders:
        if founder in MAIZE_NAM_COLORS:
            colors[founder] = MAIZE_NAM_COLORS[founder]
        else:
            # Fallback for unknown founders
            colors[founder] = fallback_palette[fallback_idx % len(fallback_palette)]
            fallback_idx += 1

    return colors


def lighten(color: str, amount: float = 0.3) -> str:
    """
    Lighten a color.

    Parameters
    ----------
    color : str
        Hex color code
    amount : float
        Amount to lighten (0-1)

    Returns
    -------
    str
        Lightened hex color
    """
    rgb = _hex_to_rgb(color)
    new_rgb = tuple(int(c + (255 - c) * amount) for c in rgb)
    return _rgb_to_hex(new_rgb)


def darken(color: str, amount: float = 0.3) -> str:
    """
    Darken a color.

    Parameters
    ----------
    color : str
        Hex color code
    amount : float
        Amount to darken (0-1)

    Returns
    -------
    str
        Darkened hex color
    """
    rgb = _hex_to_rgb(color)
    new_rgb = tuple(int(c * (1 - amount)) for c in rgb)
    return _rgb_to_hex(new_rgb)
