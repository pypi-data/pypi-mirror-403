from __future__ import annotations

import importlib
import os
from typing import Any, Callable, Dict, List, Optional, Type, Union

# Backend registry to store all registered backends
_BACKENDS: Dict[str, Dict[str, Any]] = {}

# Current active backend name
_CURRENT_BACKEND: str = None

# Default backend to use when none is specified
_DEFAULT_BACKEND: str = None

# Mapping of visualization types to backend-specific implementations
_VISUALIZATION_REGISTRY: Dict[str, Dict[str, Callable]] = {}


def register_backend(
    name: str,
    module: str = None,
    package: Optional[str] = None,
    is_default: bool = False
) -> None:
    """
    Register a visualization backend.

    Args:
        name: Name of the backend
        module: Module path for the backend
        package: Package name for the backend
        is_default: Whether to set this as the default backend

    Raises:
        ImportError: If the backend cannot be imported
    """
    # Jika module path diberikan, coba impor backend
    if module:
        try:
            backend_module = importlib.import_module(module, package=package)
            _BACKENDS[name] = {
                "module": backend_module,
                "package": package,
                "enabled": True,
            }
        except ImportError as e:
            _BACKENDS[name] = {
                "module": None,
                "package": package,
                "enabled": False,
                "error": str(e),
            }
            raise ImportError(f"Backend '{name}' could not be imported: {str(e)}")
    else:
        # Jika tidak ada module path, daftarkan sebagai placeholder
        _BACKENDS[name] = {
            "module": None,
            "package": package,
            "enabled": False,
        }

    # Set sebagai backend default jika diminta atau jika ini adalah backend pertama
    global _DEFAULT_BACKEND, _CURRENT_BACKEND
    if is_default or _DEFAULT_BACKEND is None:
        _DEFAULT_BACKEND = name

    # Set sebagai backend aktif jika belum ada yang aktif
    if _CURRENT_BACKEND is None:
        _CURRENT_BACKEND = name


def set_backend(name: str) -> None:
    """
    Set the active visualization backend.

    Args:
        name: Name of the backend to activate

    Raises:
        ValueError: If the backend is not registered or not available
    """
    if name not in _BACKENDS:
        raise ValueError(f"Backend '{name}' is not registered. Available backends: {list(_BACKENDS.keys())}")

    if not _BACKENDS[name].get("enabled", False) and _BACKENDS[name].get("module") is None:
        # Coba load backend jika belum diload
        try:
            backend_info = _BACKENDS[name]
            if backend_info.get("package"):
                module_name = f"{backend_info['package']}.{name}"
            else:
                module_name = f"fmus_viz.backends.{name}"

            backend_module = importlib.import_module(module_name)
            _BACKENDS[name]["module"] = backend_module
            _BACKENDS[name]["enabled"] = True
        except ImportError as e:
            _BACKENDS[name]["error"] = str(e)
            raise ValueError(f"Backend '{name}' is not available: {str(e)}")

    global _CURRENT_BACKEND
    _CURRENT_BACKEND = name


def get_backend(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the backend information.

    Args:
        name: Name of the backend to get, or None for the current backend

    Returns:
        Backend information dictionary

    Raises:
        ValueError: If the backend is not registered or no backend is active
    """
    # Gunakan current backend jika name tidak diberikan
    if name is None:
        if _CURRENT_BACKEND is None:
            if _DEFAULT_BACKEND is None:
                raise ValueError("No active backend and no default backend set")
            set_backend(_DEFAULT_BACKEND)
        name = _CURRENT_BACKEND

    if name not in _BACKENDS:
        raise ValueError(f"Backend '{name}' is not registered. Available backends: {list(_BACKENDS.keys())}")

    return _BACKENDS[name]


def get_current_backend_name() -> str:
    """
    Get the name of the current active backend.

    Returns:
        Name of the current backend

    Raises:
        ValueError: If no backend is active
    """
    if _CURRENT_BACKEND is None:
        if _DEFAULT_BACKEND is None:
            raise ValueError("No active backend and no default backend set")
        set_backend(_DEFAULT_BACKEND)

    return _CURRENT_BACKEND


def register_visualization(
    vis_type: str,
    backend_name: str,
    implementation: Callable
) -> None:
    """
    Register a backend implementation for a visualization type.

    Args:
        vis_type: Type of visualization (e.g., 'bar', 'line', 'scatter')
        backend_name: Name of the backend
        implementation: Function that implements the visualization
    """
    if vis_type not in _VISUALIZATION_REGISTRY:
        _VISUALIZATION_REGISTRY[vis_type] = {}

    _VISUALIZATION_REGISTRY[vis_type][backend_name] = implementation


def get_visualization_implementation(
    vis_type: str,
    backend_name: Optional[str] = None
) -> Callable:
    """
    Get the implementation function for a visualization type.

    Args:
        vis_type: Type of visualization
        backend_name: Name of the backend, or None for the current backend

    Returns:
        Implementation function

    Raises:
        ValueError: If no implementation is found for the visualization type and backend
    """
    if backend_name is None:
        backend_name = get_current_backend_name()

    if vis_type not in _VISUALIZATION_REGISTRY:
        raise ValueError(f"Visualization type '{vis_type}' is not registered")

    if backend_name not in _VISUALIZATION_REGISTRY[vis_type]:
        raise ValueError(f"Backend '{backend_name}' does not implement visualization type '{vis_type}'")

    return _VISUALIZATION_REGISTRY[vis_type][backend_name]


def list_backends() -> List[str]:
    """
    List all registered backends.

    Returns:
        List of backend names
    """
    return list(_BACKENDS.keys())


def list_available_backends() -> List[str]:
    """
    List all available backends (backends that can be loaded).

    Returns:
        List of available backend names
    """
    return [name for name, info in _BACKENDS.items() if info.get("enabled", False)]


def list_visualization_types() -> List[str]:
    """
    List all registered visualization types.

    Returns:
        List of visualization type names
    """
    return list(_VISUALIZATION_REGISTRY.keys())


# Auto-register built-in backends on import
def _auto_register_backends():
    """
    Automatically register built-in backends based on available packages.
    """
    # Matplotlib
    try:
        import matplotlib
        register_backend("matplotlib", "fmus_viz.backends.matplotlib", is_default=True)
    except ImportError:
        register_backend("matplotlib", is_default=False)

    # Plotly
    try:
        import plotly
        register_backend("plotly", "fmus_viz.backends.plotly")
    except ImportError:
        register_backend("plotly")

    # Seaborn (depends on matplotlib)
    try:
        import seaborn
        register_backend("seaborn", "fmus_viz.backends.seaborn")
    except ImportError:
        register_backend("seaborn")

    # Bokeh
    try:
        import bokeh
        register_backend("bokeh", "fmus_viz.backends.bokeh")
    except ImportError:
        register_backend("bokeh")

    # Altair
    try:
        import altair
        register_backend("altair", "fmus_viz.backends.altair")
    except ImportError:
        register_backend("altair")


# Initialize backends when this module is imported
_auto_register_backends()
