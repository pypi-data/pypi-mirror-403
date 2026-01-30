from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union

from fmus_viz.core.config import get_config


def setup_plotly_template(template: Optional[str] = None) -> None:
    """
    Set up Plotly template.

    Args:
        template: Name of the template to use, or None for the default
    """
    if template is None:
        template = get_config('template', 'plotly')

    # Set default template
    if template and template != 'default':
        try:
            pio.templates.default = template
        except Exception:
            # Jika template tidak tersedia, gunakan default
            pio.templates.default = 'plotly_white'


def create_figure(
    width: Optional[int] = None,
    height: Optional[int] = None,
    **kwargs
) -> go.Figure:
    """
    Create a Plotly figure.

    Args:
        width: Figure width in pixels, or None for default
        height: Figure height in pixels, or None for default
        **kwargs: Additional figure parameters

    Returns:
        Plotly Figure
    """
    # Dapatkan konfigurasi default
    if width is None or height is None:
        figsize = get_config('figsize', 'plotly')
        dpi = get_config('dpi', 'plotly')

        if width is None:
            # Konversi inch ke pixel menggunakan dpi
            width = int(figsize[0] * dpi)

        if height is None:
            # Konversi inch ke pixel menggunakan dpi
            height = int(figsize[1] * dpi)

    # Buat figur
    fig = go.Figure()

    # Atur ukuran
    fig.update_layout(
        width=width,
        height=height,
        **kwargs
    )

    return fig


def apply_figure_styling(
    fig: go.Figure,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    show_grid: bool = True,
    show_legend: bool = True,
    **kwargs
) -> None:
    """
    Apply styling to a Plotly figure.

    Args:
        fig: Figure to style
        title: Title text, or None for no title
        xlabel: X-axis label, or None for no label
        ylabel: Y-axis label, or None for no label
        show_grid: Whether to show the grid
        show_legend: Whether to show the legend
        **kwargs: Additional styling options
    """
    # Tema
    theme = kwargs.get('theme', get_config('theme', 'plotly'))
    if theme and theme != 'default':
        try:
            fig.update_layout(template=theme)
        except Exception:
            # Jika template tidak tersedia, gunakan default
            pass

    # Layout updates
    layout_updates = {}

    # Judul
    if title is not None:
        title_size = kwargs.get('title_size', get_config('title_size', 'plotly'))
        layout_updates['title'] = {
            'text': title,
            'font': {'size': title_size}
        }

    # Label sumbu
    axis_updates = {}

    if xlabel is not None:
        label_size = kwargs.get('label_size', get_config('label_size', 'plotly'))
        axis_updates['xaxis'] = {
            'title': {
                'text': xlabel,
                'font': {'size': label_size}
            }
        }

    if ylabel is not None:
        label_size = kwargs.get('label_size', get_config('label_size', 'plotly'))
        axis_updates['yaxis'] = {
            'title': {
                'text': ylabel,
                'font': {'size': label_size}
            }
        }

    # Grid
    if show_grid:
        x_grid = axis_updates.get('xaxis', {})
        x_grid['showgrid'] = True
        axis_updates['xaxis'] = x_grid

        y_grid = axis_updates.get('yaxis', {})
        y_grid['showgrid'] = True
        axis_updates['yaxis'] = y_grid

    # Legend
    layout_updates['showlegend'] = show_legend

    # Font size untuk ticks
    tick_size = kwargs.get('tick_size', get_config('tick_size', 'plotly'))
    if 'xaxis' in axis_updates:
        axis_updates['xaxis']['tickfont'] = {'size': tick_size}
    else:
        axis_updates['xaxis'] = {'tickfont': {'size': tick_size}}

    if 'yaxis' in axis_updates:
        axis_updates['yaxis']['tickfont'] = {'size': tick_size}
    else:
        axis_updates['yaxis'] = {'tickfont': {'size': tick_size}}

    # Gabungkan semua updates
    layout_updates.update(axis_updates)

    # Terapkan styling
    fig.update_layout(**layout_updates)


def get_color_sequence(n_colors: int, colorscale: Optional[str] = None) -> List[str]:
    """
    Get a sequence of colors from a colorscale.

    Args:
        n_colors: Number of colors to generate
        colorscale: Name of the colorscale, or None for default

    Returns:
        List of colors as hex strings
    """
    if colorscale is None:
        colorscale = get_config('cmap', 'plotly')

    # Jika hanya perlu satu warna, gunakan warna default
    if n_colors <= 1:
        return ['#636EFA']

    # Gunakan colorscale untuk membuat sequence
    try:
        import plotly.colors as colors
        color_scale = getattr(colors.sequential, colorscale, None)
        if color_scale is None:
            return colors.qualitative.Plotly[:n_colors]

        # Interpolasi colors dari colorscale
        positions = np.linspace(0, 1, n_colors)
        color_sequence = [colors.sample_colorscale(color_scale, p)[0] for p in positions]
        return color_sequence
    except Exception:
        # Fallback ke default colors
        default_colors = [
            '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
            '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
        ]
        return [default_colors[i % len(default_colors)] for i in range(n_colors)]


def convert_categorical_x(data: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Convert categorical x-data for plotting.

    Args:
        data: X-axis data

    Returns:
        Tuple of (numerical data, category labels)
    """
    if not isinstance(data[0], (str, bytes)):
        return data, None

    # Jika data adalah string, konversi ke indeks numerik
    categories = list(dict.fromkeys(data))  # Hapus duplikat tapi pertahankan urutan
    x_numeric = np.array([categories.index(x) for x in data])

    return x_numeric, categories
