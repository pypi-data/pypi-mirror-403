from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union

from fmus_viz.core.base import StatisticalVisualization
from fmus_viz.core.config import get_config
from fmus_viz.core.utils import (
    convert_to_dataframe,
    get_column_data,
    infer_categorical_columns,
    parse_color_argument
)


class MatplotlibStatVisualization(StatisticalVisualization):
    """Base class for Matplotlib statistical visualizations."""

    def __init__(self, data: Any, **kwargs):
        """Initialize a Matplotlib statistical visualization."""
        super().__init__(data, **kwargs)
        self._figure = None
        self._ax = None

    def _create_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create a Matplotlib figure and axes."""
        figsize = self.config.get('figsize', get_config('figsize', 'matplotlib'))
        dpi = self.config.get('dpi', get_config('dpi', 'matplotlib'))

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        return fig, ax

    def _apply_styling(self, fig: plt.Figure, ax: plt.Axes) -> None:
        """Apply styling to figure and axes."""
        if 'title' in self.config:
            title_size = self.config.get('title_size', get_config('title_size', 'matplotlib'))
            ax.set_title(self.config['title'], fontsize=title_size)

        if 'xlabel' in self.config:
            label_size = self.config.get('label_size', get_config('label_size', 'matplotlib'))
            ax.set_xlabel(self.config['xlabel'], fontsize=label_size)

        if 'ylabel' in self.config:
            label_size = self.config.get('label_size', get_config('label_size', 'matplotlib'))
            ax.set_ylabel(self.config['ylabel'], fontsize=label_size)

        grid_config = self.config.get('grid', {'show': get_config('show_grid', 'matplotlib')})
        ax.grid(grid_config.get('show', True), **{k: v for k, v in grid_config.items() if k != 'show'})

        legend_config = self.config.get('legend', {})
        if legend_config.get('show', True) and ax.get_legend_handles_labels()[0]:
            legend_loc = legend_config.get('loc', get_config('legend_loc', 'matplotlib'))
            ax.legend(loc=legend_loc)

        tick_size = self.config.get('tick_size', get_config('tick_size', 'matplotlib'))
        ax.tick_params(axis='both', which='major', labelsize=tick_size)

        if 'width' in self.config and 'height' in self.config:
            fig.set_size_inches(self.config['width'], self.config['height'])

    def render(self) -> plt.Figure:
        """Render the visualization."""
        self._figure, self._ax = self._create_figure()
        self._apply_styling(self._figure, self._ax)
        return self._figure

    def show(self) -> MatplotlibStatVisualization:
        """Display the visualization."""
        if self._figure is None:
            self._figure = self.render()

        plt.show()
        return self

    def save(self, filename: str, **kwargs) -> MatplotlibStatVisualization:
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


class BoxplotVisualization(MatplotlibStatVisualization):
    """Box plot visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a box plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Determine columns to use
        if x is None and y is None:
            # Use all numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                raise ValueError("No numeric columns found for box plot")
            y_data = [df[col].dropna().values for col in numeric_cols]
            labels = numeric_cols
        elif y is not None:
            if x is not None:
                # Grouped boxplot
                groups = df.groupby(x)[y].apply(list)
                y_data = groups.values
                labels = groups.index
            else:
                y_data = [df[y].dropna().values]
                labels = [y] if isinstance(y, str) else ['value']
        else:
            raise ValueError("Could not determine columns for box plot")

        # Prepare colors
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, len(y_data))

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot boxplot
        bp = ax.boxplot(y_data, labels=labels, patch_artist=True)

        # Apply colors if provided
        if color is not None:
            for patch, c in zip(bp['boxes'], [color] * len(bp['boxes']) if isinstance(color, str) else color):
                patch.set_facecolor(c)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class ViolinVisualization(MatplotlibStatVisualization):
    """Violin plot visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a violin plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Determine columns to use
        if x is None and y is None:
            # Use all numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                raise ValueError("No numeric columns found for violin plot")
            y_data = [df[col].dropna().values for col in numeric_cols]
            labels = numeric_cols
        elif y is not None:
            if x is not None:
                # Grouped violin plot
                groups = df.groupby(x)[y].apply(list)
                y_data = groups.values
                labels = groups.index
            else:
                y_data = [df[y].dropna().values]
                labels = [y] if isinstance(y, str) else ['value']
        else:
            raise ValueError("Could not determine columns for violin plot")

        # Prepare colors
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, len(y_data))

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot violin
        parts = ax.violinplot(y_data, showmeans=True, showmedians=True)

        # Apply colors if provided
        if color is not None:
            colors = [color] * len(parts['bodies']) if isinstance(color, str) else color
            for pc, c in zip(parts['bodies'], colors):
                pc.set_facecolor(c)
                pc.set_alpha(0.7)

        # Set labels
        ax.set_xticks(np.arange(1, len(labels) + 1))
        ax.set_xticklabels(labels)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class HeatmapVisualization(MatplotlibStatVisualization):
    """Heatmap visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a heatmap."""
        df = convert_to_dataframe(self.data)

        # Get the data matrix for heatmap
        value = self.config.get('value')
        if value is not None:
            # Pivot the data if x and y are provided
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
        cmap = self.config.get('cmap', get_config('cmap', 'matplotlib'))

        # Get colorbar setting
        show_colorbar = self.config.get('colorbar', True)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot heatmap
        im = ax.imshow(matrix.values, cmap=cmap, aspect='auto')

        # Set ticks
        ax.set_xticks(np.arange(len(matrix.columns)))
        ax.set_yticks(np.arange(len(matrix.index)))
        ax.set_xticklabels(matrix.columns)
        ax.set_yticklabels(matrix.index)

        # Rotate x labels if needed
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

        # Add colorbar
        if show_colorbar:
            cbar = plt.colorbar(im, ax=ax)
            if 'ylabel' in self.config:
                cbar.set_label(self.config['ylabel'])

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class CorrelationVisualization(MatplotlibStatVisualization):
    """Correlation matrix heatmap visualization using Matplotlib."""

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

        # Get colorbar setting
        show_colorbar = self.config.get('colorbar', True)

        # Get annotation setting
        annot = self.config.get('annot', False)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot correlation matrix
        im = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1, aspect='auto')

        # Set ticks
        ax.set_xticks(np.arange(len(corr.columns)))
        ax.set_yticks(np.arange(len(corr.index)))
        ax.set_xticklabels(corr.columns)
        ax.set_yticklabels(corr.index)

        # Rotate x labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

        # Add annotations if requested
        if annot:
            for i in range(len(corr)):
                for j in range(len(corr.columns)):
                    text = ax.text(j, i, f'{corr.iloc[i, j]:.2f}',
                                 ha='center', va='center', color='black', fontsize=8)

        # Add colorbar
        if show_colorbar:
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Correlation')

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


class DensityVisualization(MatplotlibStatVisualization):
    """Density plot (KDE) visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a density plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Determine columns to use
        if x is None and y is None:
            # Use first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                raise ValueError("No numeric columns found for density plot")
            x = numeric_cols[0]

        # Prepare data
        if y is None:
            # 1D KDE
            x_data = df[x].dropna().values
            is_2d = False
        else:
            # 2D KDE
            x_data = df[x].dropna().values
            y_data = df[y].dropna().values
            is_2d = True

        # Get bandwidth
        bw_method = self.config.get('bw_method', 'scott')

        # Get color
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, 1)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Try to use scipy for KDE
        try:
            from scipy import stats

            if is_2d:
                # 2D KDE
                xmin, xmax = x_data.min(), x_data.max()
                ymin, ymax = y_data.min(), y_data.max()
                xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]

                values = np.vstack([x_data, y_data])
                kernel = stats.gaussian_kde(values, bw_method=bw_method)
                positions = np.vstack([xx.ravel(), yy.ravel()])
                z = np.reshape(kernel(positions).T, xx.shape)

                ax.contourf(xx, yy, z, cmap=self.config.get('cmap', 'viridis'))
                ax.scatter(x_data, y_data, c=color, alpha=0.5, s=5)
            else:
                # 1D KDE
                xmin, xmax = x_data.min(), x_data.max()
                xx = np.linspace(xmin, xmax, 200)
                kernel = stats.gaussian_kde(x_data, bw_method=bw_method)
                zz = kernel(xx)

                ax.plot(xx, zz, color=color)
                ax.fill_between(xx, zz, alpha=0.3, color=color)

        except ImportError:
            # Fallback to histogram if scipy not available
            if is_2d:
                ax.hist2d(x_data, y_data, bins=50, cmap=self.config.get('cmap', 'viridis'))
            else:
                ax.hist(x_data, bins=50, density=True, color=color, alpha=0.7)

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


class RegressionVisualization(MatplotlibStatVisualization):
    """Regression plot visualization using Matplotlib."""

    def render(self) -> plt.Figure:
        """Render a regression plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        if x is None or y is None:
            # Try to infer x and y columns
            from fmus_viz.core.utils import infer_x_y_columns
            inferred_x, inferred_y = infer_x_y_columns(df)
            x = x or inferred_x
            y = y or inferred_y

        if x is None or y is None:
            raise ValueError("Could not determine x and y columns for regression plot")

        # Get data
        x_data = get_column_data(df, x)
        y_data = get_column_data(df, y)

        # Remove NaN values
        mask = ~(np.isnan(x_data) | np.isnan(y_data))
        x_data = x_data[mask]
        y_data = y_data[mask]

        # Get color
        color = self.config.get('color')
        if color is not None:
            color = parse_color_argument(color, 1)

        # Get confidence interval setting
        show_ci = self.config.get('ci', True)

        # Create figure and axes
        fig, ax = self._create_figure()

        # Plot scatter
        ax.scatter(x_data, y_data, c=color, alpha=0.6, s=30)

        # Fit and plot regression line
        try:
            from scipy import stats

            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
            line_x = np.array([x_data.min(), x_data.max()])
            line_y = slope * line_x + intercept

            ax.plot(line_x, line_y, 'r-', linewidth=2, label=f'y = {slope:.2f}x + {intercept:.2f}')

            # Add confidence interval if requested
            if show_ci and len(x_data) > 2:
                # Calculate prediction interval
                predict_y = slope * x_data + intercept
                residuals = y_data - predict_y
                std_residuals = np.std(residuals)

                # 95% confidence interval
                ci = 1.96 * std_residuals
                ax.fill_between(line_x, line_y - ci, line_y + ci, alpha=0.2, color='red')

            # Add legend with R^2
            ax.legend()

        except ImportError:
            # Fallback: simple line through endpoints
            ax.plot([x_data.min(), x_data.max()], [y_data.min(), y_data.max()], 'r-', linewidth=2)

        # Apply styling
        self._apply_styling(fig, ax)

        self._figure = fig
        self._ax = ax

        return fig


# Factory functions

def boxplot_plot(data: Any, **kwargs) -> BoxplotVisualization:
    """Create a box plot visualization using Matplotlib."""
    return BoxplotVisualization(data, **kwargs)


def violin_plot(data: Any, **kwargs) -> ViolinVisualization:
    """Create a violin plot visualization using Matplotlib."""
    return ViolinVisualization(data, **kwargs)


def heatmap_plot(data: Any, **kwargs) -> HeatmapVisualization:
    """Create a heatmap visualization using Matplotlib."""
    return HeatmapVisualization(data, **kwargs)


def corr_plot(data: Any, **kwargs) -> CorrelationVisualization:
    """Create a correlation matrix heatmap visualization using Matplotlib."""
    return CorrelationVisualization(data, **kwargs)


def density_plot(data: Any, **kwargs) -> DensityVisualization:
    """Create a density plot visualization using Matplotlib."""
    return DensityVisualization(data, **kwargs)


def regression_plot(data: Any, **kwargs) -> RegressionVisualization:
    """Create a regression plot visualization using Matplotlib."""
    return RegressionVisualization(data, **kwargs)
