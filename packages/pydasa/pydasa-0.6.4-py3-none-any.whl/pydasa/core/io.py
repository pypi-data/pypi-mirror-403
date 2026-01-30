# -*- coding: utf-8 -*-
"""
Module io.py
===========================================

Generic I/O operations for PyDASA.

This module provides functions for reading and writing data to files, handling different data formats (JSON, CSV, etc.), and ensuring compatibility with the data structures used in PyDASA.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

import json
from pathlib import Path
from typing import Any

# global variable to define supported formats
READ = "r"
WRITE = "w"
PATTERN = "utf-8"
AVAIL_FMT = [".json"]


def load_json(file_path: str | Path) -> dict[str, Any]:
    """*load_json()* reads a JSON file and returns its content as a dictionary.

    Args:
        file_path (str | Path): Path to the JSON file.

    Returns:
        dict[str, Any]: Dictionary with the JSON content.
    """
    file_path = Path(file_path)
    with open(file_path, READ, encoding=PATTERN) as f:
        return json.load(f)


def save_json(data: dict[str, Any],
              file_path: str | Path,
              indent: int = 4) -> None:
    """*save_json()* writes a dictionary to a JSON file.

    Args:
        data (dict[str, Any]): Dictionary to be saved.
        file_path (str | Path): Path to the output JSON file.
        indent (int, optional): Indentation level. Defaults to 4.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, WRITE, encoding=PATTERN) as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load(file_path: str | Path) -> dict[str, Any]:
    """*load()* generic load function - detects format from file extension.

    Args:
        file_path (str | Path): Input file path.

    Raises:
        ValueError: If unsupported file format.

    Returns:
        dict[str, Any]: Loaded data as a dictionary.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix in AVAIL_FMT:
        return load_json(file_path)
    else:
        _msg = f"Unsupported file format: {suffix}. "
        _msg += f"Supported: {', '.join(AVAIL_FMT)}"
        raise ValueError(_msg)


def save(data: dict[str, Any],
         file_path: str | Path, **kwargs) -> None:
    """*save()* generic save function - detects format from file extension.

    Args:
        data (dict[str, Any]): Data to be saved.
        file_path (str | Path): Output file path.
        **kwargs: Additional keyword arguments for specific save functions.

    Raises:
        ValueError: If unsupported file format.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix in AVAIL_FMT:
        indent = kwargs.get("indent", 4)
        save_json(data, file_path, indent=indent)
    else:
        _msg = f"Unsupported file format: {suffix}. "
        _msg += f"Supported: {', '.join(AVAIL_FMT)}"
        raise ValueError(_msg)
