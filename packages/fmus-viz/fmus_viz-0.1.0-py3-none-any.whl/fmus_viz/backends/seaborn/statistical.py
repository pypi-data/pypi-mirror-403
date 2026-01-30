from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union

from fmus_viz.core.base import StatisticalVisualization
from fmus_viz.core.config import get_config
from fmus_viz.core.utils import (
    convert_to_dataframe,
    get_column_data,
    parse_color_argument
)


class SeabornStatVisualization(StatisticalVisualization):
    """Base class for Seaborn statistical visualizations."""

    def __init__(self, data: Any, **kwargs):
        """Initialize a Seaborn statistical visualization."""
        super().__init__(data, **kwargs)
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

    def show(self) -> SeabornStatVisualization:
        """Display the visualization."""
        if self._figure is None:
            self._figure = self.render()

        plt.show()
        return self

    def save(self, filename: str, **kwargs) -> SeabornStatVisualization:
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


class BoxplotVisualization(SeabornStatVisualization):
    """Box plot visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a box plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        if x is not None and y is not None:
            sns.boxplot(data=df, x=x, y=y, ax=ax)
        elif y is not None:
            sns.boxplot(data=df, y=y, ax=ax)
        else:
            # Use all numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            sns.boxplot(data=numeric_df, ax=ax)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class ViolinVisualization(SeabornStatVisualization):
    """Violin plot visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a violin plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        if x is not None and y is not None:
            sns.violinplot(data=df, x=x, y=y, ax=ax)
        elif y is not None:
            sns.violinplot(data=df, y=y, ax=ax)
        else:
            # Use all numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            sns.violinplot(data=numeric_df, ax=ax)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class HeatmapVisualization(SeabornStatVisualization):
    """Heatmap visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a heatmap."""
        df = convert_to_dataframe(self.data)

        # Get the data matrix for heatmap
        value = self.config.get('value')
        if value is not None:
            x = self.config.get('x')
            y = self.config.get('y')
            if x is not None and y is not None:
                matrix = df.pivot(index=y, columns=x, values=value)
            else:
                matrix = df.set_index(value) if len(df.columns) == 1 else df
        else:
            # Use the entire dataframe as matrix
            numeric_df = df.select_dtypes(include=[np.number])
            if numeric_df.empty:
                raise ValueError("No numeric data found for heatmap")
            matrix = numeric_df

        # Handle NaN values
        matrix = matrix.fillna(0)

        # Get colormap
        cmap = self.config.get('cmap', get_config('cmap', 'seaborn'))

        # Get annotation setting
        annot = self.config.get('annot', False)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot heatmap
        sns.heatmap(matrix, cmap=cmap, annot=annot, ax=ax)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class CorrelationVisualization(SeabornStatVisualization):
    """Correlation matrix heatmap visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a correlation matrix heatmap."""
        df = convert_to_dataframe(self.data)

        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            raise ValueError("No numeric data found for correlation matrix")

        # Compute correlation matrix
        corr = numeric_df.corr()

        # Get colormap
        cmap = self.config.get('cmap', 'coolwarm')

        # Get annotation setting
        annot = self.config.get('annot', False)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot correlation matrix
        sns.heatmap(corr, cmap=cmap, annot=annot, center=0, vmin=-1, vmax=1, ax=ax)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class DensityVisualization(SeabornStatVisualization):
    """Density plot (KDE) visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a density plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        if y is None:
            # 1D KDE
            if x is None:
                # Use first numeric column
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_cols:
                    raise ValueError("No numeric columns found for density plot")
                x = numeric_cols[0]

            sns.kdeplot(data=df, x=x, ax=ax, fill=self.config.get('fill', True))
        else:
            # 2D KDE
            sns.kdeplot(data=df, x=x, y=y, ax=ax)

        # Apply styling
        if 'xlabel' not in self.config and x is not None:
            ax.set_xlabel(x)
        if 'ylabel' not in self.config:
            if y is not None:
                ax.set_ylabel(y)
            else:
                ax.set_ylabel('Density')

        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class RegressionVisualization(SeabornStatVisualization):
    """Regression plot visualization using Seaborn."""

    def render(self) -> plt.Figure:
        """Render a regression plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            from fmus_viz.core.utils import infer_x_y_columns
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for regression plot")

        # Get confidence interval setting
        ci = self.config.get('ci', True)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot using seaborn
        sns.regplot(data=df, x=x, y=y, ax=ax, ci=95 if ci else None)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


# Factory functions

def boxplot_plot(data: Any, **kwargs) -> BoxplotVisualization:
    """Create a box plot visualization using Seaborn."""
    return BoxplotVisualization(data, **kwargs)


def violin_plot(data: Any, **kwargs) -> ViolinVisualization:
    """Create a violin plot visualization using Seaborn."""
    return ViolinVisualization(data, **kwargs)


def heatmap_plot(data: Any, **kwargs) -> HeatmapVisualization:
    """Create a heatmap visualization using Seaborn."""
    return HeatmapVisualization(data, **kwargs)


def corr_plot(data: Any, **kwargs) -> CorrelationVisualization:
    """Create a correlation matrix heatmap visualization using Seaborn."""
    return CorrelationVisualization(data, **kwargs)


def density_plot(data: Any, **kwargs) -> DensityVisualization:
    """Create a density plot visualization using Seaborn."""
    return DensityVisualization(data, **kwargs)


def regression_plot(data: Any, **kwargs) -> RegressionVisualization:
    """Create a regression plot visualization using Seaborn."""
    return RegressionVisualization(data, **kwargs)
