# -*- coding: utf-8 -*-
"""
Module htme.py
===========================================

Module to represent the **MapEntry** data structure for the **Hash Table** in *PyDASA*.

classes:
    **MapEntry**: Represents a key-value pair in a hash table with type validation and error handling.

*IMPORTANT:* based on the implementations proposed by the following authors/books:

    # . Algorithms, 4th Edition, Robert Sedgewick and Kevin Wayne.
    # . Data Structure and Algorithms in Python, M.T. Goodrich, R. Tamassia, M.H. Goldwasser.
"""

# native python modules
# dataclass imports
from dataclasses import dataclass
# data type imports
from typing import Generic, Optional
# code inspection imports
import inspect

# custom modules
# generic types and global variables
from pydasa.structs.types.generics import T
# generic error handling and type checking
from pydasa.validations.error import handle_error as error

# checking custom modules
assert T
assert error


@dataclass
class MapEntry(Generic[T]):
    """**MapEntry** class for creating a map entry in the **Hash Table**. Fundamental for the **Hash Table** data structure.

    Args:
        Generic (T): Generic type for a Python data structure.

    Returns:
        MapEntry: A map entry object with the following attributes:
            - `_key`: The key of the map entry.
            - `_value`: The value of the map entry.
    """

    # optional key of any type
    # :attr: _key
    _key: Optional[T] = None
    """
    Es la llave del registro del mapa.
    """
    # optional value of any type
    # _value
    _value: Optional[T] = None
    """
    Es el valor del registro del mapa.
    """

    def _error_handler(self, err: Exception) -> None:
        """*_error_handler()* to process the context (package/class), function name (method), and the error (exception) that was raised to format a detailed error message and traceback.

        Args:
            err (Exception): Python raised exception.
        """
        _context = self.__class__.__name__
        _function_name = "unknown"
        frame = inspect.currentframe()
        if frame is not None:
            if frame.f_back is not None:
                _function_name = frame.f_back.f_code.co_name
        else:
            _function_name = "unknown"
        error(_context, _function_name, err)

    def _validate_key_type(self, key: T) -> bool:
        """*_validate_key_type()* checks if the type of the key is the same as the type of the *MapEntry*.

        Args:
            key (T):_key to process in the *MapEntry*.

        Raises:
            TypeError: error if the type of the key to be added is not the same as the type of the keys already contained in the *MapEntry*.

        Returns:
            bool: True if the type of the key is the same as the type of the *MapEntry*.
        """
        if not isinstance(key, type(self._key)):
            _msg = f"Invalid data type: {type(self._key)} "
            _msg += f"for key data: {type(key)}"
            raise TypeError(_msg)
        return True

    def _validate_value_type(self, value: T) -> bool:
        """*_validate_value_type()* checks if the type of the value is the same as the type of the *MapEntry*.

        Args:
            value (T): value to process in the *MapEntry*.

        Raises:
            TypeError: error if the type of the value to be added is not the same as the type of the values already contained in the *MapEntry*.

        Returns:
            bool: True if the type of the value is the same as the type of the *MapEntry*.
        """
        if not isinstance(value, type(self._value)):
            _msg = f"Invalid data type: {type(self._value)} "
            _msg += f"for value data: {type(value)}"
            raise TypeError(_msg)
        return True

    @property
    def key(self) -> Optional[T]:
        """*key* Property to read the key in the *MapEntry*. Acts as a getter (*get()*) for the *_key* attribute.

        Returns:
            Optional[T]: recovered key in the *MapEntry*. None if the key is not set.
        """
        return self._key

    @key.setter
    def key(self, key: T) -> None:
        """*key* Property to write the key in the *MapEntry*. Acts as a setter (*set()*) for the *_key* attribute.
        Args:
            key (T): key set in the *MapEntry*.
        """
        # check already set key type
        if self._key is not None and self._validate_key_type(key):
            self._key = key

    @property
    def value(self) -> Optional[T]:
        """*value* Property to read the value in the *MapEntry*. Acts as a getter (*get()*) for the *_value* attribute.

        Returns:
            Optional[T]: recovered value in the *MapEntry*. None if the value is not set.
        """
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        """*value* Property to write the value in the *MapEntry*. Acts as a setter (*set()*) for the *_value* attribute.

        Args:
            value (T): value to be set in the *MapEntry*.
        Raises:
        """
        # check already set value type
        if self._value is not None and self._validate_value_type(value):
            self._value = value

    def __str__(self) -> str:
        """*__str__()* function to return a string representation of the *MapEntry*.

        Returns:
            str: string representation of the *MapEntry*.
        """
        _attr_lt = []
        for attr, value in vars(self).items():
            # Skip private attributes starting with "__"
            if attr.startswith("__"):
                continue
            # Format callable attributes
            if callable(value):
                value = f"{value.__name__}{inspect.signature(value)}"
            # Format attribute name and value
            _attr_name = attr.lstrip("_")
            _attr_lt.append(f"{_attr_name}={str(value)}")

        # Format the string representation of MapEntry class and its attributes
        _str = f"{self.__class__.__name__}({', '.join(_attr_lt)})"
        return _str

    def __repr__(self) -> str:
        """*__repr__()* function to return a string representation of the *MapEntry*.

        Returns:
            str: string representation of the *MapEntry*.
        """
        return self.__str__()
