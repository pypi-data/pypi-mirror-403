# -*- coding: utf-8 -*-
"""
Module helpers.py
===========================================

Module with utility functions for handling memory allocation in the Data Structures of *PyDASA*.

Module with utility functions for handling data in the maps of *PyDASA*. Specifically for Separate Chaining and Linear Probing Hash Tables.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""
# python native modules
from typing import Hashable
# import math

# import global variables
from pydasa.structs.types.generics import VLD_IOTYPE_LT


def mad_hash(key: Hashable,
             scale: int,
             shift: int,
             prime: int,
             mcap: int) -> int:
    """*mad_hash()* function to compress the indices of the Hash tables using the MAD (Multiply-Add-and-Divide) method.

    MAD is defined as: mad_hash(y) = ((a*y + b) % p) % M, where:
        a (scale) and b (shift) are random integers in the range [0,p-1], with a > 0
        p (prime) is a prime number greater than M,
        M (capacity) is the size of the table, prime

    Args:
        key (Hashable): key to calculate the index in the Hash table, Can be any native data type in Python or user-defined.
        scale (int): line slope of the compression function.
        shift (int): offset of the compression function.
        prime (int): prime number much greater than the capacity of the Hash table.
        mcap (int): size of the Hash table, it is a prime number to avoid collisions.

    Returns:
        int: the index of the element in the Hash table.
    """
    # TODO data should be hashable?
    # data types are (dict, list, set, tuple)
    if isinstance(key, VLD_IOTYPE_LT) or isinstance(key, dict):
        key = str(key)
    # getting the hash from the key
    hkey = hash(key)
    # calculating the index with the MAD compression function
    idx = int((abs(scale * hkey + shift) % prime) % mcap)
    return idx
