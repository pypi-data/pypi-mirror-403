"""
fmus-viz: A Human-Oriented Visualization Library

A unified, intuitive interface over multiple visualization backends.
"""

from importlib.metadata import PackageNotFoundError, version

# Import core functions
from fmus_viz.core.config import (
    get_config,
    set_config,
    reset_config,
    set_theme,
    set_figure_size,
    set_interactive,
    set_colormap
)
from fmus_viz.core.registry import (
    set_backend,
    get_current_backend_name,
    list_backends,
    list_available_backends
)

# Import API functions
from fmus_viz.api import (
    area,
    bar,
    barh,
    histogram,
    line,
    pie,
    scatter,
    boxplot,
    corr,
    density,
    heatmap,
    regression,
    violin
)

# Try to get version from package metadata
try:
    __version__ = version("fmus-viz")
except PackageNotFoundError:
    # Package is not installed
    try:
        from fmus_viz._version import version as __version__
    except ImportError:
        __version__ = "0.1.0"

# Expose API functions
__all__ = [
    # Core functions
    'get_config',
    'set_config',
    'reset_config',
    'set_theme',
    'set_figure_size',
    'set_interactive',
    'set_colormap',
    'set_backend',
    'get_current_backend_name',
    'list_backends',
    'list_available_backends',

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
