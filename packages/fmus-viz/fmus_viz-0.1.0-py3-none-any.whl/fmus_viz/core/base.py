from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


class Visualization(abc.ABC):
    """
    Base class for all visualizations.

    This abstract class defines the interface that all visualization types must implement.

    Attributes:
        data: The data to visualize
        config: Configuration dictionary for visualization settings
        _backend: The backend visualization object
    """

    def __init__(self, data: Any, **kwargs) -> None:
        """
        Initialize a visualization object.

        Args:
            data: Data to visualize (DataFrame, array, list, etc.)
            **kwargs: Additional configuration parameters
        """
        self.data = self._validate_data(data)
        self.config = kwargs
        self._backend = None
        self._figure = None

    @staticmethod
    def _validate_data(data: Any) -> Any:
        """
        Validates and potentially transforms input data.

        Args:
            data: Input data to validate

        Returns:
            Validated/transformed data ready for visualization

        Raises:
            ValueError: If data format is invalid
        """
        # Jika data adalah dict, ubah menjadi DataFrame
        if isinstance(data, dict):
            return pd.DataFrame(data)

        # Jika data adalah list, coba ubah menjadi DataFrame atau array
        if isinstance(data, list):
            try:
                return pd.DataFrame(data)
            except Exception:
                return np.array(data)

        # DataFrame, Series, atau array dapat digunakan langsung
        if isinstance(data, (pd.DataFrame, pd.Series, np.ndarray)):
            return data

        # Jika format lain, coba konversi ke array
        try:
            return np.array(data)
        except Exception as e:
            raise ValueError(f"Unsupported data format. Error: {str(e)}")

    @abc.abstractmethod
    def render(self) -> Any:
        """
        Render the visualization with the current backend.

        This method must be implemented by all visualization subclasses.

        Returns:
            The rendered visualization object
        """
        pass

    def show(self) -> Any:
        """
        Display the visualization.

        Returns:
            The visualization object for method chaining
        """
        if self._figure is None:
            self._figure = self.render()

        return self

    def save(self, filename: str, **kwargs) -> Visualization:
        """
        Save the visualization to a file.

        Args:
            filename: Path to save the visualization
            **kwargs: Additional save options

        Returns:
            The visualization object for method chaining
        """
        if self._figure is None:
            self._figure = self.render()

        # Implementing actual save methods will be backend-specific
        return self

    # Common customization methods that use method chaining
    def title(self, title: str) -> Visualization:
        """
        Set the title of the visualization.

        Args:
            title: The title text

        Returns:
            The visualization object for method chaining
        """
        self.config["title"] = title
        return self

    def xlabel(self, label: str) -> Visualization:
        """
        Set the x-axis label.

        Args:
            label: The x-axis label text

        Returns:
            The visualization object for method chaining
        """
        self.config["xlabel"] = label
        return self

    def ylabel(self, label: str) -> Visualization:
        """
        Set the y-axis label.

        Args:
            label: The y-axis label text

        Returns:
            The visualization object for method chaining
        """
        self.config["ylabel"] = label
        return self

    def color(self, value: Union[str, List[str]]) -> Visualization:
        """
        Set the color for the visualization.

        Args:
            value: Color value(s) to use

        Returns:
            The visualization object for method chaining
        """
        self.config["color"] = value
        return self

    def legend(self, show: bool = True, **kwargs) -> Visualization:
        """
        Configure the legend.

        Args:
            show: Whether to show the legend
            **kwargs: Additional legend configuration

        Returns:
            The visualization object for method chaining
        """
        self.config["legend"] = {"show": show, **kwargs}
        return self

    def grid(self, show: bool = True, **kwargs) -> Visualization:
        """
        Configure the grid.

        Args:
            show: Whether to show the grid
            **kwargs: Additional grid configuration

        Returns:
            The visualization object for method chaining
        """
        self.config["grid"] = {"show": show, **kwargs}
        return self

    def theme(self, name: str) -> Visualization:
        """
        Apply a theme to the visualization.

        Args:
            name: Name of the theme to apply

        Returns:
            The visualization object for method chaining
        """
        self.config["theme"] = name
        return self

    def width(self, value: Union[int, float]) -> Visualization:
        """
        Set the width of the visualization.

        Args:
            value: Width value

        Returns:
            The visualization object for method chaining
        """
        self.config["width"] = value
        return self

    def height(self, value: Union[int, float]) -> Visualization:
        """
        Set the height of the visualization.

        Args:
            value: Height value

        Returns:
            The visualization object for method chaining
        """
        self.config["height"] = value
        return self

    def size(self, value: Union[int, float, Tuple[int, int]]) -> Visualization:
        """
        Set the size of the visualization.

        Args:
            value: Size value or tuple of (width, height)

        Returns:
            The visualization object for method chaining
        """
        if isinstance(value, tuple) and len(value) == 2:
            self.config["width"] = value[0]
            self.config["height"] = value[1]
        else:
            self.config["size"] = value
        return self


class ChartVisualization(Visualization):
    """
    Base class for chart-type visualizations.

    Extends the base Visualization class with common chart functionality.
    """

    def __init__(
        self,
        data: Any,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        **kwargs
    ) -> None:
        """
        Initialize a chart visualization.

        Args:
            data: Data to visualize
            x: Name of the column to use for x-axis
            y: Name of the column(s) to use for y-axis
            **kwargs: Additional configuration parameters
        """
        super().__init__(data, **kwargs)

        self.config["x"] = x
        self.config["y"] = y


class StatisticalVisualization(Visualization):
    """
    Base class for statistical visualizations.

    Extends the base Visualization class with functionality specific to statistical plots.
    """

    def __init__(self, data: Any, **kwargs) -> None:
        """
        Initialize a statistical visualization.

        Args:
            data: Data to visualize
            **kwargs: Additional configuration parameters
        """
        super().__init__(data, **kwargs)


class GeoVisualization(Visualization):
    """
    Base class for geospatial visualizations.

    Extends the base Visualization class with functionality specific to geospatial plots.
    """

    def __init__(self, data: Any, **kwargs) -> None:
        """
        Initialize a geospatial visualization.

        Args:
            data: Data to visualize
            **kwargs: Additional configuration parameters
        """
        super().__init__(data, **kwargs)


class NetworkVisualization(Visualization):
    """
    Base class for network/graph visualizations.

    Extends the base Visualization class with functionality specific to network plots.
    """

    def __init__(self, data: Any, **kwargs) -> None:
        """
        Initialize a network visualization.

        Args:
            data: Data to visualize
            **kwargs: Additional configuration parameters
        """
        super().__init__(data, **kwargs)


class ThreeDVisualization(Visualization):
    """
    Base class for 3D visualizations.

    Extends the base Visualization class with functionality specific to 3D plots.
    """

    def __init__(self, data: Any, **kwargs) -> None:
        """
        Initialize a 3D visualization.

        Args:
            data: Data to visualize
            **kwargs: Additional configuration parameters
        """
        super().__init__(data, **kwargs)

    def zlabel(self, label: str) -> ThreeDVisualization:
        """
        Set the z-axis label.

        Args:
            label: The z-axis label text

        Returns:
            The visualization object for method chaining
        """
        self.config["zlabel"] = label
        return self
