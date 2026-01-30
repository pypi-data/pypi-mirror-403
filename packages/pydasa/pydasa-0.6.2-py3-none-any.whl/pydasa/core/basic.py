# -*- coding: utf-8 -*-
"""
Module basic.py
===========================================

This module provides base classes with common validation logic used across FDU, Parameter, and Variable classes to eliminate code duplication.

Classes:
    **Foundation**: enforces common validation logic.
    **IdxBasis**: enforces index/precedence validation logic.
    **SymBasis**: enforces symbol and framework validation logic.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""
# native python modules
# forward references + postpone eval type hints
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import inspect

# indicate it is an abstract base class
from abc import ABC

# import global variables
from pydasa.core.setup import Frameworks
from pydasa.core.setup import PYDASA_CFG
from pydasa.validations.patterns import LATEX_RE

# import validation decorators
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_emptiness
from pydasa.validations.decorators import validate_choices
from pydasa.validations.decorators import validate_pattern
from pydasa.validations.decorators import validate_index


@dataclass
class SymBasis(ABC):
    """**SymBasis** Foundation class for entities with symbols and framework functionalities.

    Args:
        ABC (ABC): Abstract base class.

    Attributes:
        _sym (str): Symbol representation.
        _alias (str): Python-compatible alias for use in code.
        _fwk (str): Frameworks context.
    """

    # :attr: _sym
    _sym: str = ""
    """Symbol representation (LaTeX or alphanumeric)."""

    # :attr: _fwk
    _fwk: str = Frameworks.PHYSICAL.value
    """Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM)."""

    # :attr: _alias
    _alias: str = ""
    """Python-compatible alias for symbol, used in executable code. e.g.: `\\rho_{1}` -> `rho_1`."""

    def __post_init__(self) -> None:
        """*__post_init__()* Post-initialization processing with symbol and framework validation.
        """
        # super().__post_init__()
        # Validate the symbol and framework
        if not self._sym:
            self._sym = self._sym.strip()
        if not self._fwk:
            self._fwk = self._fwk.strip()
        if not self._alias:
            self._alias = self._alias.strip()

    @property
    def sym(self) -> str:
        """*sym* Get the symbol.

        Returns:
            str: Symbol value.
        """
        return self._sym

    @sym.setter
    @validate_type(str)
    @validate_emptiness()
    @validate_pattern(LATEX_RE, allow_alnum=True)
    def sym(self, val: str) -> None:
        """*sym* Set the symbol with validation.

        Args:
            val (str): Symbol value.

        Raises:
            ValueError: If symbol format is invalid.
        """
        self._sym = val

    @property
    def fwk(self) -> str:
        """*fwk* Get the framework.

        Returns:
            str: Frameworks value.
        """
        return self._fwk

    @fwk.setter
    @validate_type(str)
    @validate_choices(PYDASA_CFG.frameworks)
    def fwk(self, val: str) -> None:
        """*fwk* Set the framework with validation.

        Args:
            val (str): Frameworks value.

        Raises:
            ValueError: If framework is not supported.
        """
        self._fwk = val

    @property
    def alias(self) -> Optional[str]:
        """*alias* Get the Python variable synonym.

        Returns:
            Optional[str]: Python variable name. e.g.: `\\rho_{1}` -> `rho_1`.
        """
        return self._alias

    @alias.setter
    @validate_type(str)
    @validate_emptiness()
    def alias(self, val: str) -> None:
        """*alias* Set the Python variable synonym.

        Args:
            val (str): Python variable name. e.g.: `\\rho_{1}` -> `rho_1`.

        Raises:
            ValueError: If variable name is empty.
        """
        self._alias = val

    def clear(self) -> None:
        """*clear()* Reset symbol and framework attributes to default values.

        Resets the entity's symbol-related properties to their initial state.
        """
        # Reset symbol attributes
        self._sym = ""
        self._alias = ""
        self._fwk = Frameworks.PHYSICAL.value


@dataclass
class IdxBasis(SymBasis):
    """**IdxBasis** Foundation class for entities with index/precedence functionality.

    Args:
        SymBasis (SymBasis): Inherits symbol and framework validation.

    Attributes:
        _idx (int): Index/precedence value
    """

    # :attr: _idx
    _idx: int = -1
    """Unique identifier/index for ordering in dimensional matrix."""

    def __post_init__(self) -> None:
        """*__post_init__()* Post-initialization processing with symbol and framework validation.
        """
        super().__post_init__()
        if self._idx != -1:
            self.idx = self._idx

    @property
    def idx(self) -> int:
        """*idx* Get the index/precedence value.

        Returns:
            int: Index value.
        """
        return self._idx

    @idx.setter
    @validate_type(int, allow_none=False)
    @validate_index()
    def idx(self, val: int) -> None:
        """*idx* Set the index/precedence value.

        Args:
            val (int): Index value (must be non-negative).

        Raises:
            ValueError: If index is not a non-negative integer.
        """
        self._idx = val

    def clear(self) -> None:
        """*clear()* Reset index and inherited attributes to default values.

        Resets the entity's index and symbol-related properties to their initial state.
        """
        # Reset parent class attributes
        super().clear()

        # Reset index attribute
        self._idx = -1


@dataclass
class Foundation(IdxBasis):
    """**Foundation** Foundation class for all dimensional analysis entities.

    Provides common validation logic and attributes shared by FDU, Variable, and Coeffcient classes.

    Args:
        IdxBasis (IdxBasis): Inherits index, symbol, and framework validation.

    Attributes:
        name (str): User-friendly name
        description (str): Brief summary or description
    """

    # :attr: _name
    _name: str = ""
    """User-friendly name of the entity."""

    # :attr: description
    description: str = ""
    """Brief summary or description of the entity."""

    def __post_init__(self) -> None:
        """*__post_init__()* Post-initialization processing with description capitalization.
        """
        if self.description:
            self.description = self.description.strip()

    @property
    def name(self) -> str:
        """*name* Get the name.

        Returns:
            str: Name value.
        """
        return self._name

    @name.setter
    @validate_type(str, allow_none=False)
    def name(self, val: str) -> None:
        """*name* Set the name with validation.

        Args:
            val (str): Name value.

        Raises:
            ValueError: If name is not a non-empty string.
        """
        self._name = val.strip()

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values.

        Resets the entity's properties to their initial state.
        """
        # Reset parent class attributes
        super().clear()

        # Reset name and description attributes
        self.name = ""
        self.description = ""

    def __str__(self) -> str:
        """*__str__()* Detailed string representation with all attributes.

        Returns a comprehensive view of all non-private attributes, suitable for
        detailed inspection and logging.

        Returns:
            str: Detailed string representation with all attributes.
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
            _attr_lt.append(f"{_attr_name}={repr(value)}")
        # Format the string with the class name and the attributes
        _str = f"{self.__class__.__name__}({', '.join(_attr_lt)})"
        return _str

    def __repr__(self) -> str:
        """*__repr__()* Detailed string representation.

        Returns:
            str: String representation.
        """
        return self.__str__()
