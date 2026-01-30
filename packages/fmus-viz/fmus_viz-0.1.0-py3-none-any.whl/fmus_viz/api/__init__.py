"""
API functions for fmus-viz.

This package contains the user-facing API functions for creating visualizations.
"""

from fmus_viz.api.basic import (
    area,
    bar,
    barh,
    histogram,
    line,
    pie,
    scatter
)
from fmus_viz.api.statistical import (
    boxplot,
    corr,
    density,
    heatmap,
    regression,
    violin
)

__all__ = [
    # Basic chart types
    'area',
    'bar',
    'barh',
    'histogram',
    'line',
    'pie',
    'scatter',
    # Statistical chart types
    'boxplot',
    'corr',
    'density',
    'heatmap',
    'regression',
    'violin'
]

# API functions will be imported and exposed here
# These will be implemented when we create the API modules
