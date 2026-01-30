# -*- coding: utf-8 -*-
"""
Module statistical.py
===========================================

Statistical perspective for variable representation.

This module defines the StatisticalSpecs class representing the probabilistic
distribution and sampling properties of a variable.

Classes:
    **StatisticalSpecs**: Statistical variable specifications

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, List, TYPE_CHECKING


@dataclass
class StatisticalSpecs:
    """Statistical perspective: probabilistic distributions. Answers the question: "How do we MODEL uncertainty?"

    This perspective focuses on:
        - Probability distribution types (uniform, normal, beta, custom)
        - Distribution parameters
        - Random sampling mechanisms
        - Monte Carlo simulation support
        - Uncertainty quantification
    """

    # Type annotation for sym attribute (defined in Foundation, accessed via composition)
    if TYPE_CHECKING:
        _sym: str

    # distribution specifications
    # :attr: _dist_type
    _dist_type: str = "uniform"
    """Type of distribution (e.g., 'uniform', 'normal'). By default is 'uniform'."""

    # :attr: _dist_params
    _dist_params: Optional[Dict[str, Any]] = field(default_factory=dict)
    """Parameters for the distribution (e.g., {'min': 0, 'max': 1} for uniform)."""

    # :attr: _depends
    _depends: List[str] = field(default_factory=list)
    """List of variable names that this variable depends on. (e.g., for calculated variables like F = m*a)."""

    # :attr: _dist_func
    _dist_func: Optional[Callable[..., float]] = None
    """Callable representing the distribution function defined externally by the user."""

    def sample(self, *args) -> float:
        """*sample()* Generate a random sample.

        Args:
            *args: Additional arguments for the distribution function.

        Returns:
            float: Random sample from distribution.

        Raises:
            ValueError: If no distribution has been set.
        """
        if self._dist_func is None:
            _msg = f"No distribution set for variable '{self._sym}'. "
            _msg += "Call set_function() first."
            raise ValueError(_msg)

        # if kwargs are provided, pass them to the function parameters
        elif len(args) > 0:
            return self._dist_func(*args)

        # otherwise, execute without them
        return self._dist_func()

    def has_function(self) -> bool:
        """*has_function()* Check if distribution is set.

        Returns:
            bool: True if distribution is configured.
        """
        return self._dist_func is not None

    @property
    def dist_type(self) -> str:
        """*dist_type* Get the distribution type.

        Returns:
            str: Distribution type (e.g., 'uniform', 'normal').
        """
        return self._dist_type

    @dist_type.setter
    def dist_type(self, val: str) -> None:
        """*dist_type* Set the distribution type.

        Args:
            val (str): Distribution type.

        Raises:
            ValueError: If distribution type is not supported.
        """
        # TODO improve this for later
        supported_types = [
            "uniform",
            "normal",
            "triangular",
            "exponential",
            "lognormal",
            "custom",
        ]
        if val not in supported_types:
            _msg = f"Unsupported distribution type: {val}. "
            _msg += f"Supported types: {', '.join(supported_types)}"
            raise ValueError(_msg)
        self._dist_type = val

    @property
    def dist_params(self) -> Optional[Dict[str, Any]]:
        """*dist_params* Get the distribution parameters.

        Returns:
            Optional[Dict[str, Any]: Distribution parameters.
        """
        return self._dist_params

    @dist_params.setter
    def dist_params(self, val: Optional[Dict[str, Any]]) -> None:
        """*dist_params* Set the distribution parameters.

        Args:
            val (Optional[Dict[str, Any]): Distribution parameters.

        Raises:
            ValueError: If parameters are invalid for the distribution type.
        """
        if val is None:
            self._dist_params = None
            return None
        # Validate parameters based on distribution type
        if self._dist_type == "uniform":
            if "min" not in val or "max" not in val:
                _msg = f"Invalid keys for: {self._dist_type}: {val}"
                _msg += f" {self._dist_type} needs 'min' and 'max' parameters."
                _msg += f" Provided keys are: {list(val.keys())}."
                raise ValueError(_msg)
            if val["min"] >= val["max"]:
                _msg = f"Invalid range for {self._dist_type}: {val}"
                _msg += f" {self._dist_type} needs 'min' to be less than 'max'."
                _msg += f" Provided: min={val['min']}, max={val['max']}."
                raise ValueError(_msg)
        elif self._dist_type == "normal":
            if "mean" not in val or "std" not in val:
                _msg = f"Invalid keys for: {self._dist_type}: {val}"
                _msg += f" {self._dist_type} needs 'mean' and 'std' parameters."
                _msg += f" Provided keys are: {list(val.keys())}."
                raise ValueError(_msg)
            if val["std"] < 0:
                _msg = f"Invalid value for: {self._dist_type}: {val}"
                _msg += f" {self._dist_type} requires 'std' to be positive."
                _msg += f" Provided: std={val['std']}."
                raise ValueError(_msg)
        self._dist_params = val

    @property
    def dist_func(self) -> Optional[Callable[..., float]]:
        """*dist_func* Get the distribution function.

        Returns:
            Optional[Callable]: Distribution function.
        """
        return self._dist_func

    @dist_func.setter
    def dist_func(self, val: Optional[Callable[..., float]]) -> None:
        """*dist_func* Set the distribution function.

        Args:
            val (Optional[Callable]): Distribution function.

        Raises:
            TypeError: If value is not callable when provided.
        """
        if val is not None and not callable(val):
            _msg = f"Distribution function must be callable, got {type(val)}"
            raise TypeError(_msg)
        self._dist_func = val

    @property
    def depends(self) -> List[str]:
        """*depends* Get the list of variable dependencies.

        Returns:
            List[str]: List of variable names that this variable depends on.
        """
        return self._depends

    @depends.setter
    def depends(self, val: List[str]) -> None:
        """*depends* Set the list of variable dependencies.

        Args:
            val (List[str]): List of variable names that this variable depends on.
        Raises:
            ValueError: If value is not a list of strings.
        """
        if not isinstance(val, list):
            _msg = f"{val} must be a list of strings."
            _msg += f" type {type(val)} found instead."
            raise ValueError(_msg)
        if not all(isinstance(v, str) for v in val):
            _msg = f"{val} must be a list of strings."
            _msg += f" Found types: {[type(v) for v in val]}."
            raise ValueError(_msg)
        self._depends = val

    def clear(self) -> None:
        """*clear()* Reset statistical attributes to default values.

        Resets distribution type, parameters, and function.
        """
        self._dist_type = "uniform"
        self._dist_params = {}
        self._dist_func = None
