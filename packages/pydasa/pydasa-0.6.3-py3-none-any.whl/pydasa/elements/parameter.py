# -*- coding: utf-8 -*-
"""
Module parameter.py
===========================================

Module for representing **Variable** entities in Dimensional Analysis for *PyDASA*.

Classes:
    **Variable**: Represents a Variable with dimensional properties, value ranges, and validation.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
# dataclass imports
from __future__ import annotations
from dataclasses import dataclass, fields
# data type imports
from typing import Dict, Any
# numerical imports
import numpy as np

# custom modules
# Import the four compositional perspectives
from pydasa.elements.specs import ConceptualSpecs
from pydasa.elements.specs import SymbolicSpecs
from pydasa.elements.specs import NumericalSpecs
from pydasa.elements.specs import StatisticalSpecs
# pattern interpreter imports
from pydasa.serialization.parser import latex_to_python


@dataclass
class Variable(ConceptualSpecs, SymbolicSpecs, NumericalSpecs, StatisticalSpecs):
    """**Variable** class for Dimensional Analysis in *PyDASA*.

    A comprehensive implementation that combines Parameter and Variable functionality for use in dimensional analysis calculations, simulations, and sensitivity analysis.

    This class composes four philosophical perspectives through multiple inheritance:
    - **ConceptualSpecs**: Identity and classification (what IS this variable?)
    - **SymbolicSpecs**: Mathematical representation (how do we WRITE it?)
    - **NumericalSpecs**: Computational values (what VALUES can it take?)
    - **StatisticalSpecs**: Probabilistic modeling (how do we MODEL uncertainty?)

    All attributes, properties, and methods are inherited from the spec classes.

    This class only provides integration logic and utility methods.

    Attributes:
        # From Foundation (via ConceptualSpecs)
        _name (str): User-friendly name of the variable.
        description (str): Brief summary of the variable.
        _idx (int): Index/precedence in the dimensional matrix.
        _sym (str): Symbol representation (LaTeX or alphanumeric).
        _alias (str): Python-compatible alias for use in code.
        _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).

        # From ConceptualSpecs - Identity and Classification
        _cat (str): Category (INPUT, OUT, CTRL).
        _schema (Schema): Reference to the dimensional framework or FDUs list.
        relevant (bool): Flag indicating if variable is relevant for analysis.

        # From SymbolicSpecs - Dimensional Properties
        _dims (str): Dimensional expression (e.g., "L*T^-1").
        _units (str): Units of measure (e.g., "m/s").
        _sym_exp (str): Sympy-compatible expression.
        _dim_col (List[int]): Dimensional column for matrix operations.

        # From SymbolicSpecs - Standardized Dimensional Properties
        _std_dims (str): Standardized dimensional expression.
        _std_units (str): Standardized units of measure.

        # From NumericalSpecs - Value Ranges (Original Units)
        _min (float): Minimum value in original units.
        _max (float): Maximum value in original units.
        _mean (float): Mean value in original units.
        _dev (float): Standard deviation in original units.

        # From NumericalSpecs - Value Ranges (Standardized Units)
        _std_min (float): Minimum value in standard units.
        _std_max (float): Maximum value in standard units.
        _std_mean (float): Mean value in standard units.
        _std_dev (float): Standard deviation in standard units.
        _step (float): Step size for simulations.
        _std_range (np.ndarray): Range array for analysis.

        # From StatisticalSpecs - Distribution Specifications
        _dist_type (str): Type of distribution (e.g., 'uniform', 'normal').
        _dist_params (Dict[str, Any]): Parameters for the distribution.
        _depends (List[str]): List of variable names that this variable depends on.
        _dist_func (Callable): Callable representing the distribution function.
    """

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the variable and validates its properties.

        Performs validation of core properties and processes dimensional expressions.
        Sets up range arrays if all required values are provided.

        Raises:
            ValueError: If dimensional expression is invalid.
        """
        # Initialize from base class (ConceptualSpecs -> Foundation)
        # This also sets up the schema based on framework
        super().__post_init__()

        if not self._sym:
            self._sym = f"V_{self._idx}" if self._idx >= 0 else "V_{}"

        # if custom schema is provided and dimensions exist
        if self._schema and len(self._dims) > 0 and self._dims != "n.a.":
            #     if not self._schema.validate_dims(self._dims):
            #         raise ValueError(f"Invalid dimensions for {self._fwk}")
            # # Process dimensions if provided
            # if len(self._dims) > 0 and self._dims != "n.a.":
            _schema = self._schema
            if not self._validate_exp(self._dims, _schema.fdu_regex):
                _msg = f"Invalid dimensions {self._dims} for '{self._sym}'."
                _msg += f"Check FDU precedence list: {_schema.fdu_lt}."
                raise ValueError(_msg)
            self._prepare_dims()

        # Set the Python alias if not specified
        if not self._alias:
            self._alias = latex_to_python(self._sym)

        std_min = self._std_min
        std_max = self._std_max
        step = self._step

        # NOTE: OLD CODE keep for reference
        # if all([self._std_min is not None,
        #         self._std_max is not None,
        #         self._step is not None]):
        if std_min is not None and std_max is not None and step is not None:
            self._std_range = np.arange(std_min, std_max, step)

    # NOTE: All methods below are inherited from spec classes:
    # - All properties (cat, dims, units, min, max, etc.) are inherited from respective specs

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values.

        Resets all variable properties to their initial state by calling
        clear() on all composed perspective classes.
        """
        # Call clear on all parent classes
        ConceptualSpecs.clear(self)
        SymbolicSpecs.clear(self)
        NumericalSpecs.clear(self)
        StatisticalSpecs.clear(self)

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
    def from_dict(cls, data: Dict[str, Any]) -> Variable:
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
        for _data_key in ["data", "_data"]:
            if _data_key in _data and isinstance(_data[_data_key], list):
                _data[_data_key] = np.array(_data[_data_key])

        return cls(**_data)
