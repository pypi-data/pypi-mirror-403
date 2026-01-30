# -*- coding: utf-8 -*-
"""
Module default.py
===========================================

Module for default global variables and comparison functions for use by all *PyDASA* and its Data Structures.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""


# python native modules
from dataclasses import dataclass
from typing import Any

# custom modules

# import global variables

# valid data types for the node
# :data: VLD_DTYPE_LT
VLD_DTYPE_LT: tuple = (
    int,
    float,
    str,
    bool,
    dict,
    list,
    tuple,
    set,
    dataclass,
)
"""
Native data types in Python that are comparable in the structures.
"""


def dflt_cmp_function_lt(elm1: Any, elm2: Any, key: str) -> int:
    """*dflt_cmp_function_lt()* Compare two elements of the ADT List (ArrayList, SingleLinked, DoubleLinked). They can be of Python native or user-defined.

    Args:
        elm1 (Any): First element to compare.
        elm2 (Any): Second element to compare.
        key (str): Key for comparing dictionary elements.

    Raises:
        TypeError: If elements are of different types or not comparable.
        KeyError: If the key is not found in dictionary elements.
        TypeError: If elements are not of built-in comparable types.

    Returns:
        int: -1 if elm1 < elm2, 0 if elm1 == elm2, 1 if elm1 > elm2.
    """

    val1, val2 = None, None
    # if elements are of different types, raise error
    if type(elm1) is not type(elm2):
        _msg = "Invalid comparison between "
        _msg += f"{type(elm1)} and {type(elm2)} elements."
        raise TypeError(_msg)

    # if both elements are dictionaries and a key is provided
    if key and isinstance(elm1, dict) and isinstance(elm2, dict):
        val1, val2 = elm1.get(key), elm2.get(key)
        if val1 is None or val2 is None:
            _msg = f"Invalid key: {key}, Key not found in one or both elements."
            raise KeyError(_msg)

    # if both elements are built-in comparable types
    elif isinstance(elm1, VLD_DTYPE_LT) and isinstance(elm2, VLD_DTYPE_LT):
        val1, val2 = elm1, elm2

    # otherwise, raise error
    else:
        _msg = f"Elements of type {type(elm1)} are not comparable "
        _msg += f"with elements of type {type(elm2)}."
        raise TypeError(_msg)

    # Simplified comparison: returns -1, 0, or 1
    # quivalent to the comparison as if, elif, and else statements
    return (val1 > val2) - (val1 < val2)


def dflt_cmp_function_ht(ekey1: Any, entry2, key: str, ) -> int:
    """*dflt_cmp_function_ht()* Compare the entries of the ADT Map (Hash Table). can be of Python native or user-defined.

    Args:
        ekey1 (Any): Key of the first entry (key-value pair) to compare.
        entry2 (MapEntry): Second entry (key-value pair) to compare.
        key (str): Key for comparing dictionary elements.

    Raises:
        TypeError: If the keys are of different types or not comparable.
        KeyError: If the key is not found in dictionary elements.
        TypeError: If keys are not of built-in comparable types.

    Returns:
        int: -1 if ekey1 < ekey2, 0 if ekey1 == ekey2, 1 if ekey1 > ekey2.
    """
    # Extract keys from entries
    ekey2 = entry2.key

    # if keys are of different types, raise error
    if type(ekey1) is not type(ekey2):
        _msg = "Invalid comparison between "
        _msg += f"{type(ekey1)} and {type(ekey2)} elements."
        raise TypeError(_msg)

    # if both keys are dictionaries and a key is provided
    if key and isinstance(ekey1, dict) and isinstance(ekey2, dict):
        val1, val2 = ekey1.get(key), ekey2.get(key)
        if val1 is None or val2 is None:
            _msg = f"Invalid key: '{key}', Key not found in one or both dictionary elements"
            raise KeyError(_msg)

    # if both keys are built-in comparable types
    elif isinstance(ekey1, VLD_DTYPE_LT) and isinstance(ekey2, VLD_DTYPE_LT):
        val1, val2 = ekey1, ekey2

    # otherwise, raise error
    else:
        _msg = f"Elements of type {type(ekey1)} are not comparable "
        _msg += f"with elements of type {type(ekey2)}."
        raise TypeError(_msg)

    # Simplified comparison: returns -1, 0, or 1
    return (val1 > val2) - (val1 < val2)
