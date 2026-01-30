from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fmus_viz.core.registry import get_visualization_implementation


def boxplot(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a box plot.

    Args:
        data: Data to visualize
        x: Name of the column to use for grouping (optional)
        y: Name of the column to use for values
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'group': ['A', 'A', 'B', 'B'], 'value': [1, 2, 3, 4]})
        >>> viz.boxplot(data, x='group', y='value')
        >>> viz.boxplot(data, y='value').title('My Boxplot').show()
    """
    implementation = get_visualization_implementation('boxplot')
    kwargs['x'] = x
    kwargs['y'] = y
    return implementation(data, **kwargs)


def violin(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a violin plot.

    Args:
        data: Data to visualize
        x: Name of the column to use for grouping (optional)
        y: Name of the column to use for values
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'group': ['A', 'A', 'B', 'B'], 'value': [1, 2, 3, 4]})
        >>> viz.violin(data, x='group', y='value')
    """
    implementation = get_visualization_implementation('violin')
    kwargs['x'] = x
    kwargs['y'] = y
    return implementation(data, **kwargs)


def heatmap(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    value: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a heatmap.

    Args:
        data: Data to visualize (DataFrame or matrix-like)
        x: Name of the column to use for x-axis (optional)
        y: Name of the column to use for y-axis (optional)
        value: Name of the column to use for values (optional)
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> import numpy as np
        >>> data = pd.DataFrame(np.random.rand(5, 5))
        >>> viz.heatmap(data)
        >>> data = pd.DataFrame({'x': ['A', 'B'], 'y': ['C', 'D'], 'value': [1, 2]})
        >>> viz.heatmap(data, x='x', y='y', value='value')
    """
    implementation = get_visualization_implementation('heatmap')
    kwargs['x'] = x
    kwargs['y'] = y
    kwargs['value'] = value
    return implementation(data, **kwargs)


def corr(
    data: Any,
    annot: bool = False,
    **kwargs
) -> Any:
    """
    Create a correlation matrix heatmap.

    Args:
        data: Data to visualize (DataFrame with numeric columns)
        annot: Whether to annotate cells with correlation values
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9]})
        >>> viz.corr(data)
        >>> viz.corr(data, annot=True).title('Correlation Matrix').show()
    """
    implementation = get_visualization_implementation('corr')
    kwargs['annot'] = annot
    return implementation(data, **kwargs)


def density(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a density plot (KDE).

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis (optional, for 2D KDE)
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'value': [1, 2, 2, 3, 3, 3, 4, 4, 5]})
        >>> viz.density(data, x='value')
        >>> data = pd.DataFrame({'x': [1, 2, 3, 4], 'y': [2, 3, 4, 5]})
        >>> viz.density(data, x='x', y='y')
    """
    implementation = get_visualization_implementation('density')
    kwargs['x'] = x
    kwargs['y'] = y
    return implementation(data, **kwargs)


def regression(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    ci: bool = True,
    **kwargs
) -> Any:
    """
    Create a regression plot with fitted line.

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis
        ci: Whether to show confidence interval
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [2, 4, 5, 4, 5]})
        >>> viz.regression(data, x='x', y='y')
        >>> viz.regression(data, x='x', y='y', ci=False).show()
    """
    implementation = get_visualization_implementation('regression')
    kwargs['x'] = x
    kwargs['y'] = y
    kwargs['ci'] = ci
    return implementation(data, **kwargs)
