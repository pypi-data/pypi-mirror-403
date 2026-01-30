from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
import plotly.colors as pc  # Add explicit import for Plotly colors
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
from fmus_viz.backends.plotly.utils import (
    create_figure,
    apply_figure_styling,
    get_color_sequence,
    convert_categorical_x
)


class PlotlyVisualization(ChartVisualization):
    """Base class for Plotly visualizations."""

    def __init__(
        self,
        data: Any,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        **kwargs
    ):
        """Initialize a Plotly visualization."""
        super().__init__(data, x=x, y=y, **kwargs)
        self._figure = None

    def _create_figure(self) -> go.Figure:
        """Create a Plotly figure."""
        # Dapatkan konfigurasi untuk ukuran figure
        width = self.config.get('width')
        height = self.config.get('height')

        if 'figsize' in self.config:
            figsize = self.config['figsize']
            dpi = self.config.get('dpi', get_config('dpi', 'plotly'))
            width = int(figsize[0] * dpi)
            height = int(figsize[1] * dpi)

        # Buat figure
        fig = create_figure(width=width, height=height)
        return fig

    def _apply_styling(self, fig: go.Figure) -> None:
        """Apply styling to figure."""
        # Extract styling parameters from config
        title = self.config.get('title')
        xlabel = self.config.get('xlabel')
        ylabel = self.config.get('ylabel')

        # Grid
        grid_config = self.config.get('grid', {})
        show_grid = grid_config.get('show', get_config('show_grid', 'plotly'))

        # Legend
        legend_config = self.config.get('legend', {})
        show_legend = legend_config.get('show', True)

        # Create a copy of the config without the explicit parameters
        # to avoid passing them twice
        filtered_config = self.config.copy()
        for key in ['title', 'xlabel', 'ylabel', 'grid', 'legend']:
            filtered_config.pop(key, None)

        # Apply styling
        apply_figure_styling(
            fig,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            show_grid=show_grid,
            show_legend=show_legend,
            **filtered_config
        )

    def render(self) -> go.Figure:
        """Render the visualization."""
        # Implementasi ini akan di-override oleh subclass
        self._figure = self._create_figure()
        self._apply_styling(self._figure)
        return self._figure

    def show(self) -> PlotlyVisualization:
        """Display the visualization."""
        if self._figure is None:
            self._figure = self.render()

        self._figure.show()
        return self

    def save(self, filename: str, **kwargs) -> PlotlyVisualization:
        """Save the visualization to a file."""
        if self._figure is None:
            self._figure = self.render()

        # Tentukan format dari ekstensi file
        format_type = filename.split('.')[-1] if '.' in filename else 'png'

        # Simpan file
        self._figure.write_image(filename, **kwargs)
        return self


class BarVisualization(PlotlyVisualization):
    """Bar chart visualization using Plotly."""

    def render(self) -> go.Figure:
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

        # Handle categorical data
        x_numeric, categories = convert_categorical_x(x_data)

        # Siapkan warna
        color = self.config.get('color')
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Buat figure
        fig = self._create_figure()

        # Tambahkan bar trace
        fig.add_trace(go.Bar(
            x=x_data,
            y=y_data,
            marker_color=color,
            name=y if isinstance(y, str) else 'value'
        ))

        # Terapkan styling
        self._apply_styling(fig)

        # Simpan figure
        self._figure = fig

        return fig


class BarHVisualization(PlotlyVisualization):
    """Horizontal bar chart visualization using Plotly."""

    def render(self) -> go.Figure:
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

        # Handle categorical data
        if isinstance(x_data[0], (str, bytes)):
            categories = x_data
        else:
            categories = None

        # Siapkan warna
        color = self.config.get('color')
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Buat figure
        fig = self._create_figure()

        # Tambahkan horizontal bar trace
        fig.add_trace(go.Bar(
            x=y_data,  # Note: x and y are swapped for horizontal bars
            y=x_data,
            orientation='h',
            marker_color=color,
            name=y if isinstance(y, str) else 'value'
        ))

        # Terapkan styling dengan label swapped
        xlabel_orig = self.config.get('xlabel')
        ylabel_orig = self.config.get('ylabel')

        if 'xlabel' in self.config:
            self.config['ylabel'] = xlabel_orig

        if 'ylabel' in self.config:
            self.config['xlabel'] = ylabel_orig

        self._apply_styling(fig)

        # Restore original labels
        if xlabel_orig is not None:
            self.config['xlabel'] = xlabel_orig

        if ylabel_orig is not None:
            self.config['ylabel'] = ylabel_orig

        # Simpan figure
        self._figure = fig

        return fig


class LineVisualization(PlotlyVisualization):
    """Line chart visualization using Plotly."""

    def render(self) -> go.Figure:
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
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        marker = self.config.get('marker')

        # Mode (markers, lines, or both)
        mode = 'lines'
        if marker:
            mode = 'lines+markers'

        # Buat figure
        fig = self._create_figure()

        # Tambahkan line trace
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode=mode,
            line=dict(color=color),
            name=y if isinstance(y, str) else 'value'
        ))

        # Terapkan styling
        self._apply_styling(fig)

        # Simpan figure
        self._figure = fig

        return fig


class ScatterVisualization(PlotlyVisualization):
    """Scatter plot visualization using Plotly."""

    def render(self) -> go.Figure:
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
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        size = self.config.get('size', 10)
        marker_symbol = self.config.get('marker', 'circle')

        # Buat figure
        fig = self._create_figure()

        # Tambahkan scatter trace
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            marker=dict(
                color=color,
                size=size,
                symbol=marker_symbol
            ),
            name=y if isinstance(y, str) else 'value'
        ))

        # Terapkan styling
        self._apply_styling(fig)

        # Simpan figure
        self._figure = fig

        return fig


class HistogramVisualization(PlotlyVisualization):
    """Histogram visualization using Plotly."""

    def render(self) -> go.Figure:
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
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Buat figure
        fig = self._create_figure()

        # Tambahkan histogram trace
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=bins,
            marker_color=color,
            name=value if isinstance(value, str) else 'value'
        ))

        # Terapkan styling
        if 'xlabel' not in self.config and value is not None:
            self.config['xlabel'] = value

        self._apply_styling(fig)

        # Simpan figure
        self._figure = fig

        return fig


class PieVisualization(PlotlyVisualization):
    """Pie chart visualization using Plotly."""

    def render(self) -> go.Figure:
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
        if colors is None:
            colors = get_color_sequence(len(values_data))

        # Buat figure
        fig = self._create_figure()

        # Tambahkan pie trace
        fig.add_trace(go.Pie(
            values=values_data,
            labels=labels_data,
            marker_colors=colors,
            textinfo=self.config.get('textinfo', 'percent+label'),
            hoverinfo=self.config.get('hoverinfo', 'label+percent+value')
        ))

        # Terapkan styling
        self._apply_styling(fig)

        # Simpan figure
        self._figure = fig

        return fig


class AreaVisualization(PlotlyVisualization):
    """Area chart visualization using Plotly."""

    def render(self) -> go.Figure:
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
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        opacity = self.config.get('alpha', 0.5)

        # Buat figure
        fig = self._create_figure()

        # Tambahkan area trace
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines',
            fill='tozeroy',
            fillcolor=f'rgba({",".join(str(int(c)) for c in pc.hex_to_rgb(color))},{opacity})',
            line=dict(color=color),
            name=y if isinstance(y, str) else 'value'
        ))

        # Terapkan styling
        self._apply_styling(fig)

        # Simpan figure
        self._figure = fig

        return fig


# Factory functions for creating visualizations

def bar_plot(data: Any, **kwargs) -> BarVisualization:
    """
    Create a bar chart visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        BarVisualization instance
    """
    return BarVisualization(data, **kwargs)


def barh_plot(data: Any, **kwargs) -> BarHVisualization:
    """
    Create a horizontal bar chart visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        BarHVisualization instance
    """
    return BarHVisualization(data, **kwargs)


def line_plot(data: Any, **kwargs) -> LineVisualization:
    """
    Create a line chart visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        LineVisualization instance
    """
    return LineVisualization(data, **kwargs)


def scatter_plot(data: Any, **kwargs) -> ScatterVisualization:
    """
    Create a scatter plot visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        ScatterVisualization instance
    """
    return ScatterVisualization(data, **kwargs)


def histogram_plot(data: Any, **kwargs) -> HistogramVisualization:
    """
    Create a histogram visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        HistogramVisualization instance
    """
    return HistogramVisualization(data, **kwargs)


def pie_plot(data: Any, **kwargs) -> PieVisualization:
    """
    Create a pie chart visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        PieVisualization instance
    """
    return PieVisualization(data, **kwargs)


def area_plot(data: Any, **kwargs) -> AreaVisualization:
    """
    Create an area chart visualization using Plotly.

    Args:
        data: Data to visualize
        **kwargs: Additional configuration parameters

    Returns:
        AreaVisualization instance
    """
    return AreaVisualization(data, **kwargs)
