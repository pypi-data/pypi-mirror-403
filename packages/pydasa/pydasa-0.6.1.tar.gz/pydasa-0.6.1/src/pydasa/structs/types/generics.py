# -*- coding: utf-8 -*-
"""
Module generics.py
===========================================

Module for default generic dataclass and global constants for use by all *PyDASA* and its Data Structures.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

# python native modules
from typing import TypeVar

# custom modules

# import global variables

# Type for the element stored in the dataclass
# :data: T: TypeVar
T = TypeVar("T")
"""
Type for creating Generics dataclasses in data structure classes, methods, and attrs.

NOTE: used for type hinting only in generics dataclasses.
"""


# default key for comparing dictionaries
# :data: DFLT_DICT_KEY
DFLT_DICT_KEY: str = "_idx"
"""
Default field for comparing dictionaries in the structures.
"""

# allowed input/output types for the ADTs
# :data: VLD_IOTYPE_LT
VLD_IOTYPE_LT: tuple = (
    list,
    tuple,
    set,
)
"""
Allowed input/output types for loading and saving data in the ADTs with the *load* and *save* file methods.
"""

# default big prime number for MAD compression in hash tables
# :data: DFLT_PRIME
DFLT_PRIME: int = 109345121
"""
Default big prime number for the MAD compression function in hash tables.
"""
