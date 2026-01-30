# -*- coding: utf-8 -*-
"""
Module math.py
===========================================

Module with math functions for finding prime numbers and calculating factorials. in *PyDASA*.

Module with math functions for handling data in the for Separate Chaining Hash Table.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    #. Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    #. Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.

*NOTE:* code contributed by Sanjit_Prasad in https://www.geeksforgeeks.org/prime-numbers/
"""
# python native modules
import math
from typing import Union, Optional


def is_prime(n: int) -> bool:
    """*is_prime()* checks if a number is prime or not. Original code from Sanjit_Prasad.

    Args:
        n (int): number to check if it is prime.

    Returns:
        bool: True if the number is prime, False otherwise.
    """
    # we asume that the number is prime
    # Corner cases
    # check if n is 1 or 0
    prime = True
    if n < 2:
        return False

    # checking if n is 2 or 3
    if n < 4:
        return prime

    # checking if n is divisible by 2 or 3
    if n % 2 == 0 or n % 3 == 0:
        return False

    # checking if n is divisible by 5 to to square root of n
    for i in range(5, int(math.sqrt(n) + 1), 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False
    # return True if the number is prime
    return prime


def next_prime(n: int) -> int:
    """*next_prime()* returns the next prime number greater than n.

    Args:
        n (int): number to check if it is prime.

    Returns:
        int: the next prime number greater than n.
    """
    # base case
    if n < 2:
        return 2

    # working with the next odd number
    prime = n
    found = False

    # Loop continuously until isPrime returns
    while not found:
        prime += 1
        # True for a prime number greater than n
        if is_prime(prime) is True:
            found = True
    # return the next prime number to n
    return prime


def previous_prime(n: int) -> int:
    """*previous_prime()* returns the previous prime number less than n.

    Args:
        n (int): number to check if it is prime.

    Returns:
        int: the previous prime number less than n.
    """
    # base case
    if n < 2:
        return 2

    # working with the next odd number
    prime = n
    found = False

    # Loop continuously until isPrime returns
    while not found:
        prime -= 1
        # True for a prime number greater than n
        if is_prime(prime) is True:
            found = True
    # return the previous prime number to n
    return prime


def gfactorial(x: Union[int, float],
               prec: Optional[int] = None) -> Union[int, float]:
    """*gfactorial()* calculates the factorial of a number, including support for floats less than 1.0.

        - For integers n ≥ 0: Returns n! (n factorial).
        - For floats x: Returns Γ(x+1) (gamma function).

    Args:
        x (Union[int, float]): The number to compute the factorial for.
        prec (Optional[int], optional): precision, or the number of decimal places to round the result to. Defaults to None.

    Raises:
        ValueError: If x is a negative integer.

    Returns:
        Union[int, float]: The factorial of x. Returns an integer for integer inputs ≥ 0, and a float for float inputs or integers < 0.

    Examples:
        >>> gfactorial(5)
        120
        >>> gfactorial(0)
        1
        >>> gfactorial(0.5)  # Equivalent to Γ(1.5) = 0.5 * Γ(0.5) = 0.5 * √Pi
        0.8862269254527579
        >>> gfactorial(-0.5)  # Equivalent to Γ(0.5) = √Pi
        1.7724538509055159
    """
    if isinstance(x, int) and x >= 0:
        # Standard factorial for non-negative integers
        result = math.factorial(x)
    elif isinstance(x, int) and x < 0:
        # Factorial is not defined for negative integers
        raise ValueError("Factorial is not defined for negative integers")
    else:
        # For floats, use the gamma function: Γ(x+1)
        result = math.gamma(x + 1)

    # Apply precision if specified
    if prec is not None:
        result = round(result, prec)

    return result
