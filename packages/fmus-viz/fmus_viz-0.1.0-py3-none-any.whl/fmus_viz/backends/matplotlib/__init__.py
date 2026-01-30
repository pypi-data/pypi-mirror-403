"""
Matplotlib backend for fmus-viz.
"""

import matplotlib

from fmus_viz.core.registry import register_backend, register_visualization
from fmus_viz.backends.matplotlib.basic import (
    bar_plot,
    line_plot,
    scatter_plot,
    histogram_plot,
    pie_plot,
    area_plot,
    barh_plot
)
from fmus_viz.backends.matplotlib.statistical import (
    boxplot_plot,
    violin_plot,
    heatmap_plot,
    corr_plot,
    density_plot,
    regression_plot
)

# First register the backend itself
register_backend('matplotlib', is_default=True)

# Register implementations - basic charts
register_visualization('bar', 'matplotlib', bar_plot)
register_visualization('line', 'matplotlib', line_plot)
register_visualization('scatter', 'matplotlib', scatter_plot)
register_visualization('histogram', 'matplotlib', histogram_plot)
register_visualization('pie', 'matplotlib', pie_plot)
register_visualization('area', 'matplotlib', area_plot)
register_visualization('barh', 'matplotlib', barh_plot)

# Register implementations - statistical charts
register_visualization('boxplot', 'matplotlib', boxplot_plot)
register_visualization('violin', 'matplotlib', violin_plot)
register_visualization('heatmap', 'matplotlib', heatmap_plot)
register_visualization('corr', 'matplotlib', corr_plot)
register_visualization('density', 'matplotlib', density_plot)
register_visualization('regression', 'matplotlib', regression_plot)

# Default configuration
DEFAULT_CONFIG = {
    'dpi': 100,
    'figsize': (8, 6),
    'style': 'seaborn-whitegrid',
    'show_grid': True,
    'interactive': False
}

# Apply default configuration for Matplotlib backend
from fmus_viz.core.config import set_config
for key, value in DEFAULT_CONFIG.items():
    set_config(key, value, 'matplotlib')

# More visualizations will be registered as they are implemented
