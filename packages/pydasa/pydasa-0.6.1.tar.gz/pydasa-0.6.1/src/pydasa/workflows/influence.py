# -*- coding: utf-8 -*-
"""
Module influence.py
===========================================

Module for **SensitivityAnalysis** to manage sensitivity analysis in *PyDASA*

This module provides the SensitivityAnalysis class for coordinating multiple sensitivity analyses and generating reports on which variables have the most significant impact on dimensionless coefficients.

Classes:
    **SensitivityAnalysis**: Manages sensitivity analyses for multiple coefficients, processes results, and generates reports on variable impacts.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, cast

# Import validation base classes
from pydasa.core.basic import Foundation
from pydasa.workflows.basic import WorkflowBase

# Import related classes
from pydasa.analysis.scenario import Sensitivity

# Import utils
from pydasa.serialization.parser import latex_to_python

# Import validation decorators
from pydasa.validations.decorators import validate_choices
# Import global configuration
from pydasa.core.setup import AnaliticMode
from pydasa.core.setup import PYDASA_CFG
# from pydasa.validations.patterns import LATEX_RE


@dataclass
class SensitivityAnalysis(Foundation, WorkflowBase):
    """**SensitivityAnalysis** class for managing multiple sensitivity analyses in *PyDASA*.

    Coordinates sensitivity analyses for multiple coefficients, processes their results, and generates comprehensive reports on variable impacts.

    Args:
        Foundation (Foundation): Inherits common validation logic.
        WorkflowBase (WorkflowBase): Inherits workflow basic functionalities.

    Attributes:
        # From Foundation (Identification and Classification):
            name (str): User-friendly name of the sensitivity analysis.
            description (str): Brief summary of the sensitivity analysis.
            _idx (int): Index/precedence of the sensitivity analysis.
            _sym (str): Symbol representation (LaTeX or alphanumeric).
            _alias (str): Python-compatible alias for use in code.
            _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).

        # From WorkflowBase (Common Workflow Components):
            _variables (Dict[str, Variable]): All available parameters/variables in the model (*Variable*). Accepts Variable instances or dicts.
            _schema (Optional[Schema]): Dimensional framework schema for the workflow. After __post_init__, this will always be a Schema instance.
            _coefficients (Dict[str, Coefficient]): All available coefficients in the model (*Coefficient*). Accepts Coefficient instances or dicts.
            _results (Dict[str, Dict[str, Any]]): Consolidated results from sensitivity analyses.
            _is_solved (bool): Flag indicating if the sensitivity analysis workflow has been completed.

        # Specific to SensitivityAnalysis:
            _cat (str): Category of sensitivity analysis (SYM, NUM, HYB).
            _analyses (Dict[str, Sensitivity]): All sensitivity analyses performed for each coefficient.
    """

    # ========================================================================
    # SensitivityAnalysis Specific Attributes
    # ========================================================================

    # Category attribute
    # :attr: _cat
    _cat: str = AnaliticMode.SYM.value
    """Category of sensitivity analysis workflow (SYM, NUM)."""

    # Analysis results
    # :attr: _analyses
    _analyses: Dict[str, Sensitivity] = field(default_factory=dict)
    """Dictionary of sensitivity analyses performed in the workflow."""

    def __post_init__(self) -> None:
        """*__post_init__()* Post-initialization processing with validation and setup.

        Validates basic properties and sets up component maps for the sensitivity analysis.
        """
        # Initialize from base class
        super().__post_init__()

        # Set default symbol if not specified
        if not self._sym:
            self._sym = f"SANSYS_{{\\Pi_{{{self._idx}}}}}" if self._idx >= 0 else "SANSYS_\\Pi_{-1}"

        if not self._alias:
            self._alias = latex_to_python(self._sym)

        # Set name and description if not already set
        if not self.name:
            self.name = f"Sensitivity Analysis {self._idx}"

        if not self.description:
            self.description = "Manages sensitivity analyses for coefficients."

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _create_analyses(self) -> None:
        """*_create_analyses()* Creates sensitivity analyses for each coefficient.

        Sets up Sensitivity objects for each coefficient to be analyzed.
        """
        self._analyses.clear()

        for i, (pi, coef) in enumerate(self._coefficients.items()):
            # Create sensitivity analysis
            analysis = Sensitivity(
                _idx=i,
                _sym=f"SEN_{{{coef.sym}}}",
                _fwk=self._fwk,
                _cat=self._cat,
                _name=f"Sensitivity for {coef.name}",
                description=f"Sensitivity analysis for {coef.sym}",
                # _pi_expr=coef._pi_expr
            )

            # Configure with coefficient
            analysis.set_coefficient(coef)

            # Add to list
            self._analyses[pi] = analysis

    def _get_variable_value(self,
                            var_sym: str,
                            val_type: str = "mean") -> float:
        """*_get_variable_value()* Gets a value for a variable based on value type.

        Args:
            var_sym (str): Symbol of the variable.
            val_type (str, optional): Type of value to return (mean, min, max). Defaults to "mean".

        Returns:
            float: Variable value.

        Raises:
            ValueError: If the variable is not found.
            ValueError: If the value type is invalid.
        """
        # Check if the variable symbol exists in our variable map
        if var_sym not in self._variables:
            _msg = f"Variable '{var_sym}' not found in variables."
            _msg += f" Available variables: {list(self._variables.keys())}"
            raise ValueError(_msg)

        # Get the Variable object from the map
        var = self._variables[var_sym]

        # CASE 1: Return average value
        if val_type == "mean":
            # First check if standardized average exists
            if var.std_mean is None:
                # If no standardized average, try regular average
                # If thats also None, use default value -1.0
                return var.mean if var.mean is not None else -1.0
            # Return standardized average if it exists
            return var.std_mean

        # CASE 2: Return minimum value
        elif val_type == "min":
            # First check if standardized minimum exists
            if var.std_min is None:
                # If no standardized minimum, try regular minimum
                # If thats also None, use default value -0.1
                return var.min if var.min is not None else -0.1
            # Return standardized minimum if it exists
            return var.std_min

        # CASE 3: Return maximum value
        elif val_type == "max":
            # First check if standardized maximum exists
            if var.std_max is None:
                # If no standardized maximum, try regular maximum
                # If thats also None, use default value -10.0
                return var.max if var.max is not None else -10.0
            # Return standardized maximum if it exists
            return var.std_max

        # CASE 4: Invalid value type
        else:
            # Build error message
            _msg = f"Invalid value type: {val_type}. "
            _msg += "Must be one of: mean, min, max."
            raise ValueError(_msg)

    # ========================================================================
    # Workflow Methods
    # ========================================================================

    def analyze_symbolic(self,
                         val_type: str = "mean") -> Dict[str, Dict[str, float]]:
        """*analyze_symbolic()* Performs symbolic sensitivity analysis.

        Analyzes each coefficient using symbolic differentiation at specified values.

        Args:
            val_type (str, optional): Type of value to use (mean, min, max). Defaults to "mean".

        Returns:
            Dict[str, Dict[str, float]]: Sensitivity results by coefficient and variable.
        """
        # Create analyses if not already done
        if not self._analyses:
            self._create_analyses()

        # Clear previous results
        self._results.clear()

        # Process each analysis
        for analysis in self._analyses.values():
            # Get variable values
            values = {}
            for var_sym in analysis._latex_to_py.keys():
                # Ensure symbol is a string
                values[var_sym] = self._get_variable_value(var_sym, val_type)
            # Perform analysis
            result = analysis.analyze_symbolically(values)

            # Store results
            self._results[analysis.sym] = result

        # Mark workflow as solved
        self._is_solved = True
        return self._results

    def analyze_numeric(self,
                        n_samples: int = 1000) -> Dict[str, Dict[str, Any]]:
        """*analyze_numeric()* Performs numerical sensitivity analysis.

        Analyzes each coefficient using Fourier Amplitude Sensitivity Test (FAST).

        Args:
            n_samples (int, optional): Number of samples to use. Defaults to 1000.

        Returns:
            Dict[str, Dict[str, Any]]: Sensitivity results by coefficient.
        """
        # Create analyses if not already done
        if not self._analyses:
            self._create_analyses()

        # Clear previous results
        self._results.clear()

        # Process each analysis
        for analysis in self._analyses.values():
            # Get variable bounds
            vals = []
            bounds = []
            for var_sym in analysis._latex_to_py.keys():
                var = self._variables[var_sym]
                min_val = var.std_min if var.std_min is not None else (var.min if var.min is not None else -0.1)
                max_val = var.std_max if var.std_max is not None else (var.max if var.max is not None else -10.0)
                bounds.append([min_val, max_val])
                vals.append(var.sym)

            # Perform analysis
            result = analysis.analyze_numerically(vals, bounds, n_samples)

            # Store results
            self._results[analysis.sym] = result

        # Mark workflow as solved
        self._is_solved = True
        return self._results

    # ========================================================================
    # Property Getters and Setters
    # ========================================================================

    @property
    def cat(self) -> str:
        """*cat* Get the analysis category.

        Returns:
            str: Category (SYM, NUM, HYB).
        """
        return self._cat

    @cat.setter
    @validate_choices(PYDASA_CFG.analitic_modes, case_sensitive=False)
    def cat(self, val: str) -> None:
        """*cat* Set the analysis category.

        Args:
            val (str): Category value.

        Raises:
            ValueError: If category is invalid.
        """
        self._cat = val.upper()

    @property
    def analyses(self) -> Dict[str, Sensitivity]:
        """*analyses* Get the dictionary of sensitivity analyses.

        Returns:
            Dict[str, Sensitivity]: Dictionary of sensitivity analyses.
        """
        return self._analyses.copy()

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def reset(self) -> None:
        """*reset()* Reset the analysis state while preserving input configuration.

        Clears coefficients, results, analyses, and solved state while keeping variables and schema.
        """
        # Clear SensitivityAnalysis specific attributes
        self._analyses.clear()

        # Handles coefficients, results, is_solved from WorkflowBase
        super().reset()

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values.

        Resets all analysis properties to their initial state, including variables, coefficients, and results from WorkflowBase.
        """
        # Reset SensitivityAnalysis specific attributes first
        self._cat = AnaliticMode.SYM.value
        self._analyses = {}

        # Call both parent classes' clear methods explicitly for multiple inheritance
        Foundation.clear(self)
        WorkflowBase.clear(self)

        # Reset symbol after parent clears
        self._sym = f"SANSYS_{{\\Pi_{{{self._idx}}}}}"

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert sensitivity analysis to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of sensitivity analysis.
        """
        # Get base serialization from WorkflowBase
        result = super().to_dict()

        # Add SensitivityAnalysis specific attributes
        result["cat"] = self._cat

        # Skip analyses - they are transient and recreated as needed
        # (no need to serialize _analyses)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SensitivityAnalysis:
        """*from_dict()* Create sensitivity analysis from dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary representation of sensitivity analysis.

        Returns:
            SensitivityAnalysis: New sensitivity analysis instance.
        """
        # Use parent class to handle base deserialization
        instance = cast(SensitivityAnalysis, super().from_dict(data))

        # Handle SensitivityAnalysis specific attributes
        if "cat" in data:
            instance._cat = data["cat"]

        # Note: _analyses is not deserialized as it's transient and recreated as needed
        return instance
