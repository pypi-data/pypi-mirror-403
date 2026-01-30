"""
Seaborn backend for fmus-viz.

This module provides a Seaborn backend for creating statistical visualizations.
"""

from fmus_viz.core.registry import register_backend, register_visualization
from fmus_viz.backends.seaborn.basic import (
    bar_plot,
    barh_plot,
    line_plot,
    scatter_plot,
    histogram_plot,
    area_plot
)
from fmus_viz.backends.seaborn.statistical import (
    boxplot_plot,
    violin_plot,
    heatmap_plot,
    corr_plot,
    density_plot,
    regression_plot
)

# First register the backend itself
register_backend('seaborn', is_default=False)

# Register visualizations - basic charts
register_visualization('bar', 'seaborn', bar_plot)
register_visualization('barh', 'seaborn', barh_plot)
register_visualization('line', 'seaborn', line_plot)
register_visualization('scatter', 'seaborn', scatter_plot)
register_visualization('histogram', 'seaborn', histogram_plot)
register_visualization('area', 'seaborn', area_plot)

# Register visualizations - statistical charts
register_visualization('boxplot', 'seaborn', boxplot_plot)
register_visualization('violin', 'seaborn', violin_plot)
register_visualization('heatmap', 'seaborn', heatmap_plot)
register_visualization('corr', 'seaborn', corr_plot)
register_visualization('density', 'seaborn', density_plot)
register_visualization('regression', 'seaborn', regression_plot)

# Default configuration
DEFAULT_CONFIG = {
    'dpi': 100,
    'figsize': (8, 6),
    'style': 'whitegrid',
    'context': 'notebook',
    'show_grid': True,
    'palette': 'deep',
    'interactive': False
}

# Register backend configuration
from fmus_viz.core.config import set_config

# Apply default configuration for Seaborn backend
for key, value in DEFAULT_CONFIG.items():
    set_config(key, value, 'seaborn')
