# -*- coding: utf-8 -*-
"""
Module vashchy.py
===========================================

Module for representing Dimensionless Coefficients in Dimensional Analysis for *PyDASA*.

This module provides the Coefficient class which models dimensionless numbers used in Vaschy-Buckingham's Pi-theorem for dimensional analysis.

Classes:

    **Coefficient**: Represents a dimensionless coefficient with properties, validation, and symbolic expression.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Any, Union

# third-party imports
import numpy as np
from numpy.typing import NDArray

# custom module imports
from pydasa.core.basic import Foundation
from pydasa.elements.parameter import Variable
from pydasa.elements.specs.numerical import BoundsSpecs
# import global variables
from pydasa.core.setup import PYDASA_CFG
from pydasa.core.setup import CoefCardinality
from pydasa.serialization.parser import latex_to_python
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_range
from pydasa.validations.decorators import validate_choices
from pydasa.validations.decorators import validate_emptiness
from pydasa.validations.decorators import validate_list_types
from pydasa.validations.decorators import validate_dict_types


@dataclass
class Coefficient(Foundation, BoundsSpecs):
    """**Coefficient** class for Dimensional Analysis in *PyDASA*.

    A comprehensive implementation that represents dimensionless coefficients
    (Pi numbers) used in the Vaschy-Buckingham Pi-theorem method.

    Inherits From:
        Foundation: Base class providing symbol validation and framework context.
        BoundsSpecs: Provides numerical bounds and ranges (setpoint, min, max, mean, dev).

    Attributes:
        # From Foundation (inherited):
            name (str): User-friendly name of the dimensionless coefficient.
            description (str): Brief summary of the dimensionless coefficient.
            _idx (int): Index/precedence in the dimensional matrix.
            _sym (str): Symbol representation (LaTeX or alphanumeric).
            _alias (str): Python-compatible alias for use in code.
            _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).

        # From BoundsSpecs (inherited):
            _setpoint (Optional[float]): Specific value/point of interest (always in standardized units).
            _min (Optional[float]): Minimum value (always in standardized units).
            _max (Optional[float]): Maximum value (always in standardized units).
            _mean (Optional[float]): Average value (always in standardized units).
            _dev (Optional[float]): Standard deviation (always in standardized units).

        # Coefficient-Specific Attributes:
            _cat (str): Category (COMPUTED, DERIVED).
            relevance (bool): Flag indicating if coefficient is relevant for analysis.
            _variables (Dict[str, Variable]): Variable symbols used in coefficient construction.
            _dim_col (List[int]): Dimensional column for matrix operations.
            _pivot_lt (List[int]): Pivot indices in dimensional matrix.
            _pi_expr (str): Symbolic expression of the coefficient.
            var_dims (Dict[str, int]): Dimensional variable exponents.
            _step (Optional[float]): Step size for simulations (always in standardized units).
            _data (np.ndarray): Array of coefficient values for analysis.
    """

    # Category attribute (COMPUTED, DERIVED)
    # :attr: _cat
    _cat: str = CoefCardinality.COMPUTED.value
    """Category of the coefficient (COMPUTED, DERIVED)."""

    # Coefficient construction properties
    # :attr: _variables
    _variables: Dict[str, Variable] = field(default_factory=dict)
    """Variables symbols used in the coefficient."""

    # Coefficient calculation related variables
    # :attr: _dim_col
    _dim_col: List[int] = field(default_factory=list)
    """Dimensional column for matrix operations."""

    # :attr: var_dims
    var_dims: Dict[str, int] = field(default_factory=dict)
    """Dimensional variable exponents in coefficient."""

    # :attr: _pivot_lt
    _pivot_lt: Optional[List[int]] = field(default_factory=list)
    """Pivot indices in dimensional matrix."""

    # :attr: _pi_expr
    _pi_expr: Optional[str] = None
    """Symbolic expression of coefficient."""

    # Coefficient-specific numerical attributes (override BoundsSpecs)
    # :attr: _min
    _min: Optional[float] = None
    """Standardized minimum value of the dimensionless coefficient."""

    # :attr: _max
    _max: Optional[float] = None
    """Standardized maximum value of the dimensionless coefficient."""
    # :attr: _mean
    _mean: Optional[float] = None
    """Standardized average value of the dimensionless coefficient."""

    # :attr: _dev
    _dev: Optional[float] = None
    """Standardized standard deviation of the dimensionless coefficient."""
    # :attr: _step
    _step: Optional[float] = 1e-3
    """Step size for simulations, always in standardized units."""

    # :attr: _data
    _data: NDArray[np.float64] = field(
        default_factory=lambda: np.array([], dtype=np.float64)
    )
    """Data array for the dimensionless coefficient for analysis."""

    # Flags
    # :attr: relevance
    relevance: bool = True
    """Flag indicating if coefficient is relevant for analysis."""

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the coefficient and validates its properties.

        Performs validation of core properties and builds the coefficient expression
        based on variable symbols and their respective dimensional exponents.

        Raises:
            ValueError: If variable list and dimensional column have different lengths.
        """
        # Initialize from base class
        super().__post_init__()

        # Set the Pi symbol if not specified
        if not self._sym:
            if self._idx >= 0:
                self._sym = f"\\Pi_{{{self._idx}}}"
            else:
                self._sym = "\\Pi_{-1}"
        # Set the Python alias if not specified
        if not self._alias:
            self._alias = latex_to_python(self._sym)

        self.cat = self._cat

        # Only call setter if variables is not empty
        if self._variables:
            self.variables = self._variables

        # Only call setter if dim_col is not empty
        if self._dim_col:
            self.dim_col = self._dim_col

        # Only call setter if pivot_lt is not empty
        if self._pivot_lt:
            self.pivot_lt = self._pivot_lt

        # Only build expression if parameters and dimensions are provided
        if len(self._variables) > 0 and len(self._dim_col) > 0:
            var_keys = list(self._variables.keys())
            self.pi_expr, self.var_dims = self._build_expression(var_keys,
                                                                 self._dim_col)
        else:
            # Don't set pi_expr to empty string
            self.var_dims = {}

        # Set data
        self.data = self._data

        # Set up data array if all required values are provided
        _min = self._min
        _max = self._max
        _step = self._step

        if _min is not None and _max is not None and _step is not None:
            self._data = np.arange(_min, _max, _step, dtype=np.float64)

    def _build_expression(self,
                          var_lt: List[str],
                          dim_col: List[int]) -> tuple[str, dict]:
        """*_build_expression()* Builds LaTeX expression for coefficient.

        Args:
            var_lt (List[str]): List of variable symbols.
            dim_col (List[int]): List of dimensional exponents.

        Raises:
            ValueError: If variable list and dimensional column have different lengths.

        Returns:
            tuple[str, Dict[str, int]]: LaTeX expression and variable exponents.
        """
        # Validate variable list and dimensional column
        if len(var_lt) != len(dim_col):
            _msg = f"Variables list len ({len(var_lt)}) and "
            _msg += f"dimensional column len ({len(dim_col)}) must be equal."
            raise ValueError(_msg)

        # Initialize working variables
        numerator = []
        denominator = []
        parameters = {}

        # Process parameters and their exponents
        for sym, exp in zip(var_lt, dim_col):
            # Add to numerator if exponent is positive
            if exp > 0:
                part = sym if exp == 1 else f"{sym}^{{{exp}}}"
                numerator.append(part)
            # Add to denominator if exponent is negative
            elif exp < 0:
                part = sym if exp == -1 else f"{sym}^{{{-exp}}}"
                denominator.append(part)
            # Skip zero exponents
            else:
                continue
            # Store variable exponent
            parameters[sym] = exp

        # Build expression
        num_str = "1" if not numerator else "*".join(numerator)

        # Return expression based on whether denominator exists
        if not denominator:
            return num_str, parameters
        else:
            denom_str = "*".join(denominator)
            return f"\\frac{{{num_str}}}{{{denom_str}}}", parameters

    # Property getters and setters

    @property
    def cat(self) -> str:
        """*cat* Get the coefficient category.

        Returns:
            str: Category (COMPUTED, DERIVED).
        """
        return self._cat

    @cat.setter
    @validate_choices(PYDASA_CFG.coefficient_cardinality)
    def cat(self, val: str) -> None:
        """*cat* Set the coefficient category.

        Args:
            val (str): Category value.

        Raises:
            ValueError: If category is not supported.
        """
        self._cat = val.upper()

    @property
    def variables(self) -> Dict[str, Variable]:
        """*variables* Get the variable symbols dictionary.

        Returns:
            Dict[str, Variable]: Variables symbols dictionary.
        """
        return self._variables

    @variables.setter
    @validate_type(dict, allow_none=False)
    @validate_emptiness()
    @validate_dict_types(str, Variable)
    def variables(self, val: Dict[str, Variable]) -> None:
        """*variables* Set the variable symbols dictionary.

        Args:
            val (Dict[str, Variable]): Variables symbols dictionary.

        Raises:
            ValueError: If variables dictionary is invalid.
        """
        self._variables = val

    @property
    def dim_col(self) -> List[int]:
        """*dim_col* Get the dimensional column.

        Returns:
            List[int]: Dimensional column.
        """
        return self._dim_col

    @dim_col.setter
    @validate_type(list, allow_none=False)
    @validate_emptiness()
    @validate_list_types(int, float)
    def dim_col(self, val: Union[List[int], List[float]]) -> None:
        """*dim_col* Set the dimensional column.

        Args:
            val (Union[List[int], List[float]]): Dimensional column.
        Raises:
            ValueError: If dimensional column is invalid.
        """
        # Convert to integers
        self._dim_col = [int(x) for x in val]

    @property
    def pivot_lt(self) -> Optional[List[int]]:
        """*pivot_lt* Get the pivot indices list.

        Returns:
            Optional[List[int]]: Pivot indices list.
        """
        return self._pivot_lt

    @pivot_lt.setter
    @validate_type(list, allow_none=True)
    @validate_list_types(int)
    def pivot_lt(self, val: List[int]) -> None:
        """*pivot_lt* Set the pivot indices list.

        Args:
            val (List[int]): Pivot indices list.

        Raises:
            ValueError: If pivot list is invalid.
        """
        self._pivot_lt = val

    @property
    def pi_expr(self) -> Optional[str]:
        """*pi_expr* Get the coefficient expression.

        Returns:
            Optional[str]: Coefficient expression.
        """
        return self._pi_expr

    @pi_expr.setter
    @validate_type(str, allow_none=True)
    @validate_emptiness()
    def pi_expr(self, val: str) -> None:
        """*pi_expr* Set the coefficient expression.

        Args:
            val (str): Coefficient expression.

        Raises:
            ValueError: If the coefficient expression is not a string.
        """
        self._pi_expr = val

    # Value range properties specific to Coefficient

    @property
    def step(self) -> Optional[float]:
        """*step* Get standardized step size.

        Returns:
            Optional[float]: Step size (always standardized).
        """
        return self._step

    @step.setter
    @validate_type(int, float, allow_none=False)
    @validate_range(min_value=0,
                    min_inclusive=False,
                    min_attr="_min",
                    max_attr="_max")
    def step(self, val: Optional[float]) -> None:
        """*step* Set standardized step size.

        Args:
            val (Optional[float]): Step size (always standardized).
        """
        self._step = val

    @property
    def data(self) -> NDArray[np.float64]:
        """*data* Get standardized data array.

        Returns:
            NDArray[np.float64]: Data array for range (always standardized).
        """
        return self._data

    @data.setter
    @validate_type(list, np.ndarray, allow_none=False)
    def data(self, val: NDArray[np.float64]) -> None:
        """*data* Set standardized data array.

        Args:
            val (NDArray[np.float64]): Data array for range (always standardized).

        Raises:
            ValueError: If value is not a numpy array.
        """
        # always store as numpy array
        if isinstance(val, list):
            val = np.array(val, dtype=np.float64)
        self._data = val

    # @validate_type(dict, allow_none=True)
    # @validate_dict_types(str, (int, float))
    def calculate_setpoint(self,
                           vars: Optional[Dict[str, float]] = None) -> float:
        """*calculate_setpoint()* Calculate coefficient setpoint value based on provided variable setpoints. If no variables are provided uses the ones stored in the variables standardized attribute.

        Args:
            vars (Optional[Dict[str, float]]): Variable setpoints dictionary.

        Raises:
            ValueError: If variable setpoints are missing or invalid.
            ValueError: If number of variable setpoints does not match coefficient variables.
        """
        if vars is None:
            vars = {}
            # check stored variables for setpoints
            # Only collect variables that are actually used in this coefficient
            for sym in self.var_dims.keys():
                if sym not in self._variables:
                    _msg = f"Variable '{sym}' not found in stored variables."
                    raise ValueError(_msg)
                var = self._variables[sym]
                if var.std_setpoint is None:
                    _msg = f"Variable '{sym}' std_setpoint is not defined."
                    raise ValueError(_msg)
                vars[sym] = var.std_setpoint  # Use standardized units

        # validate provided setpoints
        if len(vars) != len(self.var_dims):
            _msg = f"No. of Variable setpoints ({len(vars)}) does not "
            _msg += f"match coefficient variables ({len(self.var_dims)})."
            raise ValueError(_msg)

        # TODO can be make in symbolic, sympy is worth it?
        # setpoint start at 1.0 for multiplication
        setpoint = 1.0
        for sym, exp in self.var_dims.items():
            # if every variable setpoint is provided
            if sym not in vars:
                _msg = f"Variable '{sym}' std_setpoint is missing for "
                _msg += f"coefficient '{self._sym}' calculation."
                raise ValueError(_msg)
            var_setpoint = vars[sym]
            # calculate setpoint
            setpoint *= var_setpoint**exp
        # store calculated setpoint
        self._setpoint = setpoint
        return setpoint

    def generate_data(self) -> None:
        """*generate_data()* Generate a linear standardized data array from min, max, using step value.

        Raises:
            ValueError: If needed values are missing.
        """
        # Type narrow using local variables
        _min = self._min
        _max = self._max
        _step = self._step

        if _min is not None and _max is not None and _step is not None:
            self._data = np.arange(_min, _max, _step, dtype=np.float64)
        else:
            _msg = "Cannot generate data array. Needed values are missing: "
            _msg += f"_min={_min}, _max={_max}, _step={_step}."
            raise ValueError(_msg)

    def get_data(self) -> Dict[str, List]:
        """*get_data()* Get data array from the dimensionless coefficient and its variables.

        Returns:
            Dict[str, List]: Data dictionary with 'symbol': data_list entries.
        """
        ans = dict()
        # Add variable data
        for sym, var in self.variables.items():
            ans[sym] = var.data
        # Add coefficient data
        ans[self._sym] = self.data.tolist()
        return ans

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values.

        Resets all coefficient properties to their initial state.
        """
        # Reset parent class attributes (Foundation and BoundsSpecs)
        super().clear()
        self._sym = f"\\Pi_{{{self._idx}}}"

        # Reset coefficient-specific attributes
        self._cat = CoefCardinality.COMPUTED.value
        self._variables = {}
        self._dim_col = []
        self._pivot_lt = []
        self._pi_expr = None
        self.var_dims = {}
        self._step = 1e-3
        self._data = np.array([], dtype=np.float64)
        self.relevance = True

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert variable to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of variable.
        """
        result = {}

        # Get all dataclass fields
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, attr_name)

            # Skip numpy arrays (not JSON serializable without special handling)
            if isinstance(attr_value, np.ndarray):
                # Convert to list for JSON compatibility
                attr_value = attr_value.tolist()

            # Skip callables (can't be serialized)
            if callable(attr_value) and attr_name == "_dist_func":
                continue

            # Remove leading underscore from private attributes
            if attr_name.startswith("_"):
                clean_name = attr_name[1:]  # Remove first character
            else:
                clean_name = attr_name

            result[clean_name] = attr_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Coefficient:
        """*from_dict()* Create variable from dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary representation of variable.

        Returns:
            Variable: New variable instance.
        """
        # Get all valid field names from the dataclass
        field_names = {f.name for f in fields(cls)}

        # Map keys without underscores to keys with underscores
        _data = {}

        for key, value in data.items():
            # Try the key as-is first (handles both _idx and name)
            if key in field_names:
                _data[key] = value
            # Try adding underscore prefix (handles idx -> _idx)
            elif f"_{key}" in field_names:
                _data[f"_{key}"] = value
            # Try removing underscore prefix (handles _name -> name if needed)
            elif key.startswith("_") and key[1:] in field_names:
                _data[key[1:]] = value
            else:
                # Use as-is for unknown keys (will be validated by dataclass)
                _data[key] = value

        # Convert lists back to numpy arrays for range attributes
        for _data_key in ["_data", "data"]:
            if _data_key in _data and isinstance(_data[_data_key], list):
                _data[_data_key] = np.array(_data[_data_key],
                                            dtype=np.float64)

        return cls(**_data)
