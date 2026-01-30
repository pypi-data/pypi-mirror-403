from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union

from fmus_viz.core.base import ChartVisualization
from fmus_viz.core.config import get_config
from fmus_viz.core.utils import (
    convert_to_dataframe,
    get_column_data,
    infer_x_y_columns,
    parse_color_argument
)


class MatplotlibVisualization(ChartVisualization):
    """Base class for Matplotlib visualizations."""

    def __init__(
        self,
        data: Any,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        **kwargs
    ):
        """Initialize a Matplotlib visualization."""
        super().__init__(data, x=x, y=y, **kwargs)
        self._figure = None
        self._ax = None

    def _create_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create a Matplotlib figure and axes."""
        # Dapatkan konfigurasi figure
        figsize = self.config.get('figsize', get_config('figsize', 'matplotlib'))
        dpi = self.config.get('dpi', get_config('dpi', 'matplotlib'))

        # Buat figure dan axes
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        return fig, ax

    def _apply_styling(self, fig: plt.Figure, ax: plt.Axes) -> None:
        """Apply styling to figure and axes."""
        # Judul
        if 'title' in self.config:
            title_size = self.config.get('title_size', get_config('title_size', 'matplotlib'))
            ax.set_title(self.config['title'], fontsize=title_size)

        # Label sumbu
        if 'xlabel' in self.config:
            label_size = self.config.get('label_size', get_config('label_size', 'matplotlib'))
            ax.set_xlabel(self.config['xlabel'], fontsize=label_size)

        if 'ylabel' in self.config:
            label_size = self.config.get('label_size', get_config('label_size', 'matplotlib'))
            ax.set_ylabel(self.config['ylabel'], fontsize=label_size)

        # Grid
        grid_config = self.config.get('grid', {'show': get_config('show_grid', 'matplotlib')})
        ax.grid(grid_config.get('show', True), **{k: v for k, v in grid_config.items() if k != 'show'})

        # Legend
        legend_config = self.config.get('legend', {})
        if legend_config.get('show', True) and ax.get_legend_handles_labels()[0]:
            legend_loc = legend_config.get('loc', get_config('legend_loc', 'matplotlib'))
            ax.legend(loc=legend_loc)

        # Ukuran tick
        tick_size = self.config.get('tick_size', get_config('tick_size', 'matplotlib'))
        ax.tick_params(axis='both', which='major', labelsize=tick_size)

        # Tema/style
        if 'theme' in self.config:
            with plt.style.context(self.config['theme']):
                pass  # Style already applied, this is just to avoid warnings if theme doesn't exist

        # Ukuran figure (jika diatur secara eksplisit)
        if 'width' in self.config and 'height' in self.config:
            fig.set_size_inches(self.config['width'], self.config['height'])
        elif 'figsize' in self.config:
            fig.set_size_inches(*self.config['figsize'])

    def render(self) -> plt.Figure:
        """Render the visualization."""
        # Implementasi ini akan di-override oleh subclass
        self._figure, self._ax = self._create_figure()
        self._apply_styling(self._figure, self._ax)
        return self._figure

    def show(self) -> MatplotlibVisualization:
        """Display the visualization."""
        if self._figure is None:
            self._figure = self.render()

        plt.show()
        return self

    def save(self, filename: str, **kwargs) -> MatplotlibVisualization:
        """Save the visualization to a file."""
        if self._figure is None:
            self._figure = self.render()

        save_kwargs = {
            'dpi': self.config.get('dpi', get_config('dpi', 'matplotlib')),
            'bbox_inches': 'tight'
        }
        save_kwargs.update(kwargs)

        self._figure.savefig(filename, **save_kwargs)
        return self


class BarVisualization(MatplotlibVisualization):
    """Bar chart visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a bar chart."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Inferensi kolom x dan y jika tidak diberikan
        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for bar chart")

        # Dapatkan data untuk plotting
        x_data = get_column_data(df, x) if x is not None else np.arange(len(df))
        y_data = get_column_data(df, y)

        # Siapkan warna
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, len(x_data))

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data
        ax.bar(x_data, y_data, color=color)

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


class BarHVisualization(MatplotlibVisualization):
    """Horizontal bar chart visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a horizontal bar chart."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Inferensi kolom x dan y jika tidak diberikan
        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for horizontal bar chart")

        # Dapatkan data untuk plotting
        x_data = get_column_data(df, x) if x is not None else np.arange(len(df))
        y_data = get_column_data(df, y)

        # Siapkan warna
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, len(x_data))

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data - untuk barh, x dan y dibalik
        ax.barh(x_data, y_data, color=color)

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


class LineVisualization(MatplotlibVisualization):
    """Line chart visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a line chart."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Inferensi kolom x dan y jika tidak diberikan
        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for line chart")

        # Dapatkan data untuk plotting
        x_data = get_column_data(df, x) if x is not None else np.arange(len(df))
        y_data = get_column_data(df, y)

        # Siapkan warna dan marker
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, 1)

        marker = self.config.get('marker', '')

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data
        ax.plot(x_data, y_data, color=color, marker=marker)

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


class ScatterVisualization(MatplotlibVisualization):
    """Scatter plot visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a scatter plot."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Inferensi kolom x dan y jika tidak diberikan
        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for scatter plot")

        # Dapatkan data untuk plotting
        x_data = get_column_data(df, x) if x is not None else np.arange(len(df))
        y_data = get_column_data(df, y)

        # Siapkan warna, ukuran, dan marker
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, len(x_data))

        size = self.config.get('size', 20)
        marker = self.config.get('marker', 'o')

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data
        ax.scatter(x_data, y_data, c=color, s=size, marker=marker)

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


class HistogramVisualization(MatplotlibVisualization):
    """Histogram visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a histogram."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Dapatkan kolom nilai untuk histogram
        value = self.config.get('value') or self.config.get('y') or self.config.get('x')

        if value is None:
            # Jika tidak ada kolom yang ditentukan dan hanya ada satu kolom, gunakan itu
            if len(df.columns) == 1:
                value = df.columns[0]
            else:
                # Coba inferensi kolom numerik pertama
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    value = numeric_cols[0]
                else:
                    raise ValueError("Could not determine value column for histogram")

        # Dapatkan data untuk plotting
        data = get_column_data(df, value)

        # Dapatkan parameter histogram
        bins = self.config.get('bins', 10)
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, 1)

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data
        ax.hist(data, bins=bins, color=color)

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Set x label jika belum diatur
        if 'xlabel' not in self.config:
            ax.set_xlabel(value)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


class PieVisualization(MatplotlibVisualization):
    """Pie chart visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a pie chart."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Dapatkan kolom untuk values dan labels
        values = self.config.get('values') or self.config.get('y')
        labels = self.config.get('labels') or self.config.get('x')

        if values is None:
            # Jika tidak ada kolom nilai yang ditentukan, coba inferensi kolom numerik
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                values = numeric_cols[0]
            else:
                raise ValueError("Could not determine values column for pie chart")

        # Dapatkan data untuk plotting
        values_data = get_column_data(df, values)

        # Siapkan labels
        if labels is not None:
            labels_data = get_column_data(df, labels)
        else:
            # Jika tidak ada kolom labels yang ditentukan, gunakan index
            labels_data = df.index.values

        # Siapkan warna
        colors = self.config.get('color')

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data
        ax.pie(
            values_data,
            labels=labels_data,
            colors=colors,
            autopct=self.config.get('autopct', '%1.1f%%'),
            startangle=self.config.get('startangle', 0)
        )

        # Jika equal=True, pastikan pie chart berbentuk lingkaran
        if self.config.get('equal', True):
            ax.axis('equal')

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


class AreaVisualization(MatplotlibVisualization):
    """Area chart visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render an area chart."""
        # Siapkan data
        df = convert_to_dataframe(self.data)

        # Inferensi kolom x dan y jika tidak diberikan
        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for area chart")

        # Dapatkan data untuk plotting
        x_data = get_column_data(df, x) if x is not None else np.arange(len(df))
        y_data = get_column_data(df, y)

        # Siapkan warna dan alpha
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, 1)

        alpha = self.config.get('alpha', 0.5)

        # Buat figure dan axes
        fig, ax = self._create_figure()

        # Plot data
        ax.fill_between(x_data, y_data, color=color, alpha=alpha)

        # Terapkan styling
        self._apply_styling(fig, ax)

        # Simpan figure dan axes
        self._figure = fig
        self._ax = ax

        return fig


# Factory functions for creating visualizations

def bar_plot(data: Any, **kwargs) -> BarVisualization:
    """
    Create a bar chart visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        BarVisualization instance
    """
    return BarVisualization(data, **kwargs)


def barh_plot(data: Any, **kwargs) -> BarHVisualization:
    """
    Create a horizontal bar chart visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        BarHVisualization instance
    """
    return BarHVisualization(data, **kwargs)


def line_plot(data: Any, **kwargs) -> LineVisualization:
    """
    Create a line chart visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        LineVisualization instance
    """
    return LineVisualization(data, **kwargs)


def scatter_plot(data: Any, **kwargs) -> ScatterVisualization:
    """
    Create a scatter plot visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        ScatterVisualization instance
    """
    return ScatterVisualization(data, **kwargs)


def histogram_plot(data: Any, **kwargs) -> HistogramVisualization:
    """
    Create a histogram visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        HistogramVisualization instance
    """
    return HistogramVisualization(data, **kwargs)


def pie_plot(data: Any, **kwargs) -> PieVisualization:
    """
    Create a pie chart visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        PieVisualization instance
    """
    return PieVisualization(data, **kwargs)


def area_plot(data: Any, **kwargs) -> AreaVisualization:
    """
    Create an area chart visualization using Matplotlib.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        AreaVisualization instance
    """
    return AreaVisualization(data, **kwargs)
