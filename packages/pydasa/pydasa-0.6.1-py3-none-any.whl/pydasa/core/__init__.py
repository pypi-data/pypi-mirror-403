# -*- coding: utf-8 -*-
"""
Package data
===========================================

Data persistence and I/O operations for PyDASA.

This package provides functions for reading and writing data to files,
handling different data formats, and ensuring compatibility with the
data structures used in PyDASA.
"""

from pydasa.core.io import load, save, load_json, save_json

__all__ = ['load', 'save', 'load_json', 'save_json']
