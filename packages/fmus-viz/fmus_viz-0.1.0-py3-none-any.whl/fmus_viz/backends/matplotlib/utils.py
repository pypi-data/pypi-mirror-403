from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union

from fmus_viz.core.config import get_config


def setup_matplotlib_style(theme: Optional[str] = None) -> None:
    """
    Set up Matplotlib style based on theme.

    Args:
        theme: Name of the theme to use, or None for the default
    """
    if theme is None:
        theme = get_config('theme', 'matplotlib')

    if theme == 'default':
        # Gunakan style default
        plt.style.use('default')
    else:
        # Coba gunakan style yang ditentukan
        try:
            plt.style.use(theme)
        except Exception:
            # Jika style tidak tersedia, gunakan default
            plt.style.use('default')


def create_figure(
    figsize: Optional[Tuple[float, float]] = None,
    dpi: Optional[int] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a Matplotlib figure and axes with the given size and dpi.

    Args:
        figsize: Figure size (width, height) in inches, or None for default
        dpi: Dots per inch, or None for default

    Returns:
        Tuple of (figure, axes)
    """
    if figsize is None:
        figsize = get_config('figsize', 'matplotlib')

    if dpi is None:
        dpi = get_config('dpi', 'matplotlib')

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    return fig, ax


def apply_figure_styling(
    fig: plt.Figure,
    ax: plt.Axes,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    show_grid: bool = True,
    show_legend: bool = True,
    **kwargs
) -> None:
    """
    Apply styling to a Matplotlib figure and axes.

    Args:
        fig: Figure to style
        ax: Axes to style
        title: Title text, or None for no title
        xlabel: X-axis label, or None for no label
        ylabel: Y-axis label, or None for no label
        show_grid: Whether to show the grid
        show_legend: Whether to show the legend
        **kwargs: Additional styling options
    """
    # Judul
    if title is not None:
        title_size = kwargs.get('title_size', get_config('title_size', 'matplotlib'))
        ax.set_title(title, fontsize=title_size)

    # Label sumbu
    if xlabel is not None:
        label_size = kwargs.get('label_size', get_config('label_size', 'matplotlib'))
        ax.set_xlabel(xlabel, fontsize=label_size)

    if ylabel is not None:
        label_size = kwargs.get('label_size', get_config('label_size', 'matplotlib'))
        ax.set_ylabel(ylabel, fontsize=label_size)

    # Grid
    ax.grid(show_grid)

    # Legend
    if show_legend and ax.get_legend_handles_labels()[0]:
        legend_loc = kwargs.get('legend_loc', get_config('legend_loc', 'matplotlib'))
        ax.legend(loc=legend_loc)

    # Ukuran tick
    tick_size = kwargs.get('tick_size', get_config('tick_size', 'matplotlib'))
    ax.tick_params(axis='both', which='major', labelsize=tick_size)


def save_figure(
    fig: plt.Figure,
    filename: str,
    dpi: Optional[int] = None,
    **kwargs
) -> None:
    """
    Save a Matplotlib figure to a file.

    Args:
        fig: Figure to save
        filename: Path to save the figure
        dpi: Dots per inch, or None for default
        **kwargs: Additional save options
    """
    if dpi is None:
        dpi = get_config('dpi', 'matplotlib')

    save_kwargs = {
        'dpi': dpi,
        'bbox_inches': 'tight'
    }
    save_kwargs.update(kwargs)

    fig.savefig(filename, **save_kwargs)


def get_colormap(cmap_name: Optional[str] = None) -> Any:
    """
    Get a Matplotlib colormap.

    Args:
        cmap_name: Name of the colormap, or None for default

    Returns:
        Matplotlib colormap
    """
    if cmap_name is None:
        cmap_name = get_config('cmap', 'matplotlib')

    return plt.cm.get_cmap(cmap_name)


def convert_categorical_x(
    x_data: np.ndarray,
    ax: plt.Axes
) -> np.ndarray:
    """
    Convert categorical x-data for plotting.

    Args:
        x_data: X-axis data
        ax: Axes to update

    Returns:
        Converted x data (numerical)
    """
    if not isinstance(x_data[0], (str, bytes)):
        return x_data

    # Jika data adalah string, konversi ke indeks numerik
    categories = list(dict.fromkeys(x_data))  # Hapus duplikat tapi pertahankan urutan
    x_numeric = np.array([categories.index(x) for x in x_data])

    # Set ticks and labels
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories)

    return x_numeric
