from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


def detect_data_type(data: Any) -> str:
    """
    Detect the type of data being passed.

    Args:
        data: Data to analyze

    Returns:
        String describing the data type ('dataframe', 'series', 'array', 'list', etc.)
    """
    if isinstance(data, pd.DataFrame):
        return "dataframe"
    elif isinstance(data, pd.Series):
        return "series"
    elif isinstance(data, np.ndarray):
        return "array"
    elif isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            return "list_of_dicts"
        elif all(isinstance(item, (list, tuple)) for item in data):
            return "list_of_lists"
        else:
            return "list"
    elif isinstance(data, dict):
        return "dict"
    else:
        return "unknown"


def convert_to_dataframe(data: Any) -> pd.DataFrame:
    """
    Convert various data types to a pandas DataFrame.

    Args:
        data: Data to convert

    Returns:
        Pandas DataFrame

    Raises:
        ValueError: If data cannot be converted to a DataFrame
    """
    data_type = detect_data_type(data)

    if data_type == "dataframe":
        return data
    elif data_type == "series":
        return pd.DataFrame(data)
    elif data_type == "array":
        if data.ndim == 1:
            return pd.DataFrame({"value": data})
        elif data.ndim == 2:
            # Jika 2D array, gunakan indeks kolom numerik
            return pd.DataFrame(data)
        else:
            raise ValueError("Cannot convert arrays with more than 2 dimensions to DataFrame")
    elif data_type == "list_of_dicts":
        return pd.DataFrame(data)
    elif data_type == "list_of_lists":
        return pd.DataFrame(data)
    elif data_type == "list":
        return pd.DataFrame({"value": data})
    elif data_type == "dict":
        return pd.DataFrame(data)
    else:
        try:
            return pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f"Cannot convert data to DataFrame: {str(e)}")


def get_column_data(data: Union[pd.DataFrame, pd.Series], column: Optional[str] = None) -> np.ndarray:
    """
    Extract a column of data from a DataFrame or Series.

    Args:
        data: DataFrame or Series
        column: Column name to extract, or None to return the entire data

    Returns:
        NumPy array of column data
    """
    if column is None:
        if isinstance(data, pd.Series):
            return data.values
        else:
            return data.values.flatten() if data.shape[1] == 1 else data.values

    if isinstance(data, pd.DataFrame):
        if column in data.columns:
            return data[column].values
        else:
            raise ValueError(f"Column '{column}' not found in DataFrame")
    elif isinstance(data, pd.Series):
        if data.name == column:
            return data.values
        else:
            raise ValueError(f"Series name '{data.name}' does not match requested column '{column}'")
    else:
        raise ValueError(f"Data type {type(data)} not supported for column extraction")


def infer_x_y_columns(data: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Infer the most likely x and y columns from a DataFrame.

    Args:
        data: DataFrame to analyze

    Returns:
        Tuple of (x_column, y_column)
    """
    if len(data.columns) < 2:
        if len(data.columns) == 1:
            # Jika hanya ada satu kolom, gunakan indeks sebagai x dan kolom sebagai y
            return None, data.columns[0]
        else:
            return None, None

    # Coba deteksi kolom berdasarkan nama
    x_candidates = [
        col for col in data.columns
        if col.lower() in ('x', 'index', 'id', 'key', 'category', 'date', 'time', 'timestamp', 'period')
        or bool(re.search(r'(date|time|year|month|day|x|category|group)', col.lower()))
    ]

    y_candidates = [
        col for col in data.columns
        if col.lower() in ('y', 'value', 'count', 'sum', 'mean', 'median', 'amount', 'total')
        or bool(re.search(r'(value|count|sum|average|mean|median|total|y)', col.lower()))
    ]

    # Jika kita memiliki kandidat, gunakan yang paling mungkin
    x_col = x_candidates[0] if x_candidates else None
    y_col = y_candidates[0] if y_candidates else None

    # Jika tidak ada kandidat y yang jelas, gunakan kolom numerik pertama yang bukan x
    if y_col is None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col != x_col]
        if len(numeric_cols) > 0:
            y_col = numeric_cols[0]

    # Jika tidak ada kandidat x yang jelas, gunakan kolom kategori atau datetime pertama
    if x_col is None:
        cat_cols = data.select_dtypes(include=['category', 'object']).columns
        if len(cat_cols) > 0:
            x_col = cat_cols[0]
        else:
            date_cols = data.select_dtypes(include=['datetime']).columns
            if len(date_cols) > 0:
                x_col = date_cols[0]

    # Jika masih belum ada x, gunakan kolom pertama yang bukan y
    if x_col is None and len(data.columns) >= 2:
        candidates = [col for col in data.columns if col != y_col]
        if candidates:
            x_col = candidates[0]

    # Jika masih belum ada y, gunakan kolom kedua
    if y_col is None and len(data.columns) >= 2:
        candidates = [col for col in data.columns if col != x_col]
        if candidates:
            y_col = candidates[0]

    return x_col, y_col


def standardize_color_input(color: Any) -> Union[str, List[str], np.ndarray]:
    """
    Standardize color input to a consistent format.

    Args:
        color: Color input (string, list, array, etc.)

    Returns:
        Standardized color representation
    """
    if color is None:
        return None

    if isinstance(color, str):
        return color

    if isinstance(color, (list, tuple)):
        if all(isinstance(c, str) for c in color):
            return list(color)
        else:
            return np.array(color)

    if isinstance(color, np.ndarray):
        return color

    # Coba konversi ke string jika tipe lain
    try:
        return str(color)
    except:
        return None


def downsample_data(data: pd.DataFrame, max_points: int = 1000) -> pd.DataFrame:
    """
    Downsample a large DataFrame to a manageable size.

    Args:
        data: DataFrame to downsample
        max_points: Maximum number of points to include

    Returns:
        Downsampled DataFrame
    """
    if len(data) <= max_points:
        return data

    # Sampel beberapa baris secara merata
    indices = np.linspace(0, len(data) - 1, max_points, dtype=int)
    return data.iloc[indices]


def parse_color_argument(color: Any, data_length: int) -> Any:
    """
    Parse and validate a color argument.

    Args:
        color: Color specification
        data_length: Length of the dataset

    Returns:
        Processed color value
    """
    if color is None:
        return None

    # Jika warna adalah string, gunakan untuk semua poin data
    if isinstance(color, str):
        return color

    # Jika warna adalah list atau array
    if isinstance(color, (list, tuple, np.ndarray)):
        # Jika panjangnya 1, gunakan warna itu untuk semua poin
        if len(color) == 1:
            return color[0]

        # Jika panjangnya sama dengan data, gunakan langsung
        if len(color) == data_length:
            return color

        # Jika tidak, potong atau perluas sesuai panjang data
        if len(color) > data_length:
            return color[:data_length]
        else:
            # Duplikasi warna untuk mencapai panjang yang dibutuhkan
            result = list(color)
            while len(result) < data_length:
                result.extend(list(color))
            return result[:data_length]

    # Default: return as is
    return color


def infer_categorical_columns(data: pd.DataFrame) -> List[str]:
    """
    Infer which columns are likely categorical.

    Args:
        data: DataFrame to analyze

    Returns:
        List of column names that are likely categorical
    """
    categorical = []

    # Kolom dengan tipe kategori atau objek
    categorical.extend(data.select_dtypes(include=['category', 'object']).columns)

    # Kolom numerik dengan jumlah nilai unik yang rendah
    for col in data.select_dtypes(include=[np.number]).columns:
        n_unique = data[col].nunique()
        if n_unique <= 20 and n_unique < len(data) * 0.05:  # Max 20 unique values and less than 5% of rows
            categorical.append(col)

    return list(set(categorical))
