# -*- coding: utf-8 -*-
"""
Module practical.py
===========================================

Module for **MonteCarloSimulation** to manage the Monte Carlo experiments in *PyDASA*.

This module provides classes for managing Monte Carlo simulations of the dimensionless coefficients.

Classes:
    **MonteCarloSimulation**: Manages Monte Carlo simulation runs, including configuration and execution of the experiments.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, cast

# import random
# import re, Optional, Callable

# Third-party imports
import numpy as np
from numpy.typing import NDArray

# Import validation base classes
from pydasa.core.basic import Foundation
from pydasa.workflows.basic import WorkflowBase

# Import related classes
from pydasa.dimensional.buckingham import Coefficient
from pydasa.analysis.simulation import MonteCarlo

# Import utils
from pydasa.serialization.parser import latex_to_python

# Import validation decorators
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_range
from pydasa.validations.decorators import validate_choices

# Import global configuration
# from pydasa.core.parameter import Variable
# from pydasa.core.setup import Frameworks
from pydasa.core.setup import SimulationMode
# Import configuration
from pydasa.core.setup import PYDASA_CFG


@dataclass
class MonteCarloSimulation(Foundation, WorkflowBase):
    """**MonteCarloSimulation** class for managing Monte Carlo simulations in *PyDASA*.

    Manages the creation, configuration, and execution of Monte Carlo simulations of dimensionless coefficients.

    Args:
        Foundation (Foundation): Inherits common validation logic.
        WorkflowBase (WorkflowBase): Inherits workflow basic functionalities.

    Attributes:
        # From Foundation (Identification and Classification):
            _name (str): User-friendly name of the Monte Carlo simulation handler.
            description (str): Brief summary of the Monte Carlo simulation handler.
            _idx (int): Index/precedence of the simulation handler.
            _sym (str): Symbol representation (LaTeX or alphanumeric).
            _alias (str): Python-compatible alias for use in code.
            _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).

        # From WorkflowBase (Common Workflow Components):
            _variables (Dict[str, Variable]): All available parameters/variables in the model (*Variable*). Accepts Variable instances or dicts.
            _schema (Optional[Schema]): Dimensional framework schema for the workflow. After __post_init__, this will always be a Schema instance (inherited but not actively used in MonteCarloSimulation).
            _coefficients (Dict[str, Coefficient]): All available coefficients in the model (*Coefficient*). Accepts Coefficient instances or dicts.
            _results (Dict[str, Dict[str, Any]]): Consolidated results from Monte Carlo simulations.
            _is_solved (bool): Flag indicating if the simulation workflow has been completed.

        # Specific to MonteCarloSimulation:
            _cat (str): Category of simulation run (DIST, DATA).
            _distributions (Dict[str, Dict[str, Any]]): All distribution functions used in the simulations (specific name, parameters, and function).
            _experiments (int): Number of simulations to run. Default is -1.
            _simulations (Dict[str, MonteCarlo]): All Monte Carlo simulations performed for each coefficient.
            _shared_cache (Dict[str, NDArray[np.float64]]): In-memory cache for simulation data shared between coefficients.
    """

    # ========================================================================
    # MonteCarloSimulation Specific Attributes
    # ========================================================================

    # :attr: _cat
    _cat: str = SimulationMode.DIST.value
    """Category of simulation run (DIST, DATA)."""

    # Simulation configuration
    # :attr: _distributions
    _distributions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Variable sampling distributions and specifications for simulations (specific name, parameters, and function)."""

    # :attr: _experiments
    _experiments: int = -1
    """Number of simulation to run."""

    # Simulation Management
    # :attr: _shared_cache
    _shared_cache: Dict[str, NDArray[np.float64]] = field(default_factory=dict)
    """In-memory cache for simulation data between coefficients."""

    # :attr: _simulations
    _simulations: Dict[str, MonteCarlo] = field(default_factory=dict)
    """Dictionary of Monte Carlo simulations."""

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the Monte Carlo handler."""
        # Initialize from base class
        super().__post_init__()

        # Set default symbol if not specified
        if not self._sym:
            self._sym = f"MCS_{{\\Pi_{{{self._idx}}}}}" if self._idx >= 0 else "MCS_\\Pi_{-1}"

        if not self._alias:
            self._alias = latex_to_python(self._sym)

        # Set name and description if not already set
        if not self.name:
            self.name = f"Monte Carlo Simulation Handler {self._idx}"

        if not self.description:
            coef_keys = ", ".join(self._coefficients.keys()) if self._coefficients else "no coefficients"
            self.description = f"Manages Monte Carlo simulations for [{coef_keys}] coefficients."

        # Ensure mem_cache is always initialized
        if self._shared_cache is None:
            self._shared_cache = {}

    def configure_distributions(self) -> None:
        """*configure_distributions()* Configures sampling distributions for all variables. Sets up distribution specifications (type, parameters, functions) for each variable that will be used during Monte Carlo simulation.

        Raises:
            ValueError: If variables are not defined.
            ValueError: If distribution specifications are invalid.
        """
        if len(self._distributions) == 0:
            self._config_distributions()

    def configure_simulations(self) -> None:
        """*configure_simulations()* Configures Monte Carlo simulation objects for each coefficient. Creates MonteCarlo instances for each coefficient with appropriate distributions and dependencies. Requires distributions to be configured first.

        Raises:
            ValueError: If distributions are not configured.
            ValueError: If coefficients or variables are not defined.
        """
        if len(self._simulations) == 0:
            self._config_simulations()

    def create_simulations(self) -> None:
        """*create_simulations()* Configures distributions and simulations if not already set. This is a convenience method that orchestrates the full configuration process. It calls configure_distributions() and configure_simulations() in sequence.

        Raises:
            ValueError: If variables or coefficients are not defined.
            ValueError: If distribution specifications are invalid.
        """
        self.configure_distributions()
        self.configure_simulations()

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _validate_coefficient_vars(self,
                                   coef: Coefficient,
                                   pi_sym: str) -> Dict[str, Any]:
        """*_validate_coefficient_vars()* Validates and returns coefficient's var_dims.

        Args:
            coef (Coefficient): The coefficient to validate.
            pi_sym (str): The coefficient symbol for error messages.

        Returns:
            Dict[str, Any]: The validated var_dims dictionary.

        Raises:
            ValueError: If var_dims is None or missing.
        """
        if not hasattr(coef, 'var_dims'):
            _msg = f"Coefficient '{pi_sym}' missing var_dims attribute."
            raise ValueError(_msg)

        var_dims = coef.var_dims
        if var_dims is None:
            _msg = f"Coefficient '{pi_sym}' has None var_dims. "
            _msg += "Ensure the coefficient was properly initialized."
            raise ValueError(_msg)

        if not isinstance(var_dims, dict):
            _msg = f"Coefficient '{pi_sym}' var_dims must be a dictionary. "
            _msg += f"Got: {type(var_dims).__name__}"
            raise TypeError(_msg)

        return var_dims

    # ========================================================================
    # Configuration Methods
    # ========================================================================

    def _config_distributions(self) -> None:
        """*_config_distributions()* Creates the Monte Carlo distributions for each variable.

        Raises:
            ValueError: If the distribution specifications are invalid.
        """
        # Clear existing distributions
        self._distributions.clear()

        # Validate variables exist before processing
        if not self._variables:
            _msg = "Cannot configure distributions: no variables defined."
            raise ValueError(_msg)

        for var in self._variables.values():
            sym = var.sym

            # Skip if already configured
            if sym in self._distributions:
                continue

            # Collect specs for better error reporting
            specs = {
                "dist_type": var.dist_type,
                "dist_params": var.dist_params,
                "dist_func": var.dist_func
            }

            # Validate distribution specifications
            if not any(specs.values()):
                _msg = f"Invalid distribution for variable '{sym}'. "
                _msg += f"Incomplete specifications provided: {specs}"
                raise ValueError(_msg)

            # Store distribution configuration
            self._distributions[sym] = {
                "depends": var.depends,
                "dtype": var.dist_type,
                "params": var.dist_params,
                "func": var.dist_func
            }

    def _get_distributions(self,
                           var_keys: List[str]) -> Dict[str, Dict[str, Any]]:
        """*_get_distributions()* Retrieves the distribution specifications for a list of variable keys.

        Args:
            var_keys (List[str]): List of variable keys.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of distribution specifications.

        Raises:
            ValueError: If required distributions are missing.
        """
        # Filter distributions for requested variables
        dist = {k: v for k, v in self._distributions.items() if k in var_keys}

        # Warn about missing distributions
        missing = [k for k in var_keys if k not in dist]

        if missing:
            _msg = f"Missing distributions for variables: {missing}. "
            _msg += "Ensure _config_distributions() has been called."
            raise ValueError(_msg)

        return dist

    def _get_dependencies(self, var_keys: List[str]) -> Dict[str, List[str]]:
        """*_get_dependencies()* Retrieves variable dependencies for a list of variable keys.

        Args:
            var_keys (List[str]): List of variable keys.

        Returns:
            Dict[str, List[str]]: Dictionary mapping variable symbols to their dependencies.
        """
        deps = {
            k: v.depends for k, v in self._variables.items() if k in var_keys
        }
        return deps

    def _init_shared_cache(self) -> None:
        """*_init_shared_cache()* Initialize shared cache for all variables."""
        # Only initialize if experiments is positive
        if self._experiments < 0:
            return

        # Initialize cache for each variable once
        for var_sym in self._variables.keys():
            self._shared_cache[var_sym] = np.full((self._experiments, 1),
                                                  np.nan,
                                                  dtype=np.float64)

    def _config_simulations(self) -> None:
        """*_config_simulations()* Sets up Monte Carlo simulation objects for each coefficient to be analyzed.

        Creates a MonteCarlo instance for each coefficient with appropriate distributions and dependencies.

        Raises:
            ValueError: If coefficients or variables are not properly configured.
        """
        # Validate prerequisites
        if not self._coefficients:
            _msg = "Cannot configure simulations: no coefficients defined."
            raise ValueError(_msg)

        if not self._variables:
            _msg = "Cannot configure simulations: no variables defined."
            raise ValueError(_msg)

        if not self._distributions:
            _msg = "Cannot configure simulations: distributions not defined. "
            raise ValueError(_msg)

        # Clear existing simulations
        self._simulations.clear()

        # Initialize shared cache once
        if not self._shared_cache:
            self._init_shared_cache()

        # Create simulations for each coefficient
        for i, (pi, coef) in enumerate(self._coefficients.items()):
            # Validate coefficient before processing
            var_dims = self._validate_coefficient_vars(coef, pi)

            # Extract variables from the coefficient's expression
            vars_in_coef = list(var_dims.keys())

            # Skip coefficients with no variables
            if not vars_in_coef:
                _msg = f"Coefficient '{pi}' has no variables in expression. Skipping simulation."
                print(f"Warning: {_msg}")
                continue

            try:
                # Create Monte Carlo simulation
                sim = MonteCarlo(
                    _idx=i,
                    _sym=f"MC_{{{coef.sym}}}",
                    _fwk=self._fwk,
                    _cat=self._cat,
                    _pi_expr=coef.pi_expr,
                    _coefficient=coef,
                    _variables=self._variables,
                    # _simul_cache=self._shared_cache,
                    _experiments=self._experiments,
                    _name=f"Monte Carlo Simulation for {coef.name}",
                    description=f"Monte Carlo simulation for {coef.sym}",
                )

                # Configure with coefficient
                sim.set_coefficient(coef)

                # Get distributions with validation
                sim._distributions = self._get_distributions(vars_in_coef)
                sim._dependencies = self._get_dependencies(vars_in_coef)

                # CRITICAL: Share the cache reference
                sim._simul_cache = self._shared_cache

                # Add to simulations dictionary
                self._simulations[pi] = sim

            except Exception as e:
                _msg = f"Failed to create simulation for '{pi}': {str(e)}"
                raise RuntimeError(_msg) from e

    # ========================================================================
    # Simulation Execution Methods
    # ========================================================================

    def run(self, iters: Optional[int] = None) -> None:
        """*run()* Runs the Monte Carlo simulations.

        Args:
            iters (Optional[int]): Number of iterations (experiments) to run.
                If None, uses self._experiments value. Defaults to None.

        Raises:
            ValueError: If simulations are not configured.
            ValueError: If a required simulation is not found.
        """
        # Validate simulations exist
        if not self._simulations:
            _msg = "No simulations configured. Call create_simulations() first."
            raise ValueError(_msg)

        # Use default if not specified
        if iters is not None:
            self._experiments = iters

        #  Validate experiments
        if self._experiments < 1:
            _msg = f"Experiments must be positive. Got: {iters}"
            raise ValueError(_msg)

        # Initialize shared cache BEFORE running simulations
        if not self._shared_cache:
            for var_sym in self._variables.keys():
                self._shared_cache[var_sym] = np.full((self._experiments, 1),
                                                      np.nan,
                                                      dtype=np.float64)

        # print("----------")
        # print(f"_shared_cache keys: {self._shared_cache.keys()}")
        # # Assign shared cache to ALL simulations
        # for sim in self._simulations.values():
        #     sim._simul_cache = self._shared_cache

        results = {}

        for sym in self._coefficients:
            # Get the simulation object
            sim = self._simulations.get(sym)
            if not sim:
                _msg = f"Simulation for coefficient '{sym}' not found. "
                _msg += "Ensure _config_simulations() completed successfully."
                raise ValueError(_msg)

            try:
                # print("-----------------------------------")
                # print(f"_shared_cache status:\n {self._shared_cache}")
                # print("-----------------------------------")

                # ✅ Use shared cache
                sim._simul_cache = self._shared_cache

                # Run the simulation
                sim.run(self._experiments)

                # Store comprehensive results
                res = {
                    "inputs": sim.data,
                    "results": sim.results,
                    "statistics": sim.statistics,
                }

                # Store results
                results[sym] = res

            except Exception as e:
                _msg = f"Simulation failed for coefficient '{sym}': {str(e)}"
                raise RuntimeError(_msg) from e

        self._results = results

    def run_simulation(self, iters: Optional[int] = None) -> None:
        """*run_simulation()* Convenience method to configure and run Monte Carlo simulations.

        This method combines create_simulations() and run() into a single call. It automatically sets up distributions and simulations if needed, then runs the simulation.

        Args:
            iters (Optional[int]): Number of iterations (experiments) to run.
                If None, uses self._experiments value. Defaults to None.

        Example:
            >>> mc_handler = MonteCarloSimulation(...)
            >>> mc_handler.run_simulation(iters=10000)
        """
        # Create simulations if not already configured
        self.create_simulations()

        # Run the simulations
        self.run(iters=iters)

    # ========================================================================
    # Getter Methods
    # ========================================================================

    def get_simulation(self, name: str) -> MonteCarlo:
        """*get_simulation()* Get a simulation by name.

        Args:
            name (str): Name of the simulation.

        Returns:
            MonteCarlo: The requested simulation.

        Raises:
            ValueError: If the simulation doesn't exist.
        """
        if name not in self._simulations:
            available = ", ".join(self._simulations.keys())
            _msg = f"Simulation '{name}' does not exist. "
            _msg += f"Available: {available}"
            raise ValueError(_msg)

        return self._simulations[name]

    def get_distribution(self, name: str) -> Dict[str, Any]:
        """*get_distribution()* Get the distribution by name.

        Args:
            name (str): Name of the distribution.

        Returns:
            Dict[str, Any]: The requested distribution.

        Raises:
            ValueError: If the distribution doesn't exist.
        """
        if name not in self._distributions:
            available = ", ".join(self._distributions.keys())
            _msg = f"Distribution '{name}' does not exist. "
            _msg += f"Available: {available}"
            raise ValueError(_msg)

        return self._distributions[name]

    def get_results(self, name: str) -> Dict[str, Any]:
        """*get_results()* Get the results of a simulation by name.

        Args:
            name (str): Name of the simulation.

        Returns:
            Dict[str, Any]: The results of the requested simulation.

        Raises:
            ValueError: If the results for the simulation don't exist.
        """
        if name not in self._results:
            available = ", ".join(self._results.keys())
            _msg = f"Results for simulation '{name}' do not exist. "
            _msg += f"Available: {available}"
            raise ValueError(_msg)

        return self._results[name]

    # ========================================================================
    # Property Getters and Setters
    # ========================================================================

    @property
    def cat(self) -> str:
        """*cat* Get the Monte Carlo Simulation category.

        Returns:
            str: Category (DIST, DATA).
        """
        return self._cat

    @cat.setter
    @validate_type(str)
    @validate_choices(PYDASA_CFG.simulation_modes)
    def cat(self, val: str) -> None:
        """*cat* Set the Monte Carlo Simulation category.

        Args:
            val (str): Category value.

        Raises:
            ValueError: If category is invalid.
        """
        self._cat = val.upper()

    @property
    def experiments(self) -> int:
        """*experiments* Get the number of experiments.

        Returns:
            int: Number of experiments to run.
        """
        return self._experiments

    @experiments.setter
    @validate_type(int)
    @validate_range(min_value=1)
    def experiments(self, val: int) -> None:
        """*experiments* Set the number of experiments.

        Args:
            val (int): Number of experiments.

        Raises:
            ValueError: If value is not positive.
        """
        self._experiments = val

    @property
    def simulations(self) -> Dict[str, MonteCarlo]:
        """*simulations* Get the dictionary of Monte Carlo simulations.

        Returns:
            Dict[str, MonteCarlo]: Dictionary of Monte Carlo simulations.
        """
        return self._simulations.copy()

    @property
    def is_configured(self) -> bool:
        """*is_configured* Check if simulations are configured and ready to run.

        Returns:
            bool: True if both distributions and simulations are configured.
        """
        return len(self._distributions) > 0 and len(self._simulations) > 0

    @property
    def has_results(self) -> bool:
        """*has_results* Check if simulation results are available.

        Returns:
            bool: True if simulations have been run and results exist.
        """
        return len(self._results) > 0

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def reset(self) -> None:
        """*reset()* Reset simulation state while preserving input configuration.

        Clears results, solved state, and simulation-specific attributes (simulations, distributions, cache) while keeping variables, schema, and coefficients.
        """
        # Clear MonteCarloSimulation specific attributes
        self._simulations.clear()
        self._distributions.clear()
        self._shared_cache.clear()

        # Clear only results and is_solved, preserve coefficients (they're input config)
        self._results.clear()
        self._is_solved = False

    def clear(self) -> None:
        """*clear()* Clear all attributes to default values.

        Resets all simulation properties to their initial state, including variables, coefficients, and results from WorkflowBase.
        """
        # Reset MonteCarloSimulation specific attributes first
        self._cat = SimulationMode.DIST.value
        self._simulations = {}
        self._distributions = {}
        self._shared_cache = {}
        self._experiments = -1

        # Call both parent classes' clear methods explicitly for multiple inheritance
        Foundation.clear(self)
        WorkflowBase.clear(self)

        # Reset symbol after parent clears
        self._sym = f"MCS_{{\\Pi_{{{self._idx}}}}}"

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert the handler's state to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the handler's state.
        """
        # Get base serialization from WorkflowBase
        result = super().to_dict()

        # Add MonteCarloSimulation-specific attributes
        result["cat"] = self._cat
        result["experiments"] = self._experiments
        result["simulations"] = {
            k: v.to_dict() for k, v in self._simulations.items()
        }
        result["distributions"] = self._distributions

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MonteCarloSimulation:
        """*from_dict()* Create a MonteCarloSimulation instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing the handler's state.

        Returns:
            MonteCarloSimulation: New instance of MonteCarloSimulation.
        """
        # Use parent class to handle base deserialization
        instance = cast(MonteCarloSimulation, super().from_dict(data))

        # Handle MonteCarloSimulation-specific attributes
        instance._cat = data.get("cat", SimulationMode.DIST.value)
        instance._experiments = data.get("experiments", -1)
        instance._distributions = data.get("distributions", {})

        # Reconstruct MonteCarlo simulations if present
        simulations_data = data.get("simulations", {})
        if simulations_data:
            instance._simulations = {
                k: MonteCarlo.from_dict(v) for k, v in simulations_data.items()
            }

        return instance
