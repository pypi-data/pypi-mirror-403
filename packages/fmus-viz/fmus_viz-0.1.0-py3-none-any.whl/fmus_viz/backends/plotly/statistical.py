from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
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
from fmus_viz.backends.plotly.utils import (
    create_figure,
    apply_figure_styling,
    get_color_sequence
)


class PlotlyStatVisualization(StatisticalVisualization):
    """Base class for Plotly statistical visualizations."""

    def __init__(self, data: Any, **kwargs):
        """Initialize a Plotly statistical visualization."""
        super().__init__(data, **kwargs)
        self._figure = None

    def _create_figure(self) -> go.Figure:
        """Create a Plotly figure."""
        width = self.config.get('width')
        height = self.config.get('height')

        if 'figsize' in self.config:
            figsize = self.config['figsize']
            dpi = self.config.get('dpi', get_config('dpi', 'plotly'))
            width = int(figsize[0] * dpi)
            height = int(figsize[1] * dpi)

        return create_figure(width=width, height=height)

    def _apply_styling(self, fig: go.Figure) -> None:
        """Apply styling to figure."""
        title = self.config.get('title')
        xlabel = self.config.get('xlabel')
        ylabel = self.config.get('ylabel')

        grid_config = self.config.get('grid', {})
        show_grid = grid_config.get('show', get_config('show_grid', 'plotly'))

        legend_config = self.config.get('legend', {})
        show_legend = legend_config.get('show', True)

        filtered_config = self.config.copy()
        for key in ['title', 'xlabel', 'ylabel', 'grid', 'legend']:
            filtered_config.pop(key, None)

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
        self._figure = self._create_figure()
        self._apply_styling(self._figure)
        return self._figure

    def show(self) -> PlotlyStatVisualization:
        """Display the visualization."""
        if self._figure is None:
            self._figure = self.render()

        self._figure.show()
        return self

    def save(self, filename: str, **kwargs) -> PlotlyStatVisualization:
        """Save the visualization to a file."""
        if self._figure is None:
            self._figure = self.render()

        self._figure.write_image(filename, **kwargs)
        return self


class BoxplotVisualization(PlotlyStatVisualization):
    """Box plot visualization using Plotly."""

    def render(self) -> go.Figure:
        """Render a box plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Prepare color
        color = self.config.get('color')
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Create figure
        fig = self._create_figure()

        if x is not None and y is not None:
            # Grouped boxplot
            for i, (group_name, group_df) in enumerate(df.groupby(x)):
                fig.add_trace(go.Box(
                    y=group_df[y].dropna(),
                    name=str(group_name),
                    marker_color=color,
                    boxmean='sd'
                ))
        elif y is not None:
            # Single boxplot or multiple columns
            if isinstance(y, str):
                fig.add_trace(go.Box(
                    y=df[y].dropna(),
                    name=y,
                    marker_color=color,
                    boxmean='sd'
                ))
            else:
                for col in y:
                    fig.add_trace(go.Box(
                        y=df[col].dropna(),
                        name=col,
                        marker_color=color,
                        boxmean='sd'
                    ))
        else:
            # Use all numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                fig.add_trace(go.Box(
                    y=df[col].dropna(),
                    name=col,
                    marker_color=color,
                    boxmean='sd'
                ))

        # Apply styling
        self._apply_styling(fig)

        self._figure = fig
        return fig


class ViolinVisualization(PlotlyStatVisualization):
    """Violin plot visualization using Plotly."""

    def render(self) -> go.Figure:
        """Render a violin plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Prepare color
        color = self.config.get('color')
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Create figure
        fig = self._create_figure()

        if x is not None and y is not None:
            # Grouped violin plot
            for group_name, group_df in df.groupby(x):
                fig.add_trace(go.Violin(
                    y=group_df[y].dropna(),
                    name=str(group_name),
                    marker_color=color,
                    box_visible=True,
                    meanline_visible=True
                ))
        elif y is not None:
            # Single violin or multiple columns
            if isinstance(y, str):
                fig.add_trace(go.Violin(
                    y=df[y].dropna(),
                    name=y,
                    marker_color=color,
                    box_visible=True,
                    meanline_visible=True
                ))
            else:
                for col in y:
                    fig.add_trace(go.Violin(
                        y=df[col].dropna(),
                        name=col,
                        marker_color=color,
                        box_visible=True,
                        meanline_visible=True
                    ))
        else:
            # Use all numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                fig.add_trace(go.Violin(
                    y=df[col].dropna(),
                    name=col,
                    marker_color=color,
                    box_visible=True,
                    meanline_visible=True
                ))

        # Apply styling
        self._apply_styling(fig)

        self._figure = fig
        return fig


class HeatmapVisualization(PlotlyStatVisualization):
    """Heatmap visualization using Plotly."""

    def render(self) -> go.Figure:
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

        # Get colorscale
        colorscale = self.config.get('colorscale', get_config('colorscale', 'plotly'))

        # Create figure
        fig = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale=colorscale,
            colorbar=dict(title=self.config.get('ylabel', value or 'Value'))
        ))

        # Apply styling
        self._apply_styling(fig)

        self._figure = fig
        return fig


class CorrelationVisualization(PlotlyStatVisualization):
    """Correlation matrix heatmap visualization using Plotly."""

    def render(self) -> go.Figure:
        """Render a correlation matrix heatmap."""
        df = convert_to_dataframe(self.data)

        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            raise ValueError("No numeric data found for correlation matrix")

        # Compute correlation matrix
        corr = numeric_df.corr()

        # Get colorscale
        colorscale = self.config.get('colorscale', 'RdBu')

        # Get annotation setting
        annot = self.config.get('annot', False)

        # Create figure
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            colorscale=colorscale,
            zmid=0,
            zmin=-1,
            zmax=1,
            colorbar=dict(title='Correlation'),
            text=np.round(corr.values, 2) if annot else None,
            texttemplate='%{text}' if annot else None,
            textfont={"size": 10} if annot else None
        ))

        # Apply styling
        self._apply_styling(fig)

        self._figure = fig
        return fig


class DensityVisualization(PlotlyStatVisualization):
    """Density plot (KDE) visualization using Plotly."""

    def render(self) -> go.Figure:
        """Render a density plot."""
        df = convert_to_dataframe(self.data)

        x = self.config.get('x')
        y = self.config.get('y')

        # Determine columns to use
        if x is None and y is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                raise ValueError("No numeric columns found for density plot")
            x = numeric_cols[0]

        # Get color
        color = self.config.get('color')
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Create figure
        fig = self._create_figure()

        if y is None:
            # 1D KDE
            x_data = df[x].dropna()

            fig.add_trace(go.Histogram(
                x=x_data,
                histnorm='probability density',
                name=x if isinstance(x, str) else 'value',
                marker_color=color,
                nbinsx=50
            ))

            # Try to add KDE line
            try:
                from scipy import stats
                xmin, xmax = x_data.min(), x_data.max()
                xx = np.linspace(xmin, xmax, 200)
                kernel = stats.gaussian_kde(x_data)
                zz = kernel(xx)

                fig.add_trace(go.Scatter(
                    x=xx,
                    y=zz,
                    mode='lines',
                    name='KDE',
                    line=dict(color='red', width=2)
                ))
            except ImportError:
                pass
        else:
            # 2D KDE
            x_data = df[x].dropna()
            y_data = df[y].dropna()

            # Try to use scipy for KDE
            try:
                from scipy import stats

                xmin, xmax = x_data.min(), x_data.max()
                ymin, ymax = y_data.min(), y_data.max()
                xx, yy = np.mgrid[xmin:xmax:50j, ymin:ymax:50j]

                values = np.vstack([x_data, y_data])
                kernel = stats.gaussian_kde(values)
                positions = np.vstack([xx.ravel(), yy.ravel()])
                z = np.reshape(kernel(positions).T, xx.shape)

                fig.add_trace(go.Contour(
                    x=xx[0, :],
                    y=yy[:, 0],
                    z=z,
                    colorscale=self.config.get('colorscale', 'viridis'),
                    contours=dict(
                        showlabels=True,
                        labelfont=dict(size=10, color='white')
                    )
                ))

                fig.add_trace(go.Scatter(
                    x=x_data,
                    y=y_data,
                    mode='markers',
                    marker=dict(color=color, size=5, opacity=0.5),
                    name='data'
                ))

            except ImportError:
                # Fallback to 2D histogram
                fig.add_trace(go.Histogram2d(
                    x=x_data,
                    y=y_data,
                    colorscale=self.config.get('colorscale', 'viridis'),
                    nbinsx=50,
                    nbinsy=50
                ))

        # Apply styling
        if 'xlabel' not in self.config and x is not None:
            self.config['xlabel'] = x
        if 'ylabel' not in self.config:
            if y is not None:
                self.config['ylabel'] = y
            else:
                self.config['ylabel'] = 'Density'

        self._apply_styling(fig)

        self._figure = fig
        return fig


class RegressionVisualization(PlotlyStatVisualization):
    """Regression plot visualization using Plotly."""

    def render(self) -> go.Figure:
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

        # Get data
        x_data = get_column_data(df, x)
        y_data = get_column_data(df, y)

        # Remove NaN values
        mask = ~(np.isnan(x_data) | np.isnan(y_data))
        x_data = x_data[mask]
        y_data = y_data[mask]

        # Get color
        color = self.config.get('color')
        if color is None:
            colors = get_color_sequence(1)
            color = colors[0]

        # Get confidence interval setting
        show_ci = self.config.get('ci', True)

        # Create figure
        fig = self._create_figure()

        # Add scatter plot
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            marker=dict(color=color, size=8, opacity=0.6),
            name='data'
        ))

        # Fit and plot regression line
        try:
            from scipy import stats

            # Linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
            line_x = np.array([x_data.min(), x_data.max()])
            line_y = slope * line_x + intercept

            # Add regression line
            fig.add_trace(go.Scatter(
                x=line_x,
                y=line_y,
                mode='lines',
                line=dict(color='red', width=2),
                name=f'y = {slope:.2f}x + {intercept:.2f}<br>R² = {r_value**2:.3f}'
            ))

            # Add confidence interval if requested
            if show_ci and len(x_data) > 2:
                # Calculate prediction interval
                predict_y = slope * x_data + intercept
                residuals = y_data - predict_y
                std_residuals = np.std(residuals)

                # 95% confidence interval
                ci = 1.96 * std_residuals
                fig.add_trace(go.Scatter(
                    x=line_x,
                    y=line_y + ci,
                    mode='lines',
                    line=dict(color='red', width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                fig.add_trace(go.Scatter(
                    x=line_x,
                    y=line_y - ci,
                    mode='lines',
                    line=dict(color='red', width=0),
                    fill='tonexty',
                    fillcolor='rgba(255,0,0,0.2)',
                    showlegend=False,
                    hoverinfo='skip'
                ))

        except ImportError:
            # Fallback: simple line through endpoints
            fig.add_trace(go.Scatter(
                x=[x_data.min(), x_data.max()],
                y=[y_data.min(), y_data.max()],
                mode='lines',
                line=dict(color='red', width=2),
                name='trend'
            ))

        # Apply styling
        self._apply_styling(fig)

        self._figure = fig
        return fig


# Factory functions

def boxplot_plot(data: Any, **kwargs) -> BoxplotVisualization:
    """Create a box plot visualization using Plotly."""
    return BoxplotVisualization(data, **kwargs)


def violin_plot(data: Any, **kwargs) -> ViolinVisualization:
    """Create a violin plot visualization using Plotly."""
    return ViolinVisualization(data, **kwargs)


def heatmap_plot(data: Any, **kwargs) -> HeatmapVisualization:
    """Create a heatmap visualization using Plotly."""
    return HeatmapVisualization(data, **kwargs)


def corr_plot(data: Any, **kwargs) -> CorrelationVisualization:
    """Create a correlation matrix heatmap visualization using Plotly."""
    return CorrelationVisualization(data, **kwargs)


def density_plot(data: Any, **kwargs) -> DensityVisualization:
    """Create a density plot visualization using Plotly."""
    return DensityVisualization(data, **kwargs)


def regression_plot(data: Any, **kwargs) -> RegressionVisualization:
    """Create a regression plot visualization using Plotly."""
    return RegressionVisualization(data, **kwargs)
