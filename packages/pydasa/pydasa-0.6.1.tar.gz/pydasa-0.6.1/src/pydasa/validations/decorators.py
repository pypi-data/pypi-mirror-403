# -*- coding: utf-8 -*-
"""
Module decorators.py
===========================================

Decorator-based validation system for PyDASA attributes.

This module provides reusable decorators for property setters, eliminating
the need for separate validation methods and reducing boilerplate code.

Functions:
    **validate_type**: Validates value against expected type(s)
    **validate_emptiness**: Ensures string values are non-empty
    **validate_choices**: Validates value is in allowed set of choices
    **validate_range**: Validates numeric value is within specified range
    **validate_index**: Validates integer values with negativity control
    **validate_pattern**: Validates string matches regex pattern(s) or is alphanumeric
    **validate_custom**: Custom validation logic
"""

# native python modules
from functools import wraps
from enum import Enum
from typing import Callable, Any, Union, Type, Optional, Tuple
import re

# third-party imports
import numpy as np


def validate_type(*expected_types: type,
                  allow_none: bool = True,
                  allow_nan: bool = False) -> Callable:
    """*validate_type()* Decorator to validate argument type against expected type(s).

    Args:
        *expected_types (type): One or more expected types for validation.
        allow_none (bool, optional): Whether None values are allowed. Defaults to True.
        allow_nan (bool, optional): Whether np.nan values are allowed. Defaults to False.

    Raises:
        ValueError: If value is None when allow_none is False.
        ValueError: If value is np.nan when allow_nan is False.
        ValueError: If value type does not match any of the expected types.

    Returns:
        Callable: Decorated function with type validation.

    Example:
        @property
        def unit(self) -> str:
            return self._unit

        @unit.setter
        @validate_type(str)
        def unit(self, val: str) -> None:
            self._unit = val

        # Multiple types
        @value.setter
        @validate_type(int, float)
        def value(self, val: Union[int, float]) -> None:
            self._value = val

        # Allow np.nan
        @mean.setter
        @validate_type(int, float, allow_nan=True)
        def mean(self, val: Optional[float]) -> None:
            self._mean = val
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            # if value is None
            if value is None:
                if not allow_none:
                    _msg = f"{func.__name__} cannot be None."
                    raise ValueError(_msg)
                return func(self, value)

            # if value is np.nan
            if isinstance(value, float) and np.isnan(value):
                if not allow_nan:
                    _msg = f"{func.__name__} cannot be np.nan."
                    raise ValueError(_msg)
                return func(self, value)

            # if value type is incorrect
            if not isinstance(value, expected_types):
                type_names = " or ".join(t.__name__ for t in expected_types)
                _msg = f"{func.__name__} must be {type_names}, "
                _msg += f"got {type(value).__name__}."
                raise ValueError(_msg)
            # otherwise, return the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_emptiness(strip: bool = True) -> Callable:
    """*validate_emptiness()* Decorator to ensure values are non-empty.

    Handles strings, dictionaries, lists, tuples, and other collections.
    For strings, optionally strips whitespace before checking.

    Args:
        strip (bool, optional): Whether to strip whitespace before checking strings. Defaults to True.

    Raises:
        ValueError: If string is empty/whitespace-only, or if collection has no elements.

    Returns:
        Callable: Decorated function with non-empty validation.

    Example:
        @unit.setter
        @validate_type(str)
        @validate_emptiness()
        def unit(self, val: str) -> None:
            self._unit = val

        @variables.setter
        @validate_type(dict)
        @validate_emptiness()
        def variables(self, val: dict) -> None:
            self._variables = val
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            # if value is not None, check for emptiness
            if value is not None:
                # Handle strings separately to allow strip functionality
                if isinstance(value, str):
                    check_val = value.strip() if strip else value
                    if not check_val:
                        _msg = f"{func.__name__} must be a non-empty string. "
                        _msg += f"Provided: {repr(value)}."
                        raise ValueError(_msg)
                # Handle collections (dict, list, tuple, set, etc.)
                elif hasattr(value, '__len__'):
                    if len(value) == 0:
                        type_name = type(value).__name__
                        _msg = f"{func.__name__} must be a non-empty {type_name}. "
                        _msg += f"Provided: {repr(value)}."
                        raise ValueError(_msg)
            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_choices(choices: Union[dict, set, list, tuple, Type[Enum]],
                     allow_none: bool = False,
                     case_sensitive: bool = False) -> Callable:
    """*validate_choices()* Decorator to validate value is in allowed set of choices.

    Args:
        choices (Union[dict, set, list, tuple, Type[Enum]]): Dictionary, set, list, tuple, or Enum type of allowed values.
        allow_none (bool, optional): Whether None values are allowed. Defaults to False.
        case_sensitive (bool, optional): Whether string comparison is case-sensitive. Defaults to False.

    Raises:
        ValueError: If value is not in the allowed choices.

    Returns:
        Callable: Decorated function with choice validation.

    Example:
        from pydasa.core.setup import Frameworks

        @fwk.setter
        @validate_type(str)
        @validate_choices(Frameworks.values())
        def fwk(self, val: str) -> None:
            self._fwk = val.upper()

        # Case-sensitive choices
        @status.setter
        @validate_choices(["Active", "Inactive"], case_sensitive=True)
        def status(self, val: str) -> None:
            self._status = val
    """
    # Convert choices to set for O(1) lookup - extract enum names when needed
    if isinstance(choices, dict):
        valid_choices = set(choices.keys())
    elif isinstance(choices, type) and issubclass(choices, Enum):
        # Enum class passed directly (e.g., Frameworks)
        valid_choices = {member.name for member in choices}
    else:
        # Handle collections: check if they contain Enum members
        first_elem = next(iter(choices), None) if choices else None
        if first_elem and isinstance(first_elem, Enum):
            # Collection of Enum members (e.g., tuple of Frameworks members)
            valid_choices = {member.name for member in choices}
        else:
            # Plain collection of strings or other values
            valid_choices = set(choices)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            # if value is None
            if value is None:
                if not allow_none:
                    _msg = f"{func.__name__} cannot be None."
                    raise ValueError(_msg)
                return func(self, value)

            # Extract the actual value to check
            # If value is an Enum member, use its name
            if isinstance(value, Enum):
                actual_value = value.name
            else:
                actual_value = value

            # if case-insensitive, adjust value and choices
            if case_sensitive:
                check_val = actual_value
                compare_set = valid_choices
            # otherwise, use upper-case for comparison
            else:
                check_val = str(actual_value).upper()
                compare_set = {str(c).upper() for c in valid_choices}

            # if value not in choices, raise error
            if check_val not in compare_set:
                _msg = f"Invalid {func.__name__}: {value}. "
                # Format choices nicely - if Enum members, use their name/value only
                choice_strs = [c.name if isinstance(c, Enum) else str(c) for c in valid_choices]
                _msg += f"Must be one of: {', '.join(choice_strs)}."
                raise ValueError(_msg)

            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_index(allow_zero: bool = True,
                   allow_negative: bool = False) -> Callable:
    """*validate_index()* Decorator to validate integer values with negativity and zero control.

    Args:
        allow_zero (bool, optional): Whether zero is allowed. Defaults to True.
        allow_negative (bool, optional): Whether negative integers are allowed. Defaults to False.

    Raises:
        ValueError: If value is not an integer.
        ValueError: If negative value when allow_negative is False.
        ValueError: If zero value when allow_zero is False.

    Returns:
        Callable: Decorated function with integer validation.

    Example:
        # Non-negative integers only
        @idx.setter
        @validate_index(allow_negative=False)
        def idx(self, val: int) -> None:
            self._idx = val

        # Positive integers only (no zero)
        @count.setter
        @validate_index(allow_negative=False, allow_zero=False)
        def count(self, val: int) -> None:
            self._count = val
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            # if value is not None, perform checks
            if value is not None:
                # if not an integer, raise error
                if not isinstance(value, int):
                    _msg = f"{func.__name__} must be an integer. "
                    _msg += f"Provided: {value} ({type(value).__name__})."
                    raise ValueError(_msg)

                # if negative not allowed and value es velow zero
                if not allow_negative and value < 0:
                    _msg = f"{func.__name__} must be non-negative. "
                    _msg += f"Provided: {value}."
                    raise ValueError(_msg)

                # if zero not allowed and value is zero
                if not allow_zero and value == 0:
                    _msg = f"{func.__name__} cannot be zero. "
                    _msg += f"Provided: {value}."
                    raise ValueError(_msg)

            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_range(min_value: Optional[float] = None,
                   max_value: Optional[float] = None,
                   min_inclusive: bool = True,
                   max_inclusive: bool = True,
                   min_attr: Optional[str] = None,
                   max_attr: Optional[str] = None) -> Callable:
    """Decorator to validate numeric value is within specified range.

    Args:
        min_value (Optional[float], optional): Static minimum value. Defaults to None.
        max_value (Optional[float], optional): Static maximum value. Defaults to None.
        min_inclusive (bool, optional): Whether minimum is inclusive (>=) or exclusive (>). Defaults to True.
        max_inclusive (bool, optional): Whether maximum is inclusive (<=) or exclusive (<). Defaults to True.
        min_attr (Optional[str], optional): Attribute name for dynamic minimum (e.g., '_min'). Defaults to None.
        max_attr (Optional[str], optional): Attribute name for dynamic maximum (e.g., '_max'). Defaults to None.

    Raises:
        ValueError: If value is outside the specified range.

    Returns:
        Callable: Decorated function with range validation.

    Example:
        # Static range
        @age.setter
        @validate_type(int)
        @validate_range(min_value=0, max_value=150)
        def age(self, val: int) -> None:
            self._age = val

        # Dynamic range based on other attributes
        @mean.setter
        @validate_type(int, float)
        @validate_range(min_attr='_min', max_attr='_max')
        def mean(self, val: float) -> None:
            self._mean = val
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            if value is not None:
                # Check static minimum
                if min_value is not None:
                    if min_inclusive:
                        if value < min_value:
                            _msg = f"{func.__name__} must be >= {min_value}, "
                            _msg += f"got {value}."
                            raise ValueError(_msg)
                    else:
                        if value <= min_value:
                            _msg = f"{func.__name__} must be > {min_value}, "
                            _msg += f"got {value}."
                            raise ValueError(_msg)

                # Check static maximum
                if max_value is not None:
                    if max_inclusive:
                        if value > max_value:
                            _msg = f"{func.__name__} must be <= {max_value}, "
                            _msg += f"got {value}."
                            raise ValueError(_msg)
                    else:
                        if value >= max_value:
                            _msg = f"{func.__name__} must be < {max_value}, "
                            _msg += f"got {value}."
                            raise ValueError(_msg)

                # Check dynamic minimum from attribute
                if min_attr and hasattr(self, min_attr):
                    min_val = getattr(self, min_attr)
                    if min_val is not None and value < min_val:
                        _msg = f"{func.__name__} ({value}) cannot be less than "
                        _msg += f"minimum ({min_val})."
                        raise ValueError(_msg)

                # Check dynamic maximum from attribute
                if max_attr and hasattr(self, max_attr):
                    max_val = getattr(self, max_attr)
                    if max_val is not None and value > max_val:
                        _msg = f"{func.__name__} ({value}) cannot be greater than "
                        _msg += f"maximum ({max_val})."
                        raise ValueError(_msg)

            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_pattern(pattern: Optional[Union[str, list, tuple]] = None,
                     allow_alnum: bool = False,
                     error_msg: Optional[str] = None,
                     examples: Optional[str] = None) -> Callable:
    """Decorator to validate string matches regex pattern(s) or is alphanumeric.

    This unified decorator handles:
    - Single pattern matching
    - Multiple pattern matching (OR logic - matches any pattern)
    - Optional alphanumeric validation
    - Scientific/mathematical symbols (alphanumeric OR LaTeX)

    Args:
        pattern (Union[str, list, tuple]): Single regex pattern string, or list/tuple of patterns to match (OR logic).
        allow_alnum (bool, optional): Whether to accept alphanumeric strings. Defaults to False.
        error_msg (Optional[str], optional): Custom error message (overrides default). Defaults to None.
        examples (Optional[str], optional): Example strings to show in error messages. Defaults to None.

    Raises:
        ValueError: If value does not match any pattern and is not alphanumeric (when allowed).

    Returns:
        Callable: Decorated function with pattern validation.

    Examples:
        # Simple pattern matching
        @code.setter
        @validate_pattern(r'^[A-Z]\\d{3}$')
        def code(self, val: str) -> None:
            self._code = val

        # Symbol validation (alphanumeric OR LaTeX)
        from pydasa.validations.patterns import LATEX_RE

        @sym.setter
        @validate_type(str)
        @validate_emptiness()
        @validate_pattern(LATEX_RE, allow_alnum=True)
        def sym(self, val: str) -> None:
            self._sym = val

        # Multiple patterns (match any)
        @validate_pattern([r'^\\\\[a-z]+$', r'^\\d+$'])
        def value(self, val: str) -> None:
            self._value = val
    """
    # Validate decorator configuration
    if pattern is None and not allow_alnum:
        _msg = "Provide either 'pattern' or 'allow_alnum' must be True"
        raise ValueError(_msg)

    # Compile pattern(s) into list
    if pattern is None:
        compiled_patterns = []
    elif isinstance(pattern, (list, tuple)):
        compiled_patterns = [re.compile(p) for p in pattern]
    else:
        compiled_patterns = [re.compile(pattern)]

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            if value is not None:
                is_valid = False

                # Check if alphanumeric (if allowed)
                if allow_alnum and value.isalnum():
                    is_valid = True

                # Check if matches any pattern
                if not is_valid and compiled_patterns:
                    for compiled_pattern in compiled_patterns:
                        if compiled_pattern.match(value):
                            is_valid = True
                            break

                # Raise error if validation failed
                # TODO improve msg construction
                if not is_valid:
                    if error_msg:
                        _msg = error_msg
                    elif allow_alnum and compiled_patterns:
                        _msg = f"{func.__name__} must be alphanumeric or match pattern. "
                        _msg += f"Provided: '{value}'. "
                        if examples:
                            _msg += f"Examples: {examples}"
                        else:
                            _msg += "Examples: 'V', 'd', '\\\\Pi_{{0}}', '\\\\rho'."
                    elif allow_alnum:
                        _msg = f"{func.__name__} must be alphanumeric. "
                        _msg += f"Provided: '{value}'."
                    elif len(compiled_patterns) == 1:
                        _msg = f"{func.__name__} must match pattern. "
                        _msg += f"Provided: {repr(value)}."
                    elif len(compiled_patterns) > 1:
                        _msg = f"{func.__name__} must match one of {len(compiled_patterns)} patterns. "
                        _msg += f"Provided: {repr(value)}."
                    else:
                        _msg = f"{func.__name__} validation failed for: {repr(value)}."

                    raise ValueError(_msg)

            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_list_types(*elm_types: type) -> Callable:
    """*validate_list_types()* Decorator to validate list contains only specified element types. It asumes the list exists.

    Args:
        *elm_types (type): One or more expected types for list elements.

    Raises:
        ValueError: If value is not a list.
        ValueError: If list contains elements of wrong type.

    Returns:
        Callable: Decorated function with list type validation.

    Example:
        @dim_col.setter
        @validate_type(list, allow_none=False)
        @validate_emptiness()
        @validate_list_types(int, float)
        def dim_col(self, val: List[int]) -> None:
            self._dim_col = [int(x) for x in val]
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            # if the list exists
            if value is not None:
                # Check all elements match expected types
                if not all(isinstance(elem, elm_types) for elem in value):
                    type_names = " or ".join(t.__name__ for t in elm_types)
                    actual_types = [type(x).__name__ for x in value]
                    _msg = f"{func.__name__} must contain only {type_names} elements. "
                    _msg += f"Found types: {actual_types}."
                    raise ValueError(_msg)

            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_dict_types(key_type: type,
                        val_types: type | Tuple[type, ...]) -> Callable:
    """*validate_dict_types()* Decorator to validate dict has correct key and value types. It asumes the dict exists.

    Args:
        key_type (type): Expected type for dictionary keys.
        val_types (type | Tuple[type, ...]): Expected types for dictionary values. At least one type must be provided.

    Raises:
        ValueError: If dict keys or values have wrong types.

    Returns:
        Callable: Decorated function with dict type validation.

    Example:
        @variables.setter
        @validate_type(dict, allow_none=False)
        @validate_emptiness()
        @validate_dict_types(str, (Variable, dict))
        def variables(self, val: Dict[str, Variable]) -> None:
            self._variables = val
    """
    # Normalize val_types to always be a tuple
    if isinstance(val_types, type):
        std_types: Tuple[type, ...] = (val_types,)
    else:
        std_types = val_types

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:

            # if the dict exists
            if value is not None:
                # Check all keys match expected type
                invalid_keys = [
                    k for k in value.keys() if not isinstance(k, key_type)
                ]
                if invalid_keys:
                    _msg = f"{func.__name__} keys must be {key_type.__name__}. "
                    _msg += f"Found invalid keys: {invalid_keys}."
                    raise ValueError(_msg)

                # Check all values match expected type
                invalid_values = [
                    v for v in value.values() if not isinstance(v, std_types)
                ]
                if invalid_values:
                    # Build human-readable type names
                    if len(std_types) == 1:
                        type_names = std_types[0].__name__
                    else:
                        type_names = " or ".join(t.__name__ for t in std_types)

                    _msg = f"{func.__name__} values must be {type_names}. "
                    _msg += f"Found {len(invalid_values)} invalid value(s)."
                    raise ValueError(_msg)

            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator


def validate_custom(validator_func: Callable[[Any, Any], None]) -> Callable:
    """*validate_custom()* Decorator for custom validation logic. Allows implementing custom validation logic by providing a validator function.

    The validator function should raise ValueError if validation fails.
    NOTE: this is too abstract and should be used sparingly.

    Args:
        validator_func (Callable[[Any, Any], None]): Function(self, value) that raises ValueError if invalid.

    Raises:
        ValueError: If custom validator function raises ValueError.

    Returns:
        Callable: Decorated function with custom validation.

    Example:
        def check_range_consistency(self, value):
            '''Ensure minimum does not exceed maximum.'''
            if value is not None and self._max is not None and value > self._max:
                raise ValueError(f"min {value} > max {self._max}")

        @min.setter
        @validate_type(int, float)
        @validate_custom(check_range_consistency)
        def min(self, val: float) -> None:
            self._min = val
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: Any) -> Any:
            # Run custom validator
            validator_func(self, value)
            # otherwise, call the original function
            return func(self, value)
        return wrapper      # return the wrapper
    return decorator        # return the decorator
