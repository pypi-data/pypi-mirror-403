# -*- coding: utf-8 -*-
"""
Module simulation.py
===========================================

Module for Monte Carlo Simulation execution and analysis in *PyDASA*.

This module provides the MonteCarlo class for performing Monte Carlo simulations on dimensionless coefficients derived from dimensional analysis.

Classes:

    **MonteCarlo**: Performs Monte Carlo simulations on dimensionless coefficients.

*IMPORTANT:* Based on the theory from:

    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Any, Callable, Tuple, Union

# python third-party modules
import numpy as np
from numpy.typing import NDArray
from sympy import lambdify
# from sympy import Expr, Symbol
from scipy import stats
import sympy as sp

# Import validation base classes
from pydasa.core.basic import Foundation
from pydasa.core.setup import Frameworks   # , PYDASA_CFG
from pydasa.core.setup import SimulationMode
from pydasa.core.setup import PYDASA_CFG

# Import validation decorators
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_range
from pydasa.validations.decorators import validate_choices
from pydasa.validations.decorators import validate_emptiness
# from pydasa.validations.decorators import validate_list_types
from pydasa.validations.decorators import validate_dict_types
from pydasa.validations.decorators import validate_custom

# Import related classes
from pydasa.dimensional.buckingham import Coefficient
from pydasa.elements.parameter import Variable
from pydasa.elements.specs.numerical import BoundsSpecs

# Import utils
from pydasa.serialization.parser import parse_latex, create_latex_mapping

# Import configuration
from pydasa.serialization.parser import latex_to_python

# # Type aliases
# SymbolDict = Dict[str, sp.Symbol]
# # FIX: Allow Basic or Expr since subs() returns Basic
# SymExpr = Union[sp.Expr, sp.Basic]


@dataclass
class MonteCarlo(Foundation, BoundsSpecs):
    """**MonteCarlo** class for stochastic analysis in *PyDASA*.

    Performs Monte Carlo simulations on dimensionless coefficients to analyze the coefficient's distribution and sensitivity to input parameter
    variations.

    Args:
        Foundation: Foundation class for validation of symbols and frameworks.
        BoundsSpecs: Value bounds for statistical properties (mean, median, dev, min, max).

    Attributes:
        # Core Identification
        name (str): User-friendly name of the Monte Carlo simulation.
        description (str): Brief summary of the simulation.
        _idx (int): Index/precedence of the simulation.
        _sym (str): Symbol representation (LaTeX or alphanumeric).
        _alias (str): Python-compatible alias for use in code.
        _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).
        _cat (str): Category of analysis (SYM, NUM, HYB).

        # Coefficient and Expression Management
        _coefficient (Optional[Coefficient]): Coefficient for the simulation.
        _pi_expr (str): LaTeX expression to analyze.
        _sym_func (Callable): Sympy function of the simulation.
        _exe_func (Callable): Executable function for numerical evaluation.

        # Variable Management
        _variables (Dict[str, Variable]): Variable symbols in the expression.
        _symbols (Dict[str, Any]): Python symbols for the variables.
        _aliases (Dict[str, Any]): Variable aliases for use in code.
        _latex_to_py (Dict[str, str]): Mapping from LaTeX to Python variable names.
        _py_to_latex (Dict[str, str]): Mapping from Python to LaTeX variable names.

        # Simulation Configuration
        _experiments (int): Number of simulation experiments to run. Default is -1.
        _distributions (Dict[str, Dict[str, Any]]): Variable sampling distributions.
        _simul_cache (Dict[str, NDArray[np.float64]]): Working sampled values cache.

        # Results and Input data
        _data (Dict[str, NDArray[np.float64]]): Input data dictionary mapping variable names to arrays.
        _results (Optional[np.ndarray]): Raw simulation results.

        # Statistics (inherited from BoundsSpecs: _mean, _median, _dev, _min, _max)
        _mean (float): Mean value of simulation results.
        _median (float): Median value of simulation results.
        _dev (float): Standard deviation of simulation results.
        _min (float): Minimum value in simulation results.
        _max (float): Maximum value in simulation results.
        _count (int): Number of valid simulation results (MonteCarlo-specific).
        _statistics (Optional[Dict[str, float]]): Statistical summary.
    """

    # ========================================================================
    # Core Identification
    # ========================================================================

    # :attr: name
    _name: str = ""
    """User-friendly name of the Monte Carlo simulation."""

    # :attr: description
    description: str = ""
    """Brief summary of the simulation."""

    # :attr: _idx
    _idx: int = -1
    """Index/precedence of the simulation."""

    # :attr: _sym
    _sym: str = ""
    """Symbol representation (LaTeX or alphanumeric)."""

    # :attr: _alias
    _alias: str = ""
    """Python-compatible alias for use in code."""

    # :attr: _fwk
    _fwk: str = Frameworks.PHYSICAL.value
    """Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM)."""

    # :attr: _cat
    _cat: str = SimulationMode.DIST.value
    """Category of analysis (DIST, DATA)."""

    # ========================================================================
    # Coefficient and Expression Management
    # ========================================================================

    # :attr: _coefficient
    _coefficient: Coefficient = field(default_factory=Coefficient)
    """Coefficient for the simulation."""

    # :attr: _pi_expr
    _pi_expr: Optional[str] = None
    """LaTeX expression to analyze."""

    # :attr: _sym_func
    _sym_func: Optional[Union[sp.Expr, sp.Basic]] = None
    """Sympy expression object for the coefficient (Mul, Add, Pow, Symbol, etc.)."""

    # :attr: _exe_func
    _exe_func: Optional[Callable[..., Union[float, np.ndarray]]] = None
    """Compiled executable function for evaluation of the coefficient."""

    # ========================================================================
    # Variable Management
    # ========================================================================

    # :attr: _variables
    _variables: Dict[str, Variable] = field(default_factory=dict)
    """Dictionary of variables in the expression."""

    # :attr: _symbols
    _symbols: Dict[str, sp.Symbol] = field(default_factory=dict)
    """Map from variable names (strings) to sympy Symbols."""

    # :attr: _aliases
    _aliases: Dict[str, sp.Symbol] = field(default_factory=dict)
    """Map from Variable aliases to sympy Symbols."""

    # :attr: _latex_to_py
    _latex_to_py: Dict[str, str] = field(default_factory=dict)
    """Map from LaTeX symbols to Python-compatible names."""

    # :attr: _py_to_latex
    _py_to_latex: Dict[str, str] = field(default_factory=dict)
    """Map from Python-compatible names to LaTeX symbols."""

    # :attr: _var_symbols
    _var_symbols: List[str] = field(default_factory=list)
    """List of variable names extracted from expression."""
    # ========================================================================
    # Simulation Configuration
    # ========================================================================

    # :attr: _experiments
    _experiments: int = -1
    """Number of simulation iterations to run."""

    # :attr: _distributions
    _distributions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Variable sampling distributions and specifications that includes:
        - 'dtype': Distribution type name.
        - 'params': Distribution parameters (mean, std_dev, etc.).
        - 'func': Function for sampling, usually in Lambda format.
        - 'depends': List of variables this variable depends on.
    """

    # :attr: _dependencies
    _dependencies: Dict[str, List[str]] = field(default_factory=dict,
                                                init=False)
    """Variable dependencies for simulations."""

    # :attr: _simul_cache
    _simul_cache: Dict[str, NDArray[np.float64]] = field(default_factory=dict)
    """Working sampled values during each simulation iteration. Memory cache."""

    # ========================================================================
    # Results and Inputs
    # ========================================================================

    # :attr: _data
    _data: Dict[str, NDArray[np.float64]] = field(default_factory=dict)
    """Input data dictionary mapping variable names to their value arrays."""

    # :attr: _results
    _results: NDArray[np.float64] = field(
        default_factory=lambda: np.array([], dtype=np.float64))
    """Raw simulation results."""

    # ========================================================================
    # Statistics
    # ========================================================================

    # :attr: _mean
    _mean: Optional[float] = np.nan
    """Mean value of simulation results."""

    # :attr: _median
    _median: Optional[float] = np.nan
    """Median value of simulation results."""

    # :attr: _dev
    _dev: Optional[float] = np.nan
    """Standard deviation of simulation results."""

    # :attr: _min
    _min: Optional[float] = np.nan
    """Minimum value in simulation results."""

    # :attr: _max
    _max: Optional[float] = np.nan
    """Maximum value in simulation results."""

    # :attr: _count
    _count: int = -1
    """Number of valid simulation results."""

    # :attr: _statistics
    _statistics: Optional[Dict[str, Union[float, int, None]]] = None
    """Statistical summary of the Monte Carlo simulation results."""

    # ========================================================================
    # Initialization
    # ========================================================================

    def _validate_dist(self, value: Dict[str, Dict[str, Any]], field_name: str) -> None:
        """*_validate_dist()* Custom validator to ensure all distributions have callable 'func'.

        Args:
            value: The distributions dictionary to validate.
            field_name: Name of the field being validated.

        Raises:
            ValueError: If distributions don't have callable 'func' functions.
        """
        if not all(callable(v["func"]) for v in value.values()):
            inv = [k for k, v in value.items() if not callable(v["func"])]
            raise ValueError(
                f"All distributions must have callable 'func' functions. "
                f"Invalid entries: {inv}"
            )

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the Monte Carlo simulation."""
        # Initialize from base class
        super().__post_init__()

        # Validate coefficient
        if not self._coefficient.pi_expr:
            raise ValueError("Coefficient must have a valid expression")

        # Derive expression from coefficient
        self._pi_expr = self._coefficient.pi_expr

        # Set default symbol if not specified
        if not self._sym:
            self._sym = f"MC_\\Pi_{{{self._idx}}}" if self._idx >= 0 else "MC_\\Pi_{}"

        # Set default Python alias if not specified
        if not self._alias:
            self._alias = latex_to_python(self._sym)

        # Set name and description if not already set
        if not self._name:
            self._name = f"{self._sym} Monte Carlo"

        if not self.description:
            self.description = f"Monte Carlo simulation for {self._sym}"

        if self._pi_expr:
            # Parse the expression
            self._parse_expression(self._pi_expr)

        # Preallocate full array space with NaN only if experiments > 0
        n_sym = len(self._symbols)
        if n_sym > 0 and self._experiments > 0:
            # Only allocate if we have variables and valid experiment count
            if not self._data:  # Check if dict is empty
                # Allocate space for all variables that appear in the expression
                # Use _latex_to_py if available (from parsed expression), otherwise use _variables
                var_names = self._latex_to_py if self._latex_to_py else list(self._variables.keys())
                for var_name in var_names:
                    self._data[var_name] = np.full(self._experiments,
                                                   np.nan,
                                                   dtype=np.float64)
            if self._results.size == 0:  # Check size, not None
                self._results = np.full((self._experiments, 1),
                                        np.nan,
                                        dtype=np.float64)

        # Only initialize cache if not already provided and experiments > 0
        if not self._simul_cache and self._experiments > 0:
            # Create local cache only if no external cache provided
            for var in self._variables.keys():
                self._simul_cache[var] = np.full((self._experiments, 1),
                                                 np.nan,
                                                 dtype=np.float64)

        # Statistics attributes already set to np.nan via declarations
        # _count remains MonteCarlo-specific
        self.count = 0

    # ========================================================================
    # Foundation and Configuration
    # ========================================================================

    def _validate_readiness(self) -> None:
        """*_validate_readiness()* Checks if the simulation can be performed.

        Raises:
            ValueError: If the simulation is not ready due to missing variables, executable function, or invalid number of iterations.
        """
        if not self._variables:
            _msg = "No variables found in the expression."
            raise ValueError(_msg)
        if self._cat == SimulationMode.DIST.value and not self._distributions:
            _msg = "Distributions must be provided in 'DIST' simulation mode."
            raise ValueError(_msg)
        if self._cat == SimulationMode.DATA.value and not self._data:
            _msg = "Input data must be provided in 'DATA' simulation mode."
            raise ValueError(_msg)
        if not self._sym_func:
            _msg = "No Sympy function is not defined for the simulation."
            raise ValueError(_msg)
        if self._experiments < 1:
            _msg = f"Invalid number of iterations: {self._experiments}"
            raise ValueError(_msg)

    def set_coefficient(self, coef: Coefficient) -> None:
        """*set_coefficient()* Configure analysis from a coefficient.

        Args:
            coef (Coefficient): Dimensionless coefficient to analyze.

        Raises:
            ValueError: If the coefficient doesn't have a valid expression.
        """
        if not coef.pi_expr:
            raise ValueError("Coefficient does not have a valid expression.")

        # Save coefficient
        self._coefficient = coef

        # Set expression
        self._pi_expr = coef.pi_expr

        # Parse coefficient expression
        if coef._pi_expr:
            self._parse_expression(self._pi_expr)

        # Set name and description if not already set
        if not self._name:
            self._name = f"{coef.name} Monte Carlo Experiments"
        if not self.description:
            self.description = f"Monte Carlo simulation for {coef.name}"

    def _collect_dataset(self,
                         vars: Dict[str, Variable]) -> Dict[str, NDArray[np.float64]]:
        """*_collect_dataset()* Consolidate dataset from all variables for 'DATA' simulation mode.

        Args:
            vars (Dict[str, Variable]): Dictionary of variables to collect data from.

        Returns:
            Dict[str, NDArray[np.float64]]: Dictionary mapping variable symbols to their data arrays.

        Raises:
            ValueError: If variables have no data.
            ValueError: If variables have inconsistent lengths.
        """
        # Initialize dataset dictionary and working variables
        _dataset = {}
        _exp_len = None

        for sym, var in vars.items():
            # Check if variable has data
            if var.data is None or len(var.data) == 0:
                _msg = f"Variable '{var.sym}' has no data. "
                raise ValueError(_msg)
            # Check length consistency
            _cur_len = len(var.data)
            if _exp_len is None:
                _exp_len = _cur_len
            elif _cur_len != _exp_len:
                _msg = f"Variable '{var.sym}' has {_cur_len} data points, "
                _msg += f"but expected {_exp_len}."
                # All variables must have the same length."
                raise ValueError(_msg)
            _dataset[sym] = np.array(var.data, dtype=np.float64)
        # return the consolidated dataset
        return _dataset

    def _generate_dataset(self,
                          vars: Dict[str, Variable]) -> Dict[str, NDArray[np.float64]]:
        """*_generate_dataset()* Generate dataset by sampling from variable distributions for 'DIST' mode.

        Args:
            vars (Dict[str, Variable]): Dictionary of variables to generate samples for.

        Returns:
            Dict[str, NDArray[np.float64]]: Dictionary mapping variable symbols to sampled arrays.

        Raises:
            ValueError: If sampling fails or encounters errors.
        """
        # Initialize dataset dictionary
        _dataset = {}
        for var_name in vars.keys():
            _dataset[var_name] = np.full(self._experiments,
                                         np.nan,
                                         dtype=np.float64)

        # Run sampling loop for all experiments
        for i in range(self._experiments):
            try:
                # Dict to store sample memory for the iteration
                memory: Dict[str, float] = {}

                # Generate samples for all variables
                for var in vars.values():
                    # Check for cached value
                    cached_val = self._get_cached_value(var.sym, i)

                    # If no cached value, generate new sample
                    if cached_val is None or np.isnan(cached_val):
                        val = self._generate_sample(var, memory)
                        memory[var.sym] = val
                        self._set_cached_value(var.sym, i, val)
                    else:
                        memory[var.sym] = cached_val

                    # Store sampled value in dataset
                    _dataset[var.sym][i] = memory[var.sym]

            except Exception as e:
                _msg = f"Error generating sample at iteration {i}: {str(e)}"
                raise ValueError(_msg)

        return _dataset

    def _parse_expression(self, expr: str) -> None:
        """*_parse_expression()* Parse the LaTeX expression into a sympy function.

        Args:
            expr (str): LaTeX expression to parse.

        Raises:
            ValueError: If the expression cannot be parsed.
        """
        try:
            # Parse the expression
            self._sym_func = parse_latex(expr)

            if self._sym_func is None:
                raise ValueError("Parsing returned None")

            # Store the sympy expression
            self._sym_func = self._sym_func

            # Create symbol mapping
            maps = create_latex_mapping(expr)

            symbols_raw: Dict[Any, sp.Symbol] = maps[0]
            aliases_raw: Dict[str, sp.Symbol] = maps[1]
            latex_to_py: Dict[str, str] = maps[2]
            py_to_latex: Dict[str, str] = maps[3]

            # Convert Symbol keys to strings
            self._symbols = {
                str(k): v for k, v in symbols_raw.items()
            }
            self._aliases = aliases_raw
            self._latex_to_py = latex_to_py
            self._py_to_latex = py_to_latex

            # Substitute LaTeX symbols with Python symbols
            for latex_sym_key, py_sym in symbols_raw.items():
                if self._sym_func is None:
                    break

                # Handle both string and Symbol keys
                if isinstance(latex_sym_key, sp.Symbol):
                    # subs() returns Basic, which is fine
                    self._sym_func = self._sym_func.subs(latex_sym_key, py_sym)
                else:
                    # Try to find the symbol by name
                    latex_symbol = sp.Symbol(str(latex_sym_key))
                    self._sym_func = self._sym_func.subs(latex_symbol, py_sym)

            # Get Python variable names as strings
            con1 = self._sym_func is not None
            con2 = hasattr(self._sym_func, "free_symbols")
            if con1 and con2:
                free_symbols = self._sym_func.free_symbols
                self._var_symbols = sorted([str(s) for s in free_symbols])
            else:
                raise ValueError("Expression has no free symbols")

        except Exception as e:
            _msg = f"Failed to parse expression: {str(e)}"
            raise ValueError(_msg)

    # ========================================================================
    # Simulation Execution
    # ========================================================================

    def _generate_sample(self,
                         var: Variable,
                         memory: Dict[str, float]) -> float:
        """*_generate_sample()* Generate a sample for a given variable.

        Args:
            var (Variable): The variable to generate a sample for.
            memory (Dict[str, float]): The current iteration values.

        Returns:
            float: The generated sample.
        """
        # Initialize sample
        data: float = -1.0

        # relevant data type, HOTFIX
        _type = (list, tuple, np.ndarray)

        # Get dependency values from memory
        chace_deps = []
        for dep in var.depends:
            if dep in memory:
                dep_val = memory[dep]
                # If dependency is a list/tuple/array, take the last value
                if isinstance(dep_val, (list, tuple, np.ndarray)):
                    dep_val = dep_val[-1]
                chace_deps.append(dep_val)

        # print(f"chace_deps: {chace_deps}")

        # if the distribution function is defined
        if var._dist_func is not None:
            # If the variable is independent
            if not var.depends:
                data = var.sample()

            # If the variable has dependencies
            elif len(var.depends) == len(chace_deps):
                raw_data = var.sample(*chace_deps)
                # print(f"raw_data: {raw_data}")

                # Handle array-like results
                if isinstance(raw_data, _type):
                    # get the last number
                    data = raw_data[-1]

                    # adjust the memory accordingly to the rest of the list
                    for dep in var.depends:
                        if dep in memory:
                            memory[dep] = raw_data[var.depends.index(dep)]
                # otherwise, its a number
                else:
                    data = raw_data

        # print(f"dependencies keys {var.depends}")
        # print(f"memory: {memory}")

        # Store sample in memory
        memory[var.sym] = float(data)

        # return sampled data
        return data

    # def run_OLD(self, iters: Optional[int] = None) -> None:
    #     """*run()* Execute the Monte Carlo simulation.

    #     Args:
    #         iters (int, optional): Number of iterations to run. If None, uses _experiments.

    #     Raises:
    #         ValueError: If simulation is not ready or encounters errors during execution.
    #     """
    #     # Validate simulation readiness
    #     self._validate_readiness()

    #     # Set iterations if necessary
    #     if iters is not None:
    #         self._experiments = iters

    #     # Clear previous results, inputs, and intermediate values
    #     self._reset_memory()

    #     # Create lambdify function using Python symbols
    #     aliases = [self._aliases[v] for v in self._var_symbols]
    #     self._exe_func = lambdify(aliases, self._sym_func, "numpy")

    #     if self._exe_func is None:
    #         raise ValueError("Failed to create executable function")

    #     # Run experiment loop
    #     for _iter in range(self._experiments):
    #         try:
    #             # Dict to store sample memory for the iteration
    #             memory: Dict[str, float] = {}

    #             # run through all variables
    #             for var in self._variables.values():
    #                 # Check for cached value
    #                 cached_val = self._get_cached_value(var.sym, _iter)

    #                 # if no cached value, generate new sample
    #                 if cached_val is None or np.isnan(cached_val):
    #                     # Generate sample for the variable
    #                     val = self._generate_sample(var, memory)
    #                     # Store the sample in the iteration values
    #                     memory[var.sym] = val
    #                     self._set_cached_value(var.sym, _iter, val)

    #                 # otherwise use cached value
    #                 else:
    #                     # Use cached value
    #                     memory[var.sym] = cached_val

    #             # Prepare sorted/ordered values from memory for evaluation
    #             sorted_vals = [memory[var] for var in self._latex_to_py]

    #             # FIXME hotfix for queue functions
    #             _type = (list, tuple, np.ndarray)
    #             # Handle adjusted values
    #             if any(isinstance(v, _type) for v in sorted_vals):
    #                 sorted_vals = [
    #                     v[-1] if isinstance(v, _type) else v for v in sorted_vals]

    #             # Evaluate the coefficient
    #             result = float(self._exe_func(*sorted_vals))

    #             # Handle array results
    #             if isinstance(result, _type):
    #                 result = result[-1]
    #                 sorted_vals = [v[-1] for v in result]

    #             # Save simulation inputs and results
    #             self._data[_iter, :] = sorted_vals
    #             self._results[_iter] = result

    #         except Exception as e:
    #             _msg = f"Error during simulation run {_iter}: {str(e)}"
    #             raise ValueError(_msg)

    #     # Calculate statistics
    #     self._calculate_statistics()

    def run(self,
            iters: Optional[int] = None,
            mode: Union[str, SimulationMode] = SimulationMode.DIST) -> None:
        """*run()* Execute the Monte Carlo simulation.

        Args:
            iters (int, optional): Number of iterations to run. If None, uses _experiments.
            mode (str | SimulationMode, optional): Simulation mode. Either 'DIST' to sample from distributions, or 'DATA' to use pre-existing Variable._data. Defaults to 'DIST'.

        Raises:
            ValueError: If simulation is not ready or encounters errors during execution.
        """
        # STEP 1: check simulation configuration
        # Set mode using validated property
        self.cat = mode

        # Set iterations using validated property
        if iters is not None:
            self.experiments = iters

        # Validate simulation readiness
        self._validate_readiness()

        # Clear previous results, inputs, and intermediate values, etc.
        self._reset_memory()

        # STEP 2: prepare executale functions for simulation
        # Create lambdify function using Python symbols
        aliases = [self._aliases[v] for v in self._var_symbols]
        self._exe_func = lambdify(aliases, self._sym_func, "numpy")

        if self._exe_func is None:
            raise ValueError("Failed to create executable function")

        # STEP 3: setup the input dataset according to mode, 'DATA or 'DIST'
        # Filter variables to only those needed for the coefficient evaluation
        # Use _latex_to_py to ensure we get all variables from the parsed expression
        vars_in_expr = {}
        for k, v in self._variables.items():
            # Include if variable symbol is in _latex_to_py (parsed expression)
            # or in _var_symbols (original symbols) or alias matches
            if k in self._latex_to_py or k in self._var_symbols or v._alias in self._var_symbols:
                vars_in_expr[k] = v

        if self._cat == SimulationMode.DATA.value:
            # Collect dataset from variables in expression
            self._data = self._collect_dataset(vars_in_expr)
        elif self._cat == SimulationMode.DIST.value:
            # Generate dataset by sampling from distributions
            self._data = self._generate_dataset(vars_in_expr)

        # STEP 4: evaluate coefficient for all experiments
        for i in range(self._experiments):
            try:
                # Get values for this iteration from _data dict
                iter_vals = {
                    _sym: self._data[_sym][i] for _sym in self._data.keys()
                }

                # Prepare sorted/ordered values for evaluation
                # CRITICAL: Must use same order as aliases (from _var_symbols)
                # Map _var_symbols back to LaTeX symbols to lookup values
                sorted_vals = []
                for py_sym in self._var_symbols:
                    # Find the LaTeX symbol that maps to this Python symbol
                    latex_sym = self._py_to_latex.get(py_sym, py_sym)
                    if latex_sym in iter_vals:
                        sorted_vals.append(iter_vals[latex_sym])
                    else:
                        # Fallback: try using the Python symbol directly
                        sorted_vals.append(iter_vals[py_sym])

                # FIXME: hotfix for queue functions
                _type = (list, tuple, np.ndarray)
                if any(isinstance(v, _type) for v in sorted_vals):
                    sorted_vals = [v[-1] if isinstance(v, _type) else v for v in sorted_vals]

                # Evaluate the coefficient
                result = float(self._exe_func(*sorted_vals))

                # Handle array results
                if isinstance(result, _type):
                    result = result[-1]

                # Store result
                self._results[i] = result

            except Exception as e:
                _msg = f"Error calculating coefficient at iteration {i}: {str(e)}"
                raise ValueError(_msg)

        # Calculate statistics
        self._calculate_statistics()

        # Update experiment count
        self.count = self._experiments

    # ========================================================================
    # Memory and Statistics Management
    # ========================================================================

    def _reset_memory(self) -> None:
        """*_reset_memory()* Reset results and inputs arrays."""
        # Reset data dictionary with NaN arrays
        self._data = {}
        for sym in self._variables.keys():
            self._data[sym] = np.full(self._experiments,
                                      np.nan,
                                      dtype=np.float64)
        self._results = np.full(self._experiments,
                                np.nan,
                                dtype=np.float64)

        # # reset intermediate values
        # for var in self._variables.keys():
        #     self._simul_cache[var] = np.full(self._experiments,
        #                                      np.nan,
        #                                      dtype=np.float64)

    def _reset_statistics(self) -> None:
        """*_reset_statistics()* Reset all statistical attributes to default values."""
        # Reset inherited BoundsSpecs attributes to None
        BoundsSpecs.clear(self)

        # Override with MonteCarlo-specific defaults (np.nan for computed results)
        self.mean = np.nan
        self.median = np.nan
        self.dev = np.nan
        self.min = np.nan
        self.max = np.nan

        # Reset MonteCarlo-specific count
        self._count = -1

    def _calculate_statistics(self) -> None:
        """*_calculate_statistics()* Calculate statistical properties of simulation results."""
        # Check for empty array (size == 0), not None
        if self._results.size < 1:
            raise ValueError("No results available. Run simulation first.")

        else:
            self.mean = float(np.mean(self._results))
            self.median = float(np.median(self._results))
            self.dev = float(np.std(self._results))
            self.min = float(np.min(self._results))
            self.max = float(np.max(self._results))
            self.count = len(self._results)

    def get_confidence_interval(self,
                                conf: float = 0.95) -> Tuple[float, float]:
        """*get_confidence_interval()* Calculate the confidence interval.

        Args:
            conf (float, optional): Confidence level for the interval. Defaults to 0.95.

        Raises:
            ValueError: If no results are available or if the confidence level is invalid.

        Returns:
            Tuple[float, float]: Lower and upper bounds of the confidence interval.
        """
        if self._results.size == 0:
            _msg = "No results available. Run the simulation first."
            raise ValueError(_msg)

        if not 0 < conf < 1:
            _msg = f"Confidence must be between 0 and 1. Got: {conf}"
            raise ValueError(_msg)

        # Calculate the margin of error using the t-distribution
        alpha = stats.t.ppf((1 + conf) / 2, self._count - 1)
        margin = alpha * self._dev / np.sqrt(self._count)
        ans = (self._mean - margin, self._mean + margin)
        return ans

    # ========================================================================
    # simulation cache management
    # ========================================================================

    def _validate_cache_locations(self,
                                  var_syms: Union[str, List[str]],
                                  idx: int) -> bool:
        """*_validate_cache_locations()* Check if cache locations are valid for variable(s) at the iteration.

        Args:
            var_syms (Union[str, List[str]]): Variable symbol(s) to check.
            idx (int): Iteration index to check.

        Returns:
            bool: True if all cache locations are valid (including NaN placeholders), False otherwise.
        """
        # Convert single string to list for uniform handling
        syms = [var_syms] if isinstance(var_syms, str) else var_syms

        # Start with assumption that cache is invalid
        valid = False

        # Check each symbol
        for var_sym in syms:
            # Reset validity check for each variable
            var_valid = False

            # Get cache array for the variable
            cache_array = self._simul_cache.get(var_sym, None)

            # Check if cache exists and location is valid
            if cache_array is not None:
                # Check if index is within bounds
                if idx < cache_array.shape[0] and idx >= 0:
                    # Location exists - valid regardless of whether value is NaN
                    # (NaN is a valid placeholder for uncomputed values)
                    var_valid = True

            # If any variable is invalid, entire check fails
            if not var_valid:
                return False

        # All variables passed validation
        valid = True
        return valid

    def _get_cached_value(self, var_sym: str, idx: int) -> Optional[float]:
        """*_get_cached_value()* Retrieve cached value for variable at the iteration.

        Args:
            var_sym (str): Variable symbol.
            idx (int): Iteration index.

        Returns:
            Optional[float]: Cached value if valid, None otherwise.
        """
        # Initialize return value
        cache_data = None

        # Check if cache location is valid
        if self._validate_cache_locations(var_sym, idx):
            # Retrieve cached data
            cache_data = self._simul_cache[var_sym][idx, 0]
            # if value is not NaN (valid location, but no data yet)
            if not np.isnan(cache_data):
                # cast to float the computed value
                cache_data = float(cache_data)
        # return valid cache location
        return cache_data

    def _set_cached_value(self,
                          var_sym: str,
                          idx: int,
                          val: Union[float, Dict]) -> None:
        """*_set_cached_value()* Store value in cache for variable at the iteration.

        Args:
            var_sym (str): Variable symbol.
            idx (int): Iteration index.
            val (Union[float, Dict]): Value to cache. It can be a normal number (float) or a memory cache correction (dict).

        Raises:
            ValueError: If cache location is invalid.
        """
        # Normalize input to dictionary format
        cache_updates = val if isinstance(val, dict) else {var_sym: val}

        # Validate all cache locations
        if not self._validate_cache_locations(list(cache_updates.keys()), idx):
            invalid_vars = list(cache_updates.keys())
            _msg = f"Invalid cache location at index {idx}. "
            _msg += f"For variables: {invalid_vars}"
            raise ValueError(_msg)

        # Store all values
        for k, v in cache_updates.items():
            self._simul_cache[k][idx, 0] = v

    # ========================================================================
    # Results Extraction
    # ========================================================================

    def extract_results(self) -> Dict[str, NDArray[np.float64]]:
        """*extract_results()* Extract simulation results.

        Returns:
            Dict[str, NDArray[np.float64]]: Dictionary containing simulation results.
        """
        export: Dict[str, NDArray[np.float64]] = {}

        # Extract data for each variable from the dictionary
        for var_name, var_data in self._data.items():
            # Use a meaningful key that includes variable name and coefficient
            key = f"{var_name}@{self._coefficient.sym}"
            export[key] = var_data.copy()

        # Add the coefficient results
        export[self._coefficient.sym] = self._results.flatten()
        return export

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def variables(self) -> Dict[str, Variable]:
        """*variables* Get the variables involved in the simulation.

        Returns:
            Dict[str, Variable]: Dictionary of variable symbols and Variable objects.
        """
        return self._variables.copy()

    @property
    def coefficient(self) -> Optional[Coefficient]:
        """*coefficient* Get the coefficient associated with the simulation.

        Returns:
            Optional[Coefficient]: The associated Coefficient object, or None.
        """
        return self._coefficient

    @property
    def results(self) -> NDArray[np.float64]:
        """*results* Raw simulation results.

        Returns:
            NDArray[np.float64]: Copy of the simulation results.

        Raises:
            ValueError: If no results are available.
        """
        if self._results.size == 0:
            raise ValueError("No results available. Run the simulation first.")
        return self._results.copy()

    @property
    def data(self) -> Dict[str, NDArray[np.float64]]:
        """*data* Get the input data dictionary.

        Returns:
            Dict[str, NDArray[np.float64]]: Copy of input data mapping variable names to arrays.

        Raises:
            ValueError: If no data is available.
        """
        if not self._data:
            raise ValueError("No input data available. Run the simulation first.")
        return {k: v.copy() for k, v in self._data.items()}

    @data.setter
    @validate_type(dict, allow_none=False)
    def data(self, val: Dict[str, Union[List, NDArray[np.float64]]]) -> None:
        """*data* Set the input data dictionary.

        Args:
            val (Dict[str, Union[List, NDArray[np.float64]]]): Input data mapping variable names to arrays.

        Raises:
            ValueError: If value is not a dictionary.
        """
        # Convert all values to numpy arrays if they're lists
        self._data = {}
        for k, v in val.items():
            if isinstance(v, list):
                self._data[k] = np.array(v, dtype=np.float64)
            else:
                self._data[k] = v

    @property
    def statistics(self) -> Dict[str, Union[float, int, None]]:
        """*statistics* Get the statistical analysis of simulation results.

        Raises:
            ValueError: If no results are available.

        Returns:
            Dict[str, Union[float, int, None]]: Dictionary containing statistical properties.
        """
        if self._results.size == 0:
            _msg = "No statistics available. Run the simulation first."
            raise ValueError(_msg)

        # Build statistics dictionary from individual attributes
        self._statistics = {
            "mean": self.mean,
            "median": self.median,
            "dev": self.dev,
            "min": self.min,
            "max": self.max,
            "count": self.count
        }
        return self._statistics

    @property
    def experiments(self) -> int:
        """*experiments* Number of simulation experiments.

        Returns:
            int: Current number of experiments.
        """
        return self._experiments

    @experiments.setter
    @validate_type(int, allow_none=False)
    @validate_range(min_value=1)
    def experiments(self, val: int) -> None:
        """*experiments* Set the number of simulation runs.

        Args:
            val (int): Number of experiments to run the simulation.

        Raises:
            ValueError: If the number of experiments is not positive.
        """
        self._experiments = val

    @property
    def distributions(self) -> Dict[str, Dict[str, Any]]:
        """*distributions* Get the variable distributions.

        Returns:
            Dict[str, Dict[str, Any]]: Current variable distributions.
        """
        return self._distributions.copy()

    @distributions.setter
    @validate_type(dict, allow_none=False)
    @validate_emptiness()
    @validate_dict_types(str, dict)
    @validate_custom(lambda self, val: self._validate_dist(val,
                                                           "distributions"))
    def distributions(self, val: Dict[str, Dict[str, Any]]) -> None:
        """*distributions* Set the variable distributions.

        Args:
            val (Dict[str, Dict[str, Any]]): New variable distributions.

        Raises:
            ValueError: If the distributions are invalid.
        """
        self._distributions = val

    @property
    def dependencies(self) -> Dict[str, List[str]]:
        """*dependencies* Get variable dependencies.

        Returns:
            Dict[str, List[str]]: Dictionary of variable dependencies.
        """
        return self._dependencies

    @dependencies.setter
    @validate_type(dict, allow_none=False)
    @validate_dict_types(str, list)
    def dependencies(self, val: Dict[str, List[str]]) -> None:
        """*dependencies* Set variable dependencies.

        Args:
            val (Dict[str, List[str]]): New variable dependencies.
        """
        self._dependencies = val

    @property
    def cat(self) -> str:
        """*mode* Get simulation execution category.

        Returns:
            str: Current simulation category (DIST or DATA).
        """
        return self._cat

    @cat.setter
    @validate_type(str, allow_none=False)
    @validate_choices(PYDASA_CFG.simulation_modes, case_sensitive=False)
    def cat(self, val: str) -> None:
        """*cat* Set the analysis category.

        Args:
            val (str): Category value.

        Raises:
            ValueError: If category is invalid.
        """
        self._cat = val.upper()

    # Individual statistics properties
    # Note: mean, median, dev, min, and max are inherited from BoundsSpecs

    @property
    def count(self) -> int:
        """*count* Number of valid simulation results.

        Returns:
            int: Result count.

        Raises:
            ValueError: If no results are available.
        """
        if self._results.size < 1:
            _msg = "No statistics available. Run the simulation first."
            raise ValueError(_msg)
        return self._count

    @count.setter
    @validate_type(int, allow_none=False)
    @validate_range(min_value=0)
    def count(self, val: int) -> None:
        """*count* Set the number of valid simulation results.

        Args:
            val (int): Result count.

        Raises:
            ValueError: If count is negative.
        """
        self._count = val

    @property
    def summary(self) -> Dict[str, Union[float, int, None]]:
        """*summary* Get the statistical analysis of simulation results.

        Raises:
            ValueError: If no results are available.

        Returns:
            Dict[str, Union[float, int, None]]: Dictionary containing statistical properties.
        """
        if self._results.size < 1:
            _msg = "No statistics available. Run the simulation first."
            raise ValueError(_msg)

        # Build summary dictionary from individual attributes
        self._summary = {
            "mean": self.mean,
            "median": self.median,
            "dev": self.dev,
            "min": self.min,
            "max": self.max,
            "count": self.count
        }
        return self._summary

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values."""
        # Reset parent class attributes (Foundation)
        super().clear()
        self._sym = f"MC_{{\\Pi_{{{self._idx}}}}}"

        # Reset BoundsSpecs attributes
        BoundsSpecs.clear(self)

        # Reset MonteCarlo-specific attributes
        self._cat = SimulationMode.DIST.value
        self._coefficient = Coefficient()
        self._pi_expr = None
        self._sym_func = None
        self._exe_func = None
        self._variables = {}
        self._symbols = {}
        self._aliases = {}
        self._latex_to_py = {}
        self._py_to_latex = {}
        self._var_symbols = []
        self._experiments = -1
        self._distributions = {}
        self._dependencies = {}
        self._simul_cache = {}
        self._data = {}
        self._results = np.array([], dtype=np.float64)

        # Reset statistics with MonteCarlo-specific defaults
        self._reset_statistics()

    # ========================================================================
    # Serialization
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert simulation to dictionary representation."""
        result = {}

        # Get all dataclass fields
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, attr_name)

            # Handle numpy arrays
            if isinstance(attr_value, np.ndarray):
                attr_value = attr_value.tolist() if attr_value.size > 0 else []
            # Handle Coefficient object
            elif isinstance(attr_value, Coefficient):
                attr_value = attr_value.to_dict()
            # Handle Variable dictionaries
            elif isinstance(attr_value, dict) and attr_value:
                first_val = next(iter(attr_value.values()), None)
                if isinstance(first_val, Variable):
                    attr_value = {k: v.to_dict() for k, v in attr_value.items()}
                # Handle sympy Symbol dictionaries - skip them
                elif hasattr(first_val, '__module__') and first_val.__module__.startswith('sympy'):
                    continue
            # Handle SymPy expressions
            elif hasattr(attr_value, '__module__') and hasattr(attr_value, '__module__') and str(type(attr_value).__module__).startswith('sympy'):
                attr_value = str(attr_value)

            # Skip callables (can't be serialized)
            if callable(attr_value) and not isinstance(attr_value, type):
                continue

            # Remove leading underscore from private attributes
            clean_name = attr_name[1:] if attr_name.startswith("_") else attr_name
            result[clean_name] = attr_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonteCarlo":
        """*from_dict()* Create simulation from dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary representation.

        Returns:
            MonteCarlo: New simulation instance.
        """
        # Get all valid field names from the dataclass (only init=True fields)
        init_fields = {f.name for f in fields(cls) if f.init}
        non_init_fields = {f.name for f in fields(cls) if not f.init}

        # Map keys without underscores to keys with underscores
        mapped_data = {}
        post_init_data = {}

        for key, value in data.items():
            # Handle special conversions for Coefficient
            if key == "coefficient" and isinstance(value, dict):
                mapped_data["_coefficient"] = Coefficient.from_dict(value)
                continue
            # Handle dictionary of Variables
            elif key == "variables" and isinstance(value, dict):
                mapped_data["_variables"] = {
                    k: Variable.from_dict(v) if isinstance(v, dict) else v
                    for k, v in value.items()
                }
                continue
            # Handle numpy arrays
            elif key in ["inputs", "results"] and isinstance(value, list):
                field_key = f"_{key}" if key == "results" else key
                mapped_data[field_key] = np.array(value, dtype=np.float64)
                continue
            # Handle special key mapping for iterations -> experiments
            elif key == "iterations":
                mapped_data["_experiments"] = value
                continue

            # Try the key as-is first (handles both _idx and name)
            if key in init_fields:
                mapped_data[key] = value
            # Try adding underscore prefix (handles idx -> _idx)
            elif f"_{key}" in init_fields:
                mapped_data[f"_{key}"] = value
            # Try removing underscore prefix (handles _name -> name if needed)
            elif key.startswith("_") and key[1:] in init_fields:
                mapped_data[key[1:]] = value
            # Check if it's a non-init field (set after creation)
            elif key in non_init_fields or f"_{key}" in non_init_fields:
                field_key = key if key in non_init_fields else f"_{key}"
                post_init_data[field_key] = value
            else:
                # Skip unknown keys
                continue

        # Create instance with init fields
        instance = cls(**mapped_data)

        # Set non-init fields directly
        for key, value in post_init_data.items():
            setattr(instance, key, value)

        # Recalculate statistics if results exist
        if instance._results.size > 0:
            instance._calculate_statistics()

        return instance
