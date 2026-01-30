"""
Core functionality for fmus-viz.
"""

from fmus_viz.core.base import (
    Visualization,
    ChartVisualization,
    StatisticalVisualization,
    GeoVisualization,
    NetworkVisualization,
    ThreeDVisualization
)
from fmus_viz.core.config import (
    get_config,
    set_config,
    reset_config,
    set_theme,
    get_theme,
    set_figure_size,
    get_figure_size,
    set_interactive,
    is_interactive,
    set_colormap,
    get_colormap
)
from fmus_viz.core.registry import (
    register_backend,
    set_backend,
    get_backend,
    get_current_backend_name,
    register_visualization,
    get_visualization_implementation,
    list_backends,
    list_available_backends,
    list_visualization_types
)
from fmus_viz.core.utils import (
    convert_to_dataframe,
    get_column_data,
    infer_x_y_columns,
    standardize_color_input,
    downsample_data,
    parse_color_argument,
    infer_categorical_columns
)

__all__ = [
    # Base classes
    'Visualization',
    'ChartVisualization',
    'StatisticalVisualization',
    'GeoVisualization',
    'NetworkVisualization',
    'ThreeDVisualization',

    # Configuration
    'get_config',
    'set_config',
    'reset_config',
    'set_theme',
    'get_theme',
    'set_figure_size',
    'get_figure_size',
    'set_interactive',
    'is_interactive',
    'set_colormap',
    'get_colormap',

    # Registry
    'register_backend',
    'set_backend',
    'get_backend',
    'get_current_backend_name',
    'register_visualization',
    'get_visualization_implementation',
    'list_backends',
    'list_available_backends',
    'list_visualization_types',

    # Utilities
    'convert_to_dataframe',
    'get_column_data',
    'infer_x_y_columns',
    'standardize_color_input',
    'downsample_data',
    'parse_color_argument',
    'infer_categorical_columns'
]
