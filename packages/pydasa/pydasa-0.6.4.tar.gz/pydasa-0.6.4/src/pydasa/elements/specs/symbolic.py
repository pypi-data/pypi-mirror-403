# -*- coding: utf-8 -*-
"""
Module symbolic.py
===========================================

Symbolic perspective for variable representation.

This module defines the SymbolicSpecs class representing the mathematical
and notational properties of a variable.

Classes:
    **SymbolicSpecs**: Symbolic variable specifications

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
# dataclass imports
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
import re

# custom modules
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_emptiness

# Type checking imports (not at runtime to avoid circular imports)
if TYPE_CHECKING:
    from pydasa.dimensional.vaschy import Schema


@dataclass
class SymbolicSpecs:
    """Symbolic perspective: mathematical representation. Answers the question: "How do we WRITE this variable?"

    This perspective focuses on:
        - Symbol notation (LaTeX, Python alias)
        - Dimensional formulas (L, M, T, etc.)
        - Unit systems (original and standardized)
        - Matrix representation for linear algebra
        - Integration with symbolic math libraries

    Attributes:
        # From SymbolicSpecs
            _dims (str): Dimensional expression (e.g., "L*T^-1").
            _units (str): Units of measure (e.g., "m/s").
            _std_dims (Optional[str]): Standardized dimensional expression. e.g.: from [T^2*L^-1] to [L^(-1)*T^(2)].
            _sym_exp (Optional[str]): Sympy-compatible dimensional expression. e.g.: from [T^2*L^-1] to [T**2*L**(-1)].
            _dim_col (List[int]): Dimensional column for matrix operations. e.g.: from [T^2*L^-1] to [2, -1].
            _std_units (str): Standardized units of measure. e.g `km/h` -> `m/s`, `kByte/s` -> `bit/s`.
    """

    # Type annotation for _schema attribute (defined in ConceptualSpecs, accessed via composition)
    if TYPE_CHECKING:
        _schema: Optional[Schema]

    # Dimensional properties
    # :attr: _dims
    _dims: str = ""
    """Dimensional expression (e.g., "L*T^-1")."""

    # :attr: _units
    _units: str = ""
    """Units of measure (e.g., "m/s")."""

    # Processed dimensional attributes
    # :attr: _std_dims
    _std_dims: Optional[str] = None
    """Standardized dimensional expression. e.g.: from [T^2*L^-1] to [L^(-1)*T^(2)]."""

    # :attr: _sym_exp
    _sym_exp: Optional[str] = None
    """Sympy-compatible dimensional expression. e.g.: from [T^2*L^-1] to [T**2*L**(-1)]."""

    # :attr: _std_col
    _dim_col: List[int] = field(default_factory=list)
    """Dimensional column for matrix operations. e.g.: from [T^2*L^-1] to [2, -1]."""

    # Value ranges (standardized units)
    # :attr: _std_units
    _std_units: str = ""
    """Standardized units of measure. e.g `km/h` -> `m/s`, `kByte/s` -> `bit/s`."""

    def _validate_exp(self, exp: str, regex: str) -> bool:
        """*_validate_exp()* Validates an expression using a regex pattern (inclde dimensions and units,).

        Args:
            dims (str): Dimensions of the parameter. It is a string with the FDU formula of the parameter. e.g.: [T^2*L^-1]

        Returns:
            bool: True if the dimensions are valid, False otherwise, ignoring null or empty strings.
        """
        # TODO improve this ignoring null or empty strings for constants
        if exp in [None, ""]:
            return True
        return bool(re.match(regex, exp))

    def _prepare_dims(self) -> None:
        """*_prepare_dims()* Processes dimensional expressions for analysis.

        Standardizes and sorts dimensions, creates sympy expression and dimensional column.
        """
        self._std_dims = self._standardize_dims(self._dims)
        self._std_dims = self._sort_dims(self._std_dims)
        self._sym_exp = self._setup_sympy(self._std_dims)
        self._dim_col = self._setup_column(self._sym_exp)

    def _standardize_dims(self, dims: str) -> str:
        """*_standardize_dims()* Standardizes dimensional expression format.

        Args:
            dims (str): Dimensional expression (e.g., "L*T^-1").

        Returns:
            str: Standardized expression with parentheses (e.g., "L^(1)*T^(-1)").
        """
        if self._schema is None:
            _msg = "Schema must be initialized before standardizing dimensions"
            raise ValueError(_msg)

        # Add parentheses to powers
        # _pattern = re.compile(cfg.WKNG_POW_RE)
        _pattern = re.compile(self._schema.fdu_pow_regex)
        dims = _pattern.sub(lambda m: f"({m.group(0)})", dims)

        # Add ^1 to dimensions without explicit powers
        # _pattern = re.compile(cfg.WKNG_NO_POW_RE)
        _pattern = re.compile(self._schema.fdu_no_pow_regex)
        dims = _pattern.sub(lambda m: f"{m.group(0)}^(1)", dims)
        return dims

    def _sort_dims(self, dims: str) -> str:
        """*_sort_dims()* Sorts dimensions based on FDU precedence.

        Args:
            dims (str): Standardized dimensional expression. e.g.: [T^2*L^-1].

        Returns:
            str: Sorted dimensional expression. e.g.: [L^(-1)*T^(2)].
        """
        if self._schema is None:
            _msg = "Schema must be initialized before standardizing dimensions"
            raise ValueError(_msg)
        # Local variable for type narrowing
        _schema = self._schema

        # TODO move '*' as global operator to cfg module?
        # Split by multiplication operator
        _dims_lt = dims.split("*")

        # Sort based on FDU precedence
        # _dims_lt.sort(key=lambda x: cfg.WKNG_FDU_PREC_LT.index(x[0]))
        _dims_lt.sort(key=lambda x: _schema.fdu_symbols.index(x[0]))

        # Rejoin with multiplication operator
        _dims = "*".join(_dims_lt)
        return _dims

    def _setup_sympy(self, dims: str) -> str:
        """*_setup_sympy()* Creates sympy-compatible expression.

        Args:
            dims (str): Standardized dimensional expression. e.g.: [T^2*L^-1].

        Returns:
            str: Sympy-compatible expression. e.g.: [T**2* L**(-1)].
        """
        # TODO move '*' and '* ' as global operator to cfg module?
        # TODO do I use also regex for this?
        # replace '*' with '* ' for sympy processing
        # # replace '^' with '**' for sympy processing
        return dims.replace("*", "* ").replace("^", "**")

    def _setup_column(self, dims: str) -> List[int]:
        """*_setup_column()* Generates dimensional column (list of exponents) in the Dimensional Matrix.

        Args:
            dims (str): Standardized dimensional expression. e.g.: [T^(2)*L^(-1)]

        Returns:
            List[int]: Exponents with the dimensional expression. e.g.: [2, -1]

        Raises:
            ValueError: If dimensional expression cannot be parsed.
        """
        if self._schema is None:
            _msg = "Schema must be initialized before standardizing dimensions"
            raise ValueError(_msg)
        # Local variable for type narrowing
        _schema = self._schema

        # split the sympy expression into a list of dimensions
        dims_list = dims.split("* ")
        # set the default list of zeros with the FDU length
        # col = [0] * len(cfg.WKNG_FDU_PREC_LT)
        col = [0] * len(_schema.fdu_symbols)

        for dim in dims_list:
            # match the exponent of the dimension
            exp_match = re.search(_schema.fdu_pow_regex, dim)
            if exp_match is None:
                _msg = f"Could not extract exponent from dimension: {dim}"
                raise ValueError(_msg)
            _exp = int(exp_match.group(0))

            # match the symbol of the dimension
            sym_match = re.search(_schema.fdu_sym_regex, dim)
            if sym_match is None:
                _msg = f"Could not extract symbol from dimension: {dim}"
                raise ValueError(_msg)
            _sym = sym_match.group(0)

            # Check if symbol exists in the precedence list
            if _sym not in _schema.fdu_symbols:
                _msg = f"Unknown dimensional symbol: {_sym}"
                raise ValueError(_msg)

            # update the column with the exponent of the dimension
            col[_schema.fdu_symbols.index(_sym)] = _exp

        return col

    # Dimensional Properties

    @property
    def dims(self) -> str:
        """*dims* Get the dimensional expression.

        Returns:
            str: Dimensions. e.g.: [T^2*L^-1]
        """
        return self._dims

    @dims.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def dims(self, val: str) -> None:
        """*dims* Sets the dimensional expression.

        Args:
            val (str): Dimensions. e.g.: [T^2*L^-1]

        Raises:
            ValueError: If expression is empty
            ValueError: If dimensions are invalid according to the precedence.
        """
        if self._schema is None:
            _msg = "Schema must be initialized before standardizing dimensions"
            raise ValueError(_msg)
        # Local variable for type narrowing
        _schema = self._schema

        # Process dimensions
        if val and not self._validate_exp(val, _schema.fdu_regex):
            _msg = f"Invalid dimensional expression: {val}. "
            _msg += f"FDUS precedence is: {_schema.fdu_regex}"
            raise ValueError(_msg)

        self._dims = val

        # automatically prepare the dimensions for analysis
        self._prepare_dims()

    @property
    def units(self) -> str:
        """*units* Get the units of measure.

        Returns:
            str: Units of measure. e.g.: `m/s`, `kg/m3`, etc.
        """
        return self._units

    @units.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def units(self, val: str) -> None:
        """*units* Sets the units of measure.

        Args:
            val (str): Units of measure. i.e `m/s`, `kg/m3`, etc.

        Raises:
            ValueError: If units are empty.
        """
        self._units = val

    @property
    def sym_exp(self) -> Optional[str]:
        """*sym_exp* Get Sympy-compatible expression.

        Returns:
            Optional[str]: Sympy expression. e.g.: [T**2*L**(-1)]
        """
        return self._sym_exp

    @sym_exp.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def sym_exp(self, val: str) -> None:
        """*sym_exp* Sets Sympy-compatible expression.

        Args:
            val (str): Sympy expression. e.g.: [T**2*L**(-1)]

        Raises:
            ValueError: If the string is empty.
        """
        self._sym_exp = val

    @property
    def dim_col(self) -> Optional[List[int]]:
        """*dim_col* Get dimensional column.

        Returns:
            Optional[List[int]]: Dimensional exponents. e.g.: [2, -1]
        """
        return self._dim_col

    @dim_col.setter
    def dim_col(self, val: List[int]) -> None:
        """*dim_col* Sets the dimensional column

        Args:
            val (List[int]): Dimensional exponents. i.e..: [2, -1]

        Raises:
            ValueError: if the dimensional column is not a list of integers.
        """
        if val is not None and not isinstance(val, list):
            raise ValueError("Dimensional column must be a list of integers.")
        self._dim_col = val

    # Standardized Dimensional Properties

    @property
    def std_dims(self) -> Optional[str]:
        """*std_dims* Get the standardized dimensional expression.

        Returns:
            Optional[str]: Standardized dimensional expression. e.g.: [L^(-1)*T^(2)]
        """
        return self._std_dims

    @std_dims.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def std_dims(self, val: str) -> None:
        """*std_dims* Sets the standardized dimensional expression.

        Args:
            val (str): Standardized dimensional expression. e.g.: [L^(-1)*T^(2)]

        Raises:
            ValueError: If the standardized dimensional expression is empty.
        """
        self._std_dims = val

    @property
    def std_units(self) -> Optional[str]:
        """*std_units* Get the standardized Unit of Measure.

        Returns:
            Optional[str]: standardized Unit of Measure.
        """
        return self._std_units

    @std_units.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def std_units(self, val: str) -> None:
        """*std_units* Sets the standardized Unit of Measure.

        Args:
            val (Optional[str]): standardized Unit of Measure.

        Raises:
            ValueError: If standardized units are empty.
        """
        self._std_units = val

    def clear(self) -> None:
        """*clear()* Reset symbolic attributes to default values.

        Resets dimensions, units, and all processed dimensional attributes.
        """
        self._dims = ""
        self._units = ""
        self._std_dims = None
        self._sym_exp = None
        self._dim_col = []
        self._std_units = ""
