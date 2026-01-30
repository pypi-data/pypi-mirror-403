# -*- coding: utf-8 -*-
"""
Module fundamental.py
===========================================

Module for representing the **FDU** or **Fundamental Dimensional Unit** for Dimensional Analysis in *PyDASA*.

Classes:
    **Dimension**: Represents a Fundamental Dimensional Unit (FDU) with validation and conversion capabilities.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
# import dataclass for defining the node class
from __future__ import annotations
from dataclasses import dataclass
# import re

# custom modules
from pydasa.core.basic import Foundation
from pydasa.core.setup import Frameworks   # , PYDASA_CFG

# generic error handling and type checking
from pydasa.validations.error import handle_error as error

# import validation decorators
from pydasa.validations.decorators import validate_type, validate_emptiness

# checking custom modules
assert error


@dataclass
class Dimension(Foundation):
    """
    **Dimension** class for processing the data of a Fundamental Dimensional Unit (FDU) in *PyDASA*.

    FDUs are fundamental building blocks of dimensional analysis and are used to define the dimensions of physical and digital quantities.

    Args:
        Foundation: Foundation class for validation of symbols and frameworks.

    Attributes:
        _idx (int): The Index of the Fundamental Dimension (precedence in the Dimensional Matrix).
        _sym (str): The symbol of the Fundamental Dimension (LaTeX or alphanumeric).
        _alias (str): The Python-compatible alias for the Fundamental Dimension, used in executable code.
        _fwk (str): The framework of the Fundamental Dimension (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).
        _unit (str): The basic unit of the Fundamental Dimension, useful for unit of meassure convertion (e.g.: km -> m or GB -> bit).
        name (str): User-friendly name of the Fundamental Dimension.
        description (str): Brief summary of the Fundamental Dimension.
    """
    # All attributes and validation logic are inherited from SymBasis.
    # You can add any FDU-specific methods or overrides here if needed.

    # :attr: _idx
    _unit: str = ""
    """Basic unit of the Fundamental Dimension (e.g.: m, s, bit)."""

    def __post_init__(self) -> None:
        """*__post_init__()* Post-initialization processing with symbol and framework validation.
        """
        # Call the parent class's post-init
        super().__post_init__()

        # Validate the unit
        if not self.unit:
            self._unit = self._unit.strip()

    @property
    def unit(self) -> str:
        """*unit* Get the framework.

        Returns:
            str: Frameworks value
        """
        return self._unit

    @unit.setter
    @validate_type(str, allow_none=False)
    @validate_emptiness()
    def unit(self, val: str) -> None:
        """*unit* Set the unit with validation.

        Args:
            val (str): Unit value

        Raises:
            ValueError: If unit is not supported
        """
        self._unit = val

    def to_dict(self) -> dict:
        """*to_dict* Convert the Dimension to a dictionary representation.

        Returns:
            dict: Dictionary representation of the Dimension.
        """
        return {
            "idx": self._idx,
            "sym": self._sym,
            "alias": self._alias,
            "fwk": self._fwk,
            "unit": self._unit,
            "name": self.name,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> Dimension:
        """*from_dict* Create a Dimension instance from a dictionary.

        Args:
            data (dict): Dictionary containing Dimension attributes.

        Returns:
            Dimension: Instance of Dimension created from the dictionary.
        """
        return cls(
            _idx=data.get("idx", -1),
            _sym=data.get("sym", ""),
            _alias=data.get("alias", ""),
            _fwk=data.get("fwk", Frameworks.PHYSICAL.value),
            _unit=data.get("unit", ""),
            _name=data.get("_name", ""),
            description=data.get("description", "")
        )

    def __eq__(self, other: object) -> bool:
        """*__eq__()* Check equality of two Dimension objects.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, Dimension):
            return NotImplemented
        eq_sym = self._sym == other._sym
        eq_fwk = self._fwk == other._fwk
        eq_alias = self._alias == other._alias
        eq_unit = self._unit == other._unit
        # return (self._sym == other._sym and self._fwk == other._fwk)
        return eq_sym and eq_fwk and eq_alias and eq_unit
