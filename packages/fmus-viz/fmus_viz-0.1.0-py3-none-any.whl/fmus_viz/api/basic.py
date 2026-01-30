from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fmus_viz.core.registry import get_visualization_implementation


def bar(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a bar chart.

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'category': ['A', 'B', 'C'], 'value': [10, 15, 7]})
        >>> viz.bar(data, x='category', y='value')
        >>> viz.bar(data, x='category', y='value').title('My Bar Chart').show()
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('bar')

    # Atur parameter ke implementation
    kwargs['x'] = x
    kwargs['y'] = y

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)


def barh(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a horizontal bar chart.

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'category': ['A', 'B', 'C'], 'value': [10, 15, 7]})
        >>> viz.barh(data, x='category', y='value')
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('barh')

    # Atur parameter ke implementation
    kwargs['x'] = x
    kwargs['y'] = y

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)


def line(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a line chart.

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [10, 15, 7, 12, 9]})
        >>> viz.line(data, x='x', y='y')
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('line')

    # Atur parameter ke implementation
    kwargs['x'] = x
    kwargs['y'] = y

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)


def scatter(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a scatter plot.

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [10, 15, 7, 12, 9]})
        >>> viz.scatter(data, x='x', y='y')
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('scatter')

    # Atur parameter ke implementation
    kwargs['x'] = x
    kwargs['y'] = y

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)


def histogram(
    data: Any,
    value: Optional[str] = None,
    bins: int = 10,
    **kwargs
) -> Any:
    """
    Create a histogram.

    Args:
        data: Data to visualize
        value: Name of the column to use for values
        bins: Number of bins
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'value': [1, 2, 2, 3, 3, 3, 4, 4, 5]})
        >>> viz.histogram(data, value='value', bins=5)
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('histogram')

    # Atur parameter ke implementation
    kwargs['value'] = value
    kwargs['bins'] = bins

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)


def pie(
    data: Any,
    values: Optional[str] = None,
    labels: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create a pie chart.

    Args:
        data: Data to visualize
        values: Name of the column to use for values
        labels: Name of the column to use for labels
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'category': ['A', 'B', 'C'], 'value': [10, 15, 7]})
        >>> viz.pie(data, values='value', labels='category')
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('pie')

    # Atur parameter ke implementation
    kwargs['values'] = values
    kwargs['labels'] = labels

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)


def area(
    data: Any,
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> Any:
    """
    Create an area chart.

    Args:
        data: Data to visualize
        x: Name of the column to use for x-axis
        y: Name of the column to use for y-axis
        **kwargs: Additional configuration parameters

    Returns:
        Visualization object with method chaining support

    Examples:
        >>> import fmus_viz as viz
        >>> import pandas as pd
        >>> data = pd.DataFrame({'x': [1, 2, 3, 4, 5], 'y': [10, 15, 7, 12, 9]})
        >>> viz.area(data, x='x', y='y')
    """
    # Dapatkan implementasi backend dari registry
    implementation = get_visualization_implementation('area')

    # Atur parameter ke implementation
    kwargs['x'] = x
    kwargs['y'] = y

    # Buat visualisasi dengan backend
    return implementation(data, **kwargs)
