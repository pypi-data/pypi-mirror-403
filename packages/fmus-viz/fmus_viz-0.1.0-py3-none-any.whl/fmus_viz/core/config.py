from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

# Global configuration dictionary
_CONFIG: Dict[str, Any] = {
    "theme": "default",
    "interactive": True,
    "dpi": 100,
    "figsize": (8, 6),
    "cmap": "viridis",
    "show_grid": True,
    "save_format": "png",
    "style": None,
    "font_size": 10,
    "title_size": 14,
    "label_size": 12,
    "tick_size": 10,
    "legend_loc": "best",
    "backend_defaults": {},
}

# Backend-specific configurations
_BACKEND_CONFIG: Dict[str, Dict[str, Any]] = {
    "matplotlib": {
        "style": "seaborn-whitegrid",
        "interactive": False,
    },
    "plotly": {
        "template": "plotly_white",
        "interactive": True,
    },
    "seaborn": {
        "style": "whitegrid",
        "context": "notebook",
    },
    "bokeh": {
        "output_backend": "webgl",
        "interactive": True,
    },
    "altair": {
        "renderer": "default",
    },
}


def get_config(key: Optional[str] = None, backend: Optional[str] = None, default: Any = None) -> Any:
    """
    Get configuration value.

    Args:
        key: Configuration key to get, or None for the entire config
        backend: Backend to get configuration for, or None for global config
        default: Default value to return if key is not found

    Returns:
        Configuration value(s)
    """
    if backend is not None:
        # Get backend-specific config
        if backend not in _BACKEND_CONFIG:
            _BACKEND_CONFIG[backend] = {}

        config = _BACKEND_CONFIG[backend]

        # Jika key ada, kembalikan nilai spesifik
        if key is not None:
            return config.get(key, _CONFIG.get(key, default))

        # Jika key None, gabungkan backend config dengan global config
        result = _CONFIG.copy()
        result.update(config)
        return result

    # Get global config
    if key is not None:
        return _CONFIG.get(key, default)

    return _CONFIG.copy()


def set_config(key: str, value: Any, backend: Optional[str] = None) -> None:
    """
    Set configuration value.

    Args:
        key: Configuration key to set
        value: Value to set
        backend: Backend to set configuration for, or None for global config
    """
    if backend is not None:
        # Set backend-specific config
        if backend not in _BACKEND_CONFIG:
            _BACKEND_CONFIG[backend] = {}

        _BACKEND_CONFIG[backend][key] = value
    else:
        # Set global config
        _CONFIG[key] = value


def reset_config(backend: Optional[str] = None) -> None:
    """
    Reset configuration to defaults.

    Args:
        backend: Backend to reset configuration for, or None for global config
    """
    if backend is not None:
        # Reset backend-specific config
        if backend in _BACKEND_CONFIG:
            _BACKEND_CONFIG[backend] = _BACKEND_CONFIG.get(backend, {}).copy()
    else:
        # Reset global config
        global _CONFIG
        _CONFIG = {
            "theme": "default",
            "interactive": True,
            "dpi": 100,
            "figsize": (8, 6),
            "cmap": "viridis",
            "show_grid": True,
            "save_format": "png",
            "style": None,
            "font_size": 10,
            "title_size": 14,
            "label_size": 12,
            "tick_size": 10,
            "legend_loc": "best",
            "backend_defaults": {},
        }


def set_theme(theme: str, backend: Optional[str] = None) -> None:
    """
    Set the visualization theme.

    Args:
        theme: Theme name
        backend: Backend to set theme for, or None for global
    """
    set_config("theme", theme, backend)


def get_theme(backend: Optional[str] = None) -> str:
    """
    Get the current visualization theme.

    Args:
        backend: Backend to get theme for, or None for global

    Returns:
        Current theme name
    """
    return get_config("theme", backend)


def set_figure_size(width: float, height: float, backend: Optional[str] = None) -> None:
    """
    Set the default figure size.

    Args:
        width: Figure width in inches
        height: Figure height in inches
        backend: Backend to set figure size for, or None for global
    """
    set_config("figsize", (width, height), backend)


def get_figure_size(backend: Optional[str] = None) -> tuple:
    """
    Get the default figure size.

    Args:
        backend: Backend to get figure size for, or None for global

    Returns:
        Tuple of (width, height) in inches
    """
    return get_config("figsize", backend)


def set_interactive(interactive: bool, backend: Optional[str] = None) -> None:
    """
    Set whether visualizations should be interactive by default.

    Args:
        interactive: Whether to make visualizations interactive
        backend: Backend to set interactivity for, or None for global
    """
    set_config("interactive", interactive, backend)


def is_interactive(backend: Optional[str] = None) -> bool:
    """
    Check if visualizations should be interactive by default.

    Args:
        backend: Backend to check interactivity for, or None for global

    Returns:
        Whether visualizations should be interactive
    """
    return get_config("interactive", backend)


def set_colormap(cmap: str, backend: Optional[str] = None) -> None:
    """
    Set the default colormap.

    Args:
        cmap: Colormap name
        backend: Backend to set colormap for, or None for global
    """
    set_config("cmap", cmap, backend)


def get_colormap(backend: Optional[str] = None) -> str:
    """
    Get the default colormap.

    Args:
        backend: Backend to get colormap for, or None for global

    Returns:
        Default colormap name
    """
    return get_config("cmap", backend)


# Load configuration from environment variables
def _load_config_from_env():
    """
    Load configuration from environment variables.

    Environment variables starting with FMUS_VIZ_ will be loaded into the configuration.
    For example, FMUS_VIZ_DPI=300 will set the 'dpi' configuration to 300.
    """
    prefix = "FMUS_VIZ_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()

            # Parse value based on type inference
            if value.lower() in ("true", "yes", "1", "on"):
                value = True
            elif value.lower() in ("false", "no", "0", "off"):
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                value = float(value)

            # Set in global config
            _CONFIG[config_key] = value


# Load configuration from environment variables on import
_load_config_from_env()
