from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from fmus_viz.core.config import get_config


def setup_seaborn_style(style: Optional[str] = None, context: Optional[str] = None) -> None:
    """
    Set up Seaborn style based on theme.

    Args:
        style: Name of the style to use
        context: Name of the context (paper, notebook, talk, poster)
    """
    if style is None:
        style = get_config('style', 'seaborn')

    if context is None:
        context = get_config('context', 'seaborn')

    # Apply seaborn style
    if style:
        sns.set_style(style)

    if context:
        sns.set_context(context)


def create_figure(
    figsize: Optional[Tuple[float, float]] = None,
    dpi: Optional[int] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a Matplotlib figure with Seaborn styling.

    Args:
        figsize: Figure size (width, height) in inches
        dpi: Dots per inch

    Returns:
        Tuple of (figure, axes)
    """
    setup_seaborn_style()

    if figsize is None:
        figsize = get_config('figsize', 'seaborn')

    if dpi is None:
        dpi = get_config('dpi', 'seaborn')

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    return fig, ax


def get_default_palette() -> List[str]:
    """
    Get the default Seaborn color palette.

    Returns:
        List of color hex codes
    """
    palette = get_config('palette', 'seaborn')
    if palette:
        return sns.color_palette(palette).as_hex()
    return sns.color_palette().as_hex()


def get_palette(n_colors: int, palette: Optional[str] = None) -> List[str]:
    """
    Get a Seaborn color palette with specified number of colors.

    Args:
        n_colors: Number of colors to get
        palette: Name of the palette

    Returns:
        List of color hex codes
    """
    if palette is None:
        palette = get_config('palette', 'seaborn')

    return sns.color_palette(palette, n_colors).as_hex()
