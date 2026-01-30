# -*- coding: utf-8 -*-
"""
Module conceptual.py
===========================================

Conceptual perspective for variable representation.

This module defines the ConceptualSpecs class representing the abstract
identity and classification of a variable.

Classes:
    **ConceptualSpecs**: Conceptual variable specifications

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
# dataclass imports
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

# custom modules
from pydasa.core.basic import Foundation
from pydasa.dimensional.vaschy import Schema
from pydasa.core.setup import Frameworks
from pydasa.core.setup import VarCardinality
from pydasa.core.setup import PYDASA_CFG
from pydasa.validations.decorators import validate_choices


@dataclass
class ConceptualSpecs(Foundation):
    """Conceptual perspective: variable identity and classification.

    Answers the fundamental question: "What IS this variable?". This perspective focuses on:
        - What category does it belong to? (INPUT, OUTPUT, CONTROL)
        - Which framework is it part of? (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM)
        - Is it relevant for the current analysis?
        - What dimensional framework does it use?

    Attributes:
        # From Foundation
            _name (str): User-friendly name of the variable.
            description (str): Brief summary of the variable.
            _idx (int): Index/precedence in the dimensional matrix.
            _sym (str): Symbol representation (LaTeX or alphanumeric).
            _alias (str): Python-compatible alias for use in code.
            _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).
        # From ConceptualSpecs
            _schema (Optional[Schema]): Reference to the dimensional framework schema.
            _cat (str): Category of the variable (INPUT, OUTPUT, CONTROL).
            relevant (bool): Flag indicating if variable is relevant for analysis.
    """

    # Private attributes
    # :attr: _schema
    _schema: Optional[Schema] = None
    """Reference to the dimensional framework schema."""

    # Category attribute (INPUT, OUT, CTRL)
    # :attr: _cat
    _cat: str = VarCardinality.IN.value
    """Category of the variable (INPUT, OUT, CTRL)."""

    # Flags
    # :attr: relevant
    relevant: bool = False
    """Flag indicating if variable is relevant for analysis."""

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the conceptual properties.

        Sets up the schema reference based on framework if not explicitly provided.

        Raises:
            ValueError: If framework configuration is invalid.
        """
        # Initialize from base class
        super().__post_init__()

        # If no schema provided, create default or use global
        if self._schema is None and self._fwk != Frameworks.CUSTOM.value:
            self._schema = Schema(_fwk=self._fwk)

    def _validate_in_list(self, value: str, prec_lt: List[str]) -> bool:
        """*_validate_in_list()* Validates if a value exists in a list of allowed values.

        Args:
            value (str): Value to validate.
            prec_lt (List[str]): List of allowed values.

        Returns:
            bool: True if the value is in the list, False otherwise.
        """
        if value in [None, ""]:
            return False
        return value in prec_lt

    # Property getters and setters
    # Identification and Classification

    @property
    def cat(self) -> str:
        """*cat* Get the category of the variable.

        Returns:
            str: Category (INPUT, OUT, CTRL).
        """
        return self._cat

    @cat.setter
    @validate_choices(PYDASA_CFG.parameter_cardinality)
    def cat(self, val: str) -> None:
        """*cat* Set the category of the variable.

        Args:
            val (str): Category (INPUT, OUT, CTRL).

        Raises:
            ValueError: If category is invalid.
        """
        # if val.upper() not in PYDASA_CFG.parameter_cardinality:
        #     _msg = f"Invalid category: {val}. "
        #     _msg += "Category must be one of the following: "
        #     _msg += f"{', '.join(_param_keys)}."
        #     raise ValueError(_msg)
        self._cat = val.upper()

    @property
    def schema(self) -> Optional[Schema]:
        """*schema* Get the dimensional schema reference.

        Returns:
            Optional[Schema]: The dimensional framework schema.
        """
        return self._schema

    @schema.setter
    def schema(self, val: Optional[Schema]) -> None:
        """*schema* Set the dimensional schema reference.

        Args:
            val (Optional[Schema]): The dimensional framework schema.
        """
        self._schema = val

    def clear(self) -> None:
        """*clear()* Reset conceptual attributes to default values.

        Resets category, schema, and relevance flag.
        """
        # Reset base class attributes
        super().clear()

        # Reset variable-specific attributes
        self._cat = VarCardinality.IN.value
        self._schema = None
        self.relevant = False
