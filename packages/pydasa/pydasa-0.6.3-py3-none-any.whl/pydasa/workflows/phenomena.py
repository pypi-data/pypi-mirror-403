# -*- coding: utf-8 -*-
"""
Module phenomena.py
===========================================

Module for **AnalysisEngine** to orchestrate dimensional analysis workflows in *PyDASA*.

This module provides the **AnalysisEngine** class serves as the main entry point and workflow for *PyDASA's* dimensional analysis capabilities setting up the dimensional domain, solving the dimensional matrix, and generate coefficients.

Classes:
    **AnalysisEngine**: Main workflow class for dimensional analysis and coefficient generation.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, cast

# Import validation base classes
from pydasa.core.basic import Foundation
from pydasa.workflows.basic import WorkflowBase

# Import related classes
# from pydasa.elements.parameter import Variable
from pydasa.dimensional.buckingham import Coefficient
from pydasa.dimensional.model import Matrix
from pydasa.dimensional.vaschy import Schema

# Import utils
from pydasa.serialization.parser import latex_to_python

# Import validation decorators
from pydasa.validations.decorators import validate_type

# Import global configuration
from pydasa.core.setup import Frameworks   # , PYDASA_CFG


@dataclass
class AnalysisEngine(Foundation, WorkflowBase):
    """**AnalysisEngine** class for orchestrating dimensional analysis workflows in *PyDASA*.

    Main entry point to solve the dimensional matrix and generate the dimensionless coefficients.

    Args:
        Foundation (Foundation): Inherits common validation logic.
        WorkflowBase (WorkflowBase): Inherits workflow basic functionalities.

    Attributes:
        # From Foundation:
            _name (str): User-friendly name of the problem.
            description (str): Brief summary of the problem.
            _idx (int): Index/precedence of the problem.
            _sym (str): Symbol representation (LaTeX or alphanumeric).
            _alias (str): Python-compatible alias for use in code.
            _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).

        # From Workflows:
            _variables (Dict[str, Variable]): All variables in the model.
            _schema (Optional[Schema]): Dimensional framework schema.
            _coefficients (Dict[str, Coefficient]): All coefficients in the model.
            _results (Dict[str, Dict[str, Any]]): Consolidated results from workflow.
            _is_solved (bool): Flag indicating if the workflow has been solved.

        # For the Analysis Engine:
            _model (Optional[Matrix]): Dimensional matrix for analysis.
    """

    # ========================================================================
    # Dimensional Analysis Specific Attributes
    # ========================================================================

    # :attr: _model
    _model: Optional[Matrix] = field(default=None, init=True)
    """Dimensional matrix for Buckingham Pi analysis."""

    def __post_init__(self) -> None:
        """*__post_init__()* Post-initialization processing with validation and setup.

        Raises:
            ValueError: If framework is not supported.
            TypeError: If schema is of incorrect type.
            TypeError: If schema list items are not dictionaries.
        """
        # TODO check this after refector
        # Initialize from base class
        super().__post_init__()

        # Set default symbol if not specified
        if not self._sym:
            self._sym = f"DA_{{\\Pi_{{{self._idx}}}}}" if self._idx >= 0 else "DA_{\\Pi_{-1}}"

        if not self._alias:
            self._alias = latex_to_python(self._sym)

        # Set name and description if not already set
        if not self.name:
            self.name = f"Dimensional Analysis {self._idx}"

        if not self.description:
            self.description = "Dimensional analysis model using the Buckingham Pi-Theorem."

        # Initialize schema based on provided input and framework
        if self._schema is None:
            # No schema provided - create default based on framework
            if self.fwk == Frameworks.CUSTOM.value:
                _msg = "Custom framework requires '_schema' parameter with FDU definitions (List[Dict] or Dict)"
                raise ValueError(_msg)
            else:
                # Create schema for standard framework (PHYSICAL, COMPUTATION, SOFTWARE)
                self._schema = Schema(_fwk=self.fwk)
        else:
            # Use WorkflowBase helper to convert schema from various formats
            self._schema = self._convert_to_schema(self._schema)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    # ========================================================================
    # Property Getters and Setters
    # ========================================================================

    @property
    def matrix(self) -> Optional[Matrix]:
        """*matrix* Get the dimensional matrix.

        Returns:
            Optional[Matrix]: Dimensional matrix.
        """
        return self._model

    @matrix.setter
    @validate_type(Matrix, allow_none=True)
    def matrix(self, val: Optional[Matrix]) -> None:
        """*matrix* Set the dimensional matrix.

        Args:
            val (Optional[Matrix]): Dimensional matrix.
        """
        self._model = val
        if val is not None:
            self._is_solved = False  # Reset solve state

    # ========================================================================
    # Workflow Methods
    # ========================================================================

    def create_matrix(self, **kwargs) -> None:
        """*create_matrix()* Create and configure dimensional matrix for the model.

        Args:
            **kwargs: Optional keyword arguments to pass to Matrix constructor.

        Returns:
            Matrix: Configured dimensional matrix.

        Raises:
            ValueError: If variables are not set.
            TypeError: If schema is not set.
        """
        if not self._variables:
            raise ValueError("Variables must be set before creating matrix.")

        # After __post_init__, _schema is guaranteed to be a Schema instance
        if not isinstance(self._schema, Schema):
            raise TypeError("Schema must be set before creating matrix.")

        # Create matrix with variables
        self._model = Matrix(_idx=self.idx,
                             _fwk=self._fwk,
                             _schema=self._schema,
                             _variables=self._variables,)

        self._is_solved = False     # Reset solve state

    def solve(self) -> Dict[str, Coefficient]:
        """*solve()* Solve the dimensional matrix and generate coefficients.

        Performs dimensional analysis using the Buckingham Pi theorem to generate
        dimensionless coefficients.

        Returns:
            Dict[str, Coefficient]: Dictionary of generated coefficients.

        Raises:
            ValueError: If matrix is not created.
            RuntimeError: If solving fails.
        """
        if self._model is None:
            raise ValueError("Matrix must be created before solving. Call create_matrix() first.")

        try:
            # Solve the matrix (generate coefficients)
            self._model.create_matrix()
            self._model.solve_matrix()
            # self._model.solve()

            # Extract generated coefficients from matrix
            self._coefficients = self._model.coefficients
            self._is_solved = True
            return self._coefficients.copy()

        except Exception as e:
            _msg = f"Failed to solve dimensional matrix: {str(e)}"
            raise RuntimeError(_msg) from e

    def run_analysis(self) -> Dict[str, Any]:
        """*run_analysis()* Execute complete dimensional analysis workflow. Convenience method that runs the entire workflow: create matrix and solve.

        Returns:
            Dict[str, Any]: Dictionary of analysis results.
        """
        # Step 1: Create matrix if not already created
        if self._model is None:
            self.create_matrix()

        # Step 2: Solve and return coefficients
        # Create + Solve matrix
        coefficients = self.solve()
        results = {k: v.to_dict() for k, v in coefficients.items()}
        return results

    def derive_coefficient(self,
                           expr: str,
                           symbol: str = "",
                           name: str = "",
                           description: str = "",
                           idx: int = -1) -> Coefficient:
        """*derive_coefficient()* Derive a new coefficient from existing ones.

        Args:
            expr (str): LaTeX expression defining the new coefficient in terms of existing ones.
            symbol (str, optional): Symbol representation (LaTeX or alphanumeric) for the derived coefficient. Defaults to "" to keep the original (e.g., Pi_{0}).
            name (str, optional): User-friendly name for the derived coefficient. Defaults to "".
            description (str, optional): Description of the derived coefficient. Defaults to "".
            idx (int, optional): Index/precedence of the derived coefficient. Defaults to -1.

        Raises:
            ValueError: If matrix is not created.
            ValueError: If matrix is not solved.
            ValueError: If the expression for the derived coefficient is invalid.
            RuntimeError: If derivation fails.

        Returns:
            Coefficient: The newly derived coefficient.
        """

        if self._model is None:
            _msg = "Matrix must be created before deriving coefficients."
            _msg += " Call create_matrix() first."
            raise ValueError(_msg)

        if not self._is_solved:
            _msg = "Matrix must be solved before deriving coefficients."
            _msg += " Call solve() first."
            raise ValueError(_msg)

        try:
            # Delegate to the Matrix's derive_coefficient method
            coef = self._model.derive_coefficient(expr,
                                                  symbol,
                                                  name,
                                                  description,
                                                  idx)
            return coef
        except Exception as e:
            _msg = f"Failed to derive coefficient: {str(e)}"
            raise RuntimeError(_msg) from e

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def reset(self) -> None:
        """*reset()* Reset the solver state, all the results, KEEPING only the input variables.
        """
        # Handles coefficients, results, is_solved from WorkflowBase
        super().reset()
        self._model = None

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values.

        Clears all solver properties to their initial state, INCLUDING variables.
        """
        # Reset AnalysisEngine-specific attributes first
        self._model = None

        # Call both parent classes' clear methods explicitly for multiple inheritance
        Foundation.clear(self)
        WorkflowBase.clear(self)

        # Reset symbol and schema after parent clears
        self._sym = f"DA_{{\\Pi_{{{self._idx}}}}}"
        self._schema = Schema(_fwk=Frameworks.PHYSICAL.value)

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert solver state to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of solver state.
        """
        # Get base serialization from WorkflowBase
        result = super().to_dict()

        # Add Matrix-specific handling
        if self._model is not None:
            result["model"] = self._model.to_dict()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AnalysisEngine:
        """*from_dict()* Create a AnalysisEngine instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing the solver's state.

        Returns:
            AnalysisEngine: New instance of AnalysisEngine.
        """
        # Use parent class to handle base deserialization
        instance = cast(AnalysisEngine, super().from_dict(data))

        # Handle AnalysisEngine-specific Matrix reconstruction
        model_data = data.get("model", None)
        if model_data is not None and isinstance(model_data, dict):
            instance._model = Matrix.from_dict(model_data)

        return instance
