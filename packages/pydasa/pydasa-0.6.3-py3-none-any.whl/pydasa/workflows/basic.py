# -*- coding: utf-8 -*-
"""
Module base.py
===========================================

Base class for common attributes and methods shared across all workflow **PyDASA** workflow management.

Classes:
    **WorkflowBase**: Base class for all workflow orchestrators with common analysis components and validation methods.
"""

from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Dict, Any, Union, List, Optional


# Import related classes
from pydasa.elements.parameter import Variable
from pydasa.dimensional.buckingham import Coefficient
from pydasa.dimensional.vaschy import Schema
from pydasa.dimensional.fundamental import Dimension

# Import validation decorators
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_emptiness
from pydasa.validations.decorators import validate_dict_types
# from pydasa.validations.decorators import validate_choices

# Import global configuration
from pydasa.core.setup import Frameworks
# from pydasa.core.setup import PYDASA_CFG

# Custom type hinting for workflow inputs
Variables = Union[Dict[str, Variable], Dict[str, Any]]
"""Type hint for variables input: accepts Variable instances or dicts."""

Coefficients = Union[Dict[str, Coefficient], Dict[str, Any]]
"""Type hint for coefficients input: accepts Coefficient instances or dicts."""

FDUs = Union[str, Dict[str, Any], List[Dict], Schema]
"""Type hint for schema input: accepts framework strings, Schema objects, or FDU definitions."""


@dataclass
class WorkflowBase:
    """**WorkflowBase** Base class for PyDASA workflow orchestrators. Provides common attributes and validation methods shared across:
        - **AnalysisEngine**: Dimensional analysis workflow (phenomena.py)
        - **SensitivityAnalysis**: Sensitivity analysis workflow (influence.py)
        - **MonteCarloSimulation**: Monte Carlo experiments workflow (practical.py)

    Attributes:
        _variables (Dict[str, Variable]): All variables in the model.
        _schema (Optional[Schema]): Dimensional framework schema.
        _coefficients (Dict[str, Coefficient]): All coefficients in the model.
        _results (Dict[str, Dict[str, Any]]): Consolidated results from workflow.
        _is_solved (bool): Flag indicating if the workflow has been solved.
    """

    # Common workflow components
    # :attr: _variables
    _variables: Dict[str, Variable] = field(default_factory=dict)
    """All variables in the workflow."""

    # :attr: _schema
    _schema: Optional[Schema] = None
    """Dimensional framework schema for the workflow. After __post_init__, this will always be a Schema instance.
    """

    # Dimensional Analysis components
    # :attr: _coefficients
    _coefficients: Dict[str, Coefficient] = field(default_factory=dict)
    """Generated coefficients in the workflow."""

    # Common result components
    # :attr: _results
    _results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Consolidated results from workflow."""

    # Workflow state
    # :attr: _is_solved
    _is_solved: bool = False
    """Flag indicating if the workflow has been solved."""

    def __post_init__(self) -> None:
        pass  # Placeholder for potential future initialization logic

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _convert_to_objects(self,
                            data: Dict[str, Any],
                            tgt_cls: type) -> Dict[str, Any]:
        """*_convert_to_objects()* Converts dictionary values to target class instances (Variable or Coefficient). Accepts either existing instances or dicts to convert.

        Args:
            data (Dict[str, Any]): Input dictionary with values to convert.
            tgt_cls (type): Target class to convert values to (Variable or Coefficient).

        Raises:
            ValueError: If any value is neither the target class nor a dict.

        Returns:
            Dict[str, Any]: Dictionary with values converted to target class instances.
        """
        # Convert dict values to Variable/Coefficient objects if needed
        ans = dict()
        for key, val in data.items():
            # if value is already the target class, keep it
            if isinstance(val, tgt_cls):
                ans[key] = val
            # if value is a dict, convert to target class
            elif isinstance(val, dict):
                ans[key] = tgt_cls.from_dict(val)
            # otherwise, raise error
            else:
                _msg = f"Value for '{key}' must be "
                _msg += f"{tgt_cls.__name__} instance or dict. "
                _msg += f"Got: {type(val).__name__}"
                raise ValueError(_msg)
        # return proper dict
        return ans

    def _convert_to_schema(self, val: FDUs) -> Schema:
        """*_convert_to_schema()* Converts various schema input formats to a Schema instance. Accepts:
            - str: Framework name (e.g., "PHYSICAL"), load known schema
            - Schema: Direct Schema instance
            - Dict: Complete Schema dict or single FDU definition
            - List[Dict]: Multiple FDU definitions for CUSTOM framework

        Args:
            val (FDUs): Schema in various formats.

        Raises:
            TypeError: If val is not a valid type.
            TypeError: If list items are not dicts.

        Returns:
            Schema: Converted Schema instance.
        """
        # Already a Schema object
        if isinstance(val, Schema):
            return val

        # Framework name string
        elif isinstance(val, str):
            return Schema(_fwk=val.upper(), _idx=0)

        # List of FDU definitions - create CUSTOM schema
        elif isinstance(val, list):
            if not all(isinstance(item, dict) for item in val):
                _msg = "When schema is a list, all items must be dicts with FDU definitions."
                raise TypeError(_msg)

            _fdus = []
            for d in val:
                if isinstance(d, dict):
                    _fdus.append(Dimension(**d))
                else:
                    _fdus.append(d)

            return Schema(_fwk=Frameworks.CUSTOM.value, _fdu_lt=_fdus, _idx=0)

        # if schema is a dict, convert to Schema
        elif isinstance(val, dict):
            # Check if it's a complete Schema dict (has framework info)
            if "fwk" in val or "_fwk" in val:
                return Schema.from_dict(val)
            else:
                # Single FDU definition - treat as CUSTOM with one dimension
                _fdus = [Dimension(**val)]
                return Schema(_fwk=Frameworks.CUSTOM.value, _fdu_lt=_fdus)

        else:
            _msg = "Schema input must be 'str', 'dict', 'list', or 'Schema' object. "
            _msg += f"Got: {type(val).__name__}"
            raise TypeError(_msg)

    # ========================================================================
    # Property Getters and Setters
    # ========================================================================

    @property
    def variables(self) -> Dict[str, Variable]:
        """*variables* Get the variable dictionary.

        Returns:
            Dict[str, Variable]: Copy of variables dictionary.
        """
        return self._variables.copy()

    @variables.setter
    @validate_type(dict, Variable, allow_none=False)
    @validate_emptiness()
    @validate_dict_types(str, (Variable, dict))
    def variables(self, val: Variables) -> None:
        """*variables* Set the variable dictionary, accepting both Variable objects and dictionaries (converted automatically).

        Args:
            val (Variables): Dictionary of variables (Variable instances or dicts).
        """
        # convert dict values to Variable objects if needed
        self._variables = self._convert_to_objects(val, Variable)
        self._is_solved = False  # Reset solve state

    @property
    def schema(self) -> Optional[Schema]:
        """*schema* Get the dimensional framework schema.

        Returns:
            Optional[Schema]: Schema instance or None.
        """
        return self._schema

    @schema.setter
    @validate_type(str, dict, list, Schema, allow_none=False)
    def schema(self, val: FDUs) -> None:
        """*schema* Set the dimensional framework schema, accepting multiple formats:
            - str: Framework name (e.g., "PHYSICAL")
            - Schema: Direct Schema instance
            - Dict: Complete Schema dict or single FDU definition
            - List[Dict]: Multiple FDU definitions for CUSTOM framework

        Args:
            val (FDUs): Schema in various formats:
        """
        self._schema = self._convert_to_schema(val)
        self._is_solved = False  # Reset solve state

    @property
    def coefficients(self) -> Dict[str, Coefficient]:
        """*coefficients* Get the coefficient dictionary.

        Returns:
            Dict[str, Coefficient]: Copy of coefficients dictionary.
        """
        return self._coefficients.copy()

    @coefficients.setter
    @validate_type(dict, allow_none=False)
    @validate_emptiness()
    @validate_dict_types(str, (Coefficient, dict))
    def coefficients(self, val: Coefficients) -> None:
        """*coefficients* Set the coefficient dictionary, accepting both Coefficient objects and dictionaries (converted automatically).

        Args:
            val (Coefficients): Dictionary of coefficients (Coefficient instances or dicts).
        """
        # Convert dict values to Coefficient objects if needed
        self._coefficients = self._convert_to_objects(val, Coefficient)
        self._is_solved = False  # Reset solve state

    @property
    def results(self) -> Dict[str, Dict[str, Any]]:
        """*results* Get the result dictionary in the workflow.

        Returns:
            Dict[str, Dict[str, Any]]: Copy of results dictionary.
        """
        return self._results.copy()

    @property
    def is_solved(self) -> bool:
        """*is_solved* Check if the workflow is finished.

        Returns:
            bool: True if solved, False otherwise.
        """
        return self._is_solved

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def reset(self) -> None:
        """*reset* Reset the workflow state while preserving input configuration. Clears coefficients, results, and solved state.
        """
        self._coefficients.clear()
        self._results.clear()
        self._is_solved = False

    def clear(self) -> None:
        """*clear()* Clear all workflow attributes, including variables, coefficients, results, and solved state.
        """
        self._variables.clear()
        self._coefficients.clear()
        self._results.clear()
        self._is_solved = False
        # NOTE: _schema is intentionally not cleared as it's framework-specific

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert the workflow instance to a dictionary representation, handling nested Schema, Variable, and Coefficient objects.

        Returns:
            Dict[str, Any]: Dictionary representation of the workflow.
        """
        result = {}

        # Get all dataclass fields
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, attr_name)

            # Handle Schema object
            if isinstance(attr_value, Schema):
                attr_value = attr_value.to_dict()
            # Handle dictionaries with Variable or Coefficient values
            elif isinstance(attr_value, dict) and attr_value:
                first_val = next(iter(attr_value.values()), None)
                if isinstance(first_val, (Variable, Coefficient)):
                    attr_value = {k: v.to_dict() for k, v in attr_value.items()}

            # Skip callables (can't be serialized)
            if callable(attr_value) and not isinstance(attr_value, type):
                continue

            # Remove leading underscore from private attributes
            clean_name = attr_name[1:] if attr_name.startswith("_") else attr_name
            result[clean_name] = attr_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowBase:
        """*from_dict()* Create workflow instance from dictionary representation, converting dicts back to Variable, Coefficient, and Schema objects as needed.

        Args:
            data (Dict[str, Any]): Dictionary representation of the workflow.

        Returns:
            WorkflowBase: Workflow instance created from the dictionary.
        """
        # Get all field names from the dataclass
        field_names = {f.name for f in fields(cls)}

        # Map keys without underscores to keys with underscores
        mapped_data = {}

        for key, value in data.items():
            # Try with underscore prefix if key not in fields
            if key in field_names:
                mapped_data[key] = value
            elif f"_{key}" in field_names:
                mapped_data[f"_{key}"] = value

        # Create instance with basic fields
        obj = cls(**mapped_data)

        # Reconstruct schema if present
        if "schema" in data and data["schema"] is not None:
            schema_data = data["schema"]
            if isinstance(schema_data, dict):
                obj._schema = Schema.from_dict(schema_data)
            elif isinstance(schema_data, Schema):
                obj._schema = schema_data

        # Reconstruct variables directly from dict
        if "variables" in data and isinstance(data["variables"], dict):
            obj._variables = {}
            for k, v in data["variables"].items():
                if isinstance(v, dict):
                    obj._variables[k] = Variable.from_dict(v)
                else:
                    obj._variables[k] = v

        # Reconstruct coefficients directly from dict
        if "coefficients" in data and isinstance(data["coefficients"], dict):
            obj._coefficients = {}
            for k, v in data["coefficients"].items():
                if isinstance(v, dict):
                    obj._coefficients[k] = Coefficient.from_dict(v)
                else:
                    obj._coefficients[k] = v

        return obj
