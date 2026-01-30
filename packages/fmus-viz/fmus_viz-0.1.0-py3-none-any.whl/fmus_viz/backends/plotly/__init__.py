"""
Plotly backend for fmus-viz.

This module provides a Plotly backend for creating interactive visualizations.
"""

from fmus_viz.core.registry import register_backend, register_visualization
from fmus_viz.backends.plotly.basic import (
    bar_plot,
    barh_plot,
    line_plot,
    scatter_plot,
    histogram_plot,
    pie_plot,
    area_plot
)
from fmus_viz.backends.plotly.statistical import (
    boxplot_plot,
    violin_plot,
    heatmap_plot,
    corr_plot,
    density_plot,
    regression_plot
)

# First register the backend itself
register_backend('plotly', is_default=False)

# Register visualizations - basic charts
register_visualization('bar', 'plotly', bar_plot)
register_visualization('barh', 'plotly', barh_plot)
register_visualization('line', 'plotly', line_plot)
register_visualization('scatter', 'plotly', scatter_plot)
register_visualization('histogram', 'plotly', histogram_plot)
register_visualization('pie', 'plotly', pie_plot)
register_visualization('area', 'plotly', area_plot)

# Register visualizations - statistical charts
register_visualization('boxplot', 'plotly', boxplot_plot)
register_visualization('violin', 'plotly', violin_plot)
register_visualization('heatmap', 'plotly', heatmap_plot)
register_visualization('corr', 'plotly', corr_plot)
register_visualization('density', 'plotly', density_plot)
register_visualization('regression', 'plotly', regression_plot)

# Default configuration
DEFAULT_CONFIG = {
    'dpi': 100,
    'figsize': (10, 6),
    'template': 'plotly',
    'show_grid': True,
    'colorscale': 'viridis',
    'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50}
}

# Register backend configuration
from fmus_viz.core.config import set_config

# Apply default configuration for Plotly backend
for key, value in DEFAULT_CONFIG.items():
    set_config(key, value, 'plotly')
