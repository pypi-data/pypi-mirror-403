# -*- coding: utf-8 -*-
"""
Module memory.py
===========================================

Module with utility functions for handling memory allocation in the Data Structures of *PyDASA*.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""
# python native modules
import sys
from typing import Type

# dataclases module handles the creation of classes with slots and fields
import dataclasses

# import global variables
from pydasa.structs.types.generics import T


def mem_slot(cls: Type[T]) -> Type[T]:
    """*mem_slot()* is a decorator that converts a class into a dataclass with slots.

    Args:
        cls (Type[T]): class to convert into a dataclass with slots.

    Raises:
        TypeError: if the cls is not a class type.
        RuntimeError: if the Python version is less than 3.10.

    Returns:
        Type[T]: A dataclass with slots.
    """
    # TODO check validity of this decorator
    # TODO integrate with the dataclass decorator?
    if not isinstance(cls, type):
        raise TypeError(f"Invalid class: {cls}, class must be a type")

    # Check Python version for native slots support
    if sys.version_info >= (3, 10):
        # Use native slots support
        if dataclasses.is_dataclass(cls):
            # Already a dataclass, need to recreate with slots
            return dataclasses.dataclass(cls, slots=True)
        else:
            return dataclasses.dataclass(cls, slots=True)
    else:   # type: ignore[unreachable]
        _msg = "mem_slot requires Python 3.10+ for native support. "
        _msg += f"Current version: {sys.version_info.major}."
        _msg += f"{sys.version_info.minor}"
        raise RuntimeError(_msg)
