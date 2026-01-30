from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
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


class SeabornVisualization(ChartVisualization):
    """Base class for Seaborn visualizations."""

    def __init__(
        self,
        data: Any,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        **kwargs
    ):
        """Initialize a Seaborn visualization."""
        super().__init__(data, x=x, y=y, **kwargs)
        self._figure = None
        self._ax = None

    def _create_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create a Matplotlib figure with Seaborn styling."""
        from fmus_viz.backends.seaborn.utils import setup_seaborn_style

        setup_seaborn_style()

        figsize = self.config.get('figsize', get_config('figsize', 'seaborn'))
        dpi = self.config.get('dpi', get_config('dpi', 'seaborn'))

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        return fig, ax

    def _apply_styling(self, fig: plt.Figure, ax: plt.Axes) -> None:
        """Apply styling to figure and axes."""
        if 'title' in self.config:
            title_size = self.config.get('title_size', get_config('title_size', 'seaborn'))
            ax.set_title(self.config['title'], fontsize=title_size)

        if 'xlabel' in self.config:
            label_size = self.config.get('label_size', get_config('label_size', 'seaborn'))
            ax.set_xlabel(self.config['xlabel'], fontsize=label_size)

        if 'ylabel' in self.config:
            label_size = self.config.get('label_size', get_config('label_size', 'seaborn'))
            ax.set_ylabel(self.config['ylabel'], fontsize=label_size)

        grid_config = self.config.get('grid', {'show': get_config('show_grid', 'seaborn')})
        ax.grid(grid_config.get('show', True), **{k: v for k, v in grid_config.items() if k != 'show'})

        legend_config = self.config.get('legend', {})
        if legend_config.get('show', True) and ax.get_legend():
            legend_loc = legend_config.get('loc', get_config('legend_loc', 'seaborn'))
            ax.legend(loc=legend_loc)

        tick_size = self.config.get('tick_size', get_config('tick_size', 'seaborn'))
        ax.tick_params(axis='both', which='major', labelsize=tick_size)

        if 'width' in self.config and 'height' in self.config:
            fig.set_size_inches(self.config['width'], self.config['height'])

    def render(self) -> plt.Figure:
        """Render the visualization."""
        self._figure, self._ax = self._create_figure()
        self._apply_styling(self._figure, self._ax)
        return self._figure

    def show(self) -> SeabornVisualization:
        """Display the visualization."""
        if self._figure is None:
            self._figure = self.render()

        plt.show()
        return self

    def save(self, filename: str, **kwargs) -> SeabornVisualization:
        """Save the visualization to a file."""
        if self._figure is None:
            self._figure = self.render()

        save_kwargs = {
            'dpi': self.config.get('dpi', get_config('dpi', 'seaborn')),
            'bbox_inches': 'tight'
        }
        save_kwargs.update(kwargs)

        self._figure.savefig(filename, **save_kwargs)
        return self


class BarVisualization(SeabornVisualization):
    """Bar chart visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a bar chart."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for bar chart")

        # Get color
        color = self.config.get('color')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        sns.barplot(data=df, x=x, y=y, ax=ax, color=color)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class BarHVisualization(SeabornVisualization):
    """Horizontal bar chart visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a horizontal bar chart."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for horizontal bar chart")

        # Get color
        color = self.config.get('color')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn (swap x and y for horizontal)
        sns.barplot(data=df, x=y, y=x, ax=ax, color=color)

        # Swap labels back
        xlabel_orig = self.config.get('xlabel')
        ylabel_orig = self.config.get('ylabel')

        if xlabel_orig is not None:
            ax.set_ylabel(xlabel_orig)
        if ylabel_orig is not None:
            ax.set_xlabel(ylabel_orig)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class LineVisualization(SeabornVisualization):
    """Line chart visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a line chart."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for line chart")

        # Get color
        color = self.config.get('color')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        sns.lineplot(data=df, x=x, y=y, ax=ax, color=color)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class ScatterVisualization(SeabornVisualization):
    """Scatter plot visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a scatter plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for scatter plot")

        # Get color
        color = self.config.get('color')
        size = self.config.get('size')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        sns.scatterplot(data=df, x=x, y=y, ax=ax, color=color, size=size)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class HistogramVisualization(SeabornVisualization):
    """Histogram visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a histogram."""
        df = convert_to_dataframe(self.data)

        value = self.config.get('value') or self.config.get('y') or self.config.get('x')

        if value is None:
            if len(df.columns) == 1:
                value = df.columns[0]
            else:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    value = numeric_cols[0]
                else:
                    raise ValueError("Could not determine value column for histogram")

        bins = self.config.get('bins', 10)
        color = self.config.get('color')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        sns.histplot(data=df, x=value, bins=bins, ax=ax, color=color)

        # Apply styling
        if 'xlabel' not in self.config:
            ax.set_xlabel(value)

        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class AreaVisualization(SeabornVisualization):
    """Area chart visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render an area chart."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for area chart")

        color = self.config.get('color')
        alpha = self.config.get('alpha', 0.5)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn (use kdeplot or lineplot with fill)
        sns.kdeplot(data=df, x=x, y=y, ax=ax, color=color, fill=True, alpha=alpha)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


# Factory functions

def bar_plot(data: Any, **kwargs) -> BarVisualization:
    """Create a bar chart visualization using Seaborn."""
    return BarVisualization(data, **kwargs)


def barh_plot(data: Any, **kwargs) -> BarHVisualization:
    """Create a horizontal bar chart visualization using Seaborn."""
    return BarHVisualization(data, **kwargs)


def line_plot(data: Any, **kwargs) -> LineVisualization:
    """Create a line chart visualization using Seaborn."""
    return LineVisualization(data, **kwargs)


def scatter_plot(data: Any, **kwargs) -> ScatterVisualization:
    """Create a scatter plot visualization using Seaborn."""
    return ScatterVisualization(data, **kwargs)


def histogram_plot(data: Any, **kwargs) -> HistogramVisualization:
    """Create a histogram visualization using Seaborn."""
    return HistogramVisualization(data, **kwargs)


def area_plot(data: Any, **kwargs) -> AreaVisualization:
    """Create an area chart visualization using Seaborn."""
    return AreaVisualization(data, **kwargs)
