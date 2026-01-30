# -*- coding: utf-8 -*-
"""
Module scenario.py
===========================================

Module for sensitivity analysis in *PyDASA*.

This module provides the Sensitivity class for performing sensitivity analysis on dimensional coefficients derived from dimensional analysis.

Classes:

    **Sensitivity**: Performs sensitivity analysis on dimensional coefficients in *PyDASA*.

*IMPORTANT:* Based on the theory from:
    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Any, Callable, Union

# Third-party modules
import numpy as np
import sympy as sp
from sympy import diff, lambdify    # , Symbol, symbols

from SALib.sample.fast_sampler import sample
from SALib.analyze.fast import analyze

# Import validation base classes
from pydasa.core.basic import Foundation

# Import validation decorators
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_choices
from pydasa.validations.decorators import validate_pattern
from pydasa.validations.decorators import validate_custom
from pydasa.validations.decorators import validate_dict_types
from pydasa.validations.decorators import validate_emptiness
from pydasa.validations.decorators import validate_index

# Import related classes
from pydasa.dimensional.vaschy import Schema
from pydasa.dimensional.buckingham import Coefficient
from pydasa.elements.parameter import Variable
from pydasa.core.setup import AnaliticMode

# Import utils
from pydasa.serialization.parser import parse_latex
from pydasa.serialization.parser import create_latex_mapping
from pydasa.serialization.parser import latex_to_python

# Import configuration
from pydasa.core.setup import PYDASA_CFG
from pydasa.validations.patterns import LATEX_RE


@dataclass
class Sensitivity(Foundation):
    # FIXME clean code, some vars and types are inconsistent
    """**Sensitivity** class for analyzing variable impacts in *PyDASA*.

    Performs sensitivity analysis on dimensionless coefficients to determine which variables have the most significant impact on the system behavior.

    Args:
        Foundation: Foundation class for validation of symbols and frameworks.

    Attributes:
        # Identification and Classification
        name (str): User-friendly name of the sensitivity analysis.
        description (str): Brief summary of the sensitivity analysis.
        _idx (int): Index/precedence of the sensitivity analysis.
        _sym (str): Symbol representation (LaTeX or alphanumeric).
        _alias (str): Python-compatible alias for use in code.
        _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).
        _cat (str): Category of analysis (SYM, NUM).

        # Expression Management
        _pi_expr (str): LaTeX expression to analyze.
        _sym_func (Callable): Sympy function of the sensitivity.
        _exe_func (Callable): Executable function for numerical evaluation.
        _variables (Dict[str, Variable]): Variable symbols in the expression.
        _var_names (List[str]): List of variable names extracted from the expression.
        _schema (Schema): Dimensional framework schema.
        _coefficient (Coefficient): Specifications of the dimensionless coefficient to analyse.
        _symbols (Dict[str, Any]): Python symbols for the variables.
        _aliases (Dict[str, Any]): Variable aliases for use in code.

        # Analysis Configuration
        _var_bounds (List[List[float]]): Min/max bounds for each variable.
        _var_values (Dict[str, float]): Values for symbolic analysis.
        _var_ranges (np.ndarray): Sample value range for numerical analysis.
        _var_domains (np.ndarray): Sample domain for numerical analysis.
        _experiments (int): Number of samples for analysis.

        # Results
        _results (Dict[str, Any]): Analysis results.
    """

    # Category attribute
    # :attr: _cat
    _cat: str = AnaliticMode.SYM.value
    """Category of sensitivity analysis (SYM, NUM)."""

    # Expression properties
    # :attr: _pi_expr
    _pi_expr: Optional[str] = None
    """LaTeX expression to analyze."""

    # :attr: _sym_func
    _sym_func: Optional[sp.Expr] = None
    """Sympy expression of the sensitivity (symbolic form)."""

    # :attr: _exe_func
    _exe_func: Optional[Union[Callable, Dict[str, Callable]]] = None
    """Executable function(s) for numerical evaluation (compiled from symbolic form)."""

    # :attr: _variables
    _variables: Dict[str, Variable] = field(default_factory=dict)
    """Variable symbols in the expression."""

    # :attr: _var_names
    _var_names: List[str] = field(default_factory=list)
    """List of variable names extracted from the expression (ordered)."""

    # :attr: _schema
    _schema: Schema = field(default_factory=Schema)
    """Dimensional framework schema for FDU management."""

    # :attr: _coefficient
    _coefficient: Optional[Coefficient] = None
    """Specifications of the dimensionless coefficient to analyse."""

    # :attr: _symbols
    _symbols: Dict[sp.Symbol, sp.Symbol] = field(default_factory=dict)
    """Python symbols for the variables."""

    # :attr: _aliases
    _aliases: Dict[str, sp.Symbol] = field(default_factory=dict)
    """Variable aliases for use in code."""

    # :attr: _latex_to_py
    _latex_to_py: Dict[str, str] = field(default_factory=dict)
    """Mapping from LaTeX symbols to Python-compatible names."""

    # :attr: _py_to_latex
    _py_to_latex: Dict[str, str] = field(default_factory=dict)
    """Mapping from Python-compatible names to LaTeX symbols."""

    # Analysis configuration
    # :attr: _var_bounds
    _var_bounds: List[List[float]] = field(default_factory=list)
    """Min/max bounds for each variable."""

    # :attr: _var_values
    _var_values: Dict[str, float] = field(default_factory=dict)
    """Values for symbolic analysis."""

    # :attr: _var_domains
    _var_domains: Optional[np.ndarray] = None
    """Sample domain (inputs) for numerical analysis."""

    # :attr: _var_ranges
    _var_ranges: Optional[np.ndarray] = None
    """Sample value range (results) for numerical analysis."""

    # :attr: _experiments
    _experiments: int = -1
    """Number of experiments/samples for analysis."""

    # Results
    # :attr: _results
    _results: Dict[str, Any] = field(default_factory=dict)
    """Analysis results."""

    def __post_init__(self) -> None:
        """*__post_init__()* Initializes the sensitivity analysis. Validates basic properties, sets default values, and processes the expression if provided.
        """
        # Initialize from base class
        super().__post_init__()

        # Set default symbol if not specified
        if not self._sym:
            self._sym = f"SENS_{{\\Pi_{{{self._idx}}}}}" if self._idx >= 0 else "SENS_{\\Pi_{-1}}"
        # Set default Python alias if not specified
        if not self._alias:
            self._alias = latex_to_python(self._sym)

        # Set name and description if not already set
        if not self.name:
            self.name = f"{self._sym} Sensitivity"
        if not self.description:
            self.description = f"Sensitivity analysis for {self._sym}"

        if self._pi_expr:
            # Parse the expression
            self._parse_expression(self._pi_expr)

    def _validate_sym_expr(self, val: Any) -> None:
        """*_validate_sym_expr()* Check that the symbolic expression is a SymPy expression.

        Args:
            val (Any): Value to validate.

        Raises:
            ValueError: If value is not a valid SymPy expression.
        """
        if not isinstance(val, sp.Expr):
            _msg = "'sym_func' must be a SymPy expression, "
            _msg += f"got {type(val).__name__}"
            raise ValueError(_msg)

    def _validate_exec_func(self, val: Any) -> None:
        """Validate executable function is callable or dict of callables."""
        if callable(val):
            return
        if isinstance(val, dict):
            if not all(callable(v) for v in val.values()):
                raise ValueError("All dictionary values must be callable")
            return
        _msg = "'exe_func' must be Callable or Dict[str, Callable], "
        _msg += f"got {type(val).__name__}"
        raise ValueError(_msg)

    def _validate_analysis_ready(self) -> None:
        """*_validate_analysis_ready()* Checks if the analysis can be performed.

        Raises:
            ValueError: If the variables are missing.
            ValueError: If the python-compatible variables are missing.
            ValueError: If the symbolic expression is missing.
        """
        if not self._var_names:
            raise ValueError("No variables found in the expression.")
        if not self._aliases:
            raise ValueError("No Python aliases found for variables.")
        if not self._sym_func:
            raise ValueError("No expression has been defined for analysis.")

    def set_coefficient(self, coef: Coefficient) -> None:
        """*set_coefficient()* Configure analysis from a coefficient.

        Args:
            coef (Coefficient): Dimensionless coefficient to analyze.

        Raises:
            ValueError: If the coefficient doesn't have a valid expression.
        """
        if not coef.pi_expr:
            raise ValueError("Coefficient does not have a valid expression.")

        # Set expression
        self._pi_expr = coef.pi_expr
        # parse coefficient expresion
        if coef._pi_expr:
            self._parse_expression(self._pi_expr)

    def _parse_expression(self, expr: str) -> None:
        """*_parse_expression()* Parse the LaTeX expression into a sympy function.

        Args:
            expr (str): LaTeX expression to parse.

        Raises:
            ValueError: If the expression cannot be parsed.
            TypeError: If parsed result is not a valid SymPy expression.
        """
        try:
            # Parse the expression
            parsed_expr = parse_latex(expr)

            # Validate it's actually a SymPy expression
            if parsed_expr is None:
                _msg = "parse_latex returned 'None'."
                raise ValueError(_msg)

            if not isinstance(parsed_expr, sp.Expr):
                _msg = f"Parsed expression is not a SymPy expression: {type(parsed_expr).__name__}."
                raise TypeError(_msg)

            # Create symbol mapping
            maps = create_latex_mapping(expr)
            self._symbols = maps[0]
            self._aliases = maps[1]
            self._latex_to_py = maps[2]
            self._py_to_latex = maps[3]

            # Work with local variable (guaranteed sp.Expr type)
            sym_func: sp.Expr = parsed_expr

            # Substitute LaTeX symbols with Python symbols
            for latex_sym, py_sym in self._symbols.items():
                result = sym_func.subs(latex_sym, py_sym)
                # Ensure result is still an Expr
                if isinstance(result, sp.Expr):
                    sym_func = result
                else:
                    # Convert back to Expr if needed
                    sym_func = sp.sympify(result)

            # Assign the processed expression to the attribute
            self._sym_func = sym_func

            # Get Python variable names and store in _var_names list
            fsyms = sym_func.free_symbols
            self._var_names = sorted([str(s) for s in fsyms])

            # """
            # # OLD code, first version, keep for reference!!!
            # self.results = {
            #     var: lambdify(self._variables, diff(self._sym_fun, var), "numpy")(
            #         *[vals[v] for v in self.variables]
            #     )
            #     for var in self._variables
            # }
            # """
        except (ValueError, TypeError):
            raise  # Re-raise validation errors
        except Exception as e:
            _msg = f"Failed to parse expression: {str(e)}"
            raise ValueError(_msg) from e

    def analyze_symbolically(self,
                             vals: Dict[str, float]) -> Dict[str, float]:
        """*analyze_symbolically()* Perform symbolic sensitivity analysis.

        Args:
            vals (Dict[str, float]): Dictionary mapping variable names to values.

        Returns:
            Dict[str, float]: Sensitivity results for each variable.
        """
        # Validate analysis readiness
        self._validate_analysis_ready()

        # save variable values for the analysis
        self.var_values = vals

        # Check that all required variables are provided
        var_lt = [str(v) for v in self._latex_to_py]
        missing_vars = set(var_lt) - set(list(vals.keys()))
        if missing_vars:
            _msg = f"Missing values for variables: {missing_vars}"
            raise ValueError(_msg)

        # trying symbolic coefficient sensitivity analysis
        try:
            py_to_latex = self._py_to_latex
            results = dict()
            functions = dict()
            if self._var_names:
                for var in self._var_names:
                    # Create lambdify function using Python symbols
                    expr = diff(self._sym_func, var)
                    aliases = [self._aliases[v] for v in self._var_names]
                    # self._exe_func = lambdify(aliases, expr, "numpy")
                    func = lambdify(aliases, expr, "numpy")
                    functions[py_to_latex[var]] = func

                    # Convert back to LaTeX variables for result keys
                    val_args = [vals[py_to_latex[v]] for v in self._var_names]
                    res = functions[py_to_latex[var]](*val_args)
                    results[py_to_latex[var]] = res

            self._exe_func = functions
            self._results = results
            return self._results

        except Exception as e:
            coef = f"{self._sym} = ({self._pi_expr})"
            _msg = f"Error calculating sensitivity for {coef}: {str(e)}"
            raise ValueError(_msg)

    def analyze_numerically(self,
                            vals: List[str],
                            bounds: List[List[float]],
                            iters: int = -1) -> Dict[str, Any]:
        """*analyze_numerically()* Perform numerical sensitivity analysis.

        Args:
            vals (List[str]): List of variable names to analyze.
            bounds (List[List[float]]): Bounds for each variable [min, max].
            iters (int, optional): Number of iterations to use. Defaults to -1.

        Returns:
            Dict[str, Any]: Detailed sensitivity analysis results.
        """
        # Validate analysis readiness
        self._validate_analysis_ready()

        # trying numeric coefficient sensitivity analysis
        try:
            # Validate bounds length matches number of variables
            if len(bounds) != len(self._var_names):
                _msg = f"Expected {len(self._var_names)} "
                _msg += f"bounds (one per variable), got {len(bounds)}"
                raise ValueError(_msg)

            # Set number of samples
            self.experiments = iters
            # Store bounds
            self.var_bounds = bounds

            results: Dict[str, Any] = dict()

            if self._var_names:
                # Set up problem definition for SALib
                problem = {
                    "num_vars": len(vals),
                    "names": self._var_names,
                    "bounds": bounds,
                }

                # Generate samples (domain)
                self._var_domains = sample(problem, self._experiments)
                _len = len(self._var_names)
                self._var_domains = self._var_domains.reshape(-1, _len)

                # Create lambdify function using Python symbols
                aliases = [self._aliases[v] for v in self._var_names]
                func = lambdify(aliases, self._sym_func, "numpy")

                # Store as single callable (overwrite any previous dict)
                self._exe_func = func

                # Type guard: Ensure it's callable before using
                if not callable(self._exe_func):
                    raise TypeError("Failed to create executable function")

                # Evaluate function at sample points
                # using local variable to satisfy type checker
                exe_func = self._exe_func
                # Local variable guaranteed to be Callable
                Y = np.apply_along_axis(lambda v: exe_func(*v),
                                        1,
                                        self._var_domains)
                self._var_ranges = Y.reshape(-1, 1)

                # Perform FAST (Fourier Amplitude Sensitivity Test) analysis
                results = analyze(problem, Y)

                # Convert back to LaTeX variables for result keys
                if "names" in results:
                    py_to_latex = self._py_to_latex
                    results["names"] = [py_to_latex.get(v, v) for v in results["names"]]

            self._results = results
            return self._results

        except Exception as e:
            coef = f"{self._sym} = ({self._pi_expr})"
            _msg = f"Error calculating sensitivity for {coef}: {str(e)}"
            raise ValueError(_msg)

    # Property getters and setters

    @property
    def cat(self) -> str:
        """*cat* Get the analysis category.

        Returns:
            str: Category (SYM, NUM).
        """
        return self._cat

    @cat.setter
    @validate_type(str, allow_none=False)
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
    def pi_expr(self) -> Optional[str]:
        """*pi_expr* Get the expression to analyze.

        Returns:
            Optional[str]: LaTeX expression.
        """
        return self._pi_expr

    @pi_expr.setter
    @validate_type(str)
    @validate_emptiness()
    @validate_pattern(LATEX_RE, allow_alnum=True)
    def pi_expr(self, val: str) -> None:
        """*pi_expr* Set the expression to analyze.

        Args:
            val (str): LaTeX expression.

        Raises:
            ValueError: If expression is invalid.
        """
        # Update expression
        self._pi_expr = val

        # Parse expression
        self._parse_expression(self._pi_expr)

    @property
    def sym_func(self) -> Optional[sp.Expr]:
        """*sym_func* Get the symbolic expression.

        Returns:
            Optional[sp.Expr]: SymPy symbolic expression.
        """
        return self._sym_func

    @sym_func.setter
    @validate_type(sp.Expr, allow_none=False)
    @validate_custom(lambda self, val: self._validate_sym_expr(val))
    def sym_func(self, val: sp.Expr) -> None:
        """*sym_func* Set the symbolic expression.

        Args:
            val (sp.Expr): SymPy symbolic expression.

        Raises:
            ValueError: If value is not a valid SymPy expression.
        """
        self._sym_func = val

    @property
    def exe_func(self) -> Optional[Union[Callable, Dict[str, Callable]]]:
        """*exe_func* Get the executable function.

        Returns:
            Optional[Union[Callable, Dict[str, Callable]]]: Executable function for numerical evaluation.
        """
        return self._exe_func

    @exe_func.setter
    @validate_custom(lambda self, val: self._validate_exec_func(val))
    def exe_func(self, val: Union[Callable, Dict[str, Callable]]) -> None:
        """*exe_func* Set the executable function(s).

        Args:
            val (Union[Callable, Dict[str, Callable]]): Executable function or
                dictionary of functions.

        Raises:
            ValueError: If value is not a callable or dict of callables.
        """
        self._exe_func = val

    @property
    def variables(self) -> Dict[str, Variable]:
        """*variables* Get the variable symbols dictionary.

        Returns:
            Dict[str, Variable]: Variables symbols dictionary.
        """
        return self._variables

    @variables.setter
    @validate_type(dict, allow_none=False)
    @validate_emptiness()
    @validate_dict_types(str, Variable)
    def variables(self, val: Dict[str, Variable]) -> None:
        """*variables* Set the variable symbols dictionary.

        Args:
            val (Dict[str, Variable]): Variables symbols dictionary.

        Raises:
            ValueError: If variables dictionary is invalid.
        """
        self._variables = val

    @property
    def schema(self) -> Schema:
        """*schema* Get the dimensional schema.

        Returns:
            Schema: Current dimensional schema.
        """
        return self._schema

    @schema.setter
    @validate_type(Schema, allow_none=False)
    def schema(self, val: Schema) -> None:
        """*schema* Set the dimensional schema.

        Args:
            val (Schema): New dimensional schema.

        Raises:
            ValueError: If input is not a Schema instance.
        """
        # Update framework and global configuration
        self._schema = val

    @property
    def symbols(self) -> Dict[sp.Symbol, sp.Symbol]:
        """*symbols* Get the Python symbols for the variables.

        Returns:
            Dict[sp.Symbol, sp.Symbol]: Dictionary mapping variable names to sympy symbols.
        """
        return self._symbols

    @property
    def aliases(self) -> Dict[str, sp.Symbol]:
        """*aliases* Get the Python aliases for the variables.

        Returns:
            Dict[str, sp.Symbol]: Python-compatible variable names.
        """
        return self._aliases

    @property
    def var_names(self) -> List[str]:
        """*var_names* Get the list of variable names extracted from the expression.

        Returns:
            List[str]: Ordered list of variable names.
        """
        return self._var_names.copy()

    @property
    def coefficient(self) -> Optional[Coefficient]:
        """*coefficient* Get the dimensionless coefficient specification.

        Returns:
            Optional[Coefficient]: Coefficient specification.
        """
        return self._coefficient

    @coefficient.setter
    @validate_type(Coefficient, allow_none=True)
    def coefficient(self, val: Optional[Coefficient]) -> None:
        """*coefficient* Set the dimensionless coefficient specification.

        Args:
            val (Optional[Coefficient]): Coefficient specification.

        Raises:
            ValueError: If value is not a Coefficient instance.
        """
        self._coefficient = val

    @property
    def latex_to_py(self) -> Dict[str, str]:
        """*latex_to_py* Get the mapping from LaTeX symbols to Python compatible names.

        Returns:
            Dict[str, str]: LaTeX to Python symbol mapping.
        """
        return self._latex_to_py.copy()

    @property
    def py_to_latex(self) -> Dict[str, str]:
        """*py_to_latex* Get the mapping from Python compatible names to LaTeX symbols.

        Returns:
            Dict[str, str]: Python to LaTeX symbol mapping.
        """
        return self._py_to_latex.copy()

    @property
    def var_bounds(self) -> List[List[float]]:
        """*var_bounds* Get the min/max bounds for each variable.

        Returns:
            List[List[float]]: Bounds for each variable.
        """
        return self._var_bounds.copy()

    @var_bounds.setter
    @validate_type(list, allow_none=False)
    @validate_emptiness()
    def var_bounds(self, val: List[List[float]]) -> None:
        """*var_bounds* Set the min/max bounds for each variable.

        Args:
            val (List[List[float]]): Bounds for each variable [min, max].

        Raises:
            ValueError: If bounds list is invalid or empty.
        """
        self._var_bounds = val

    @property
    def var_values(self) -> Dict[str, float]:
        """*var_values* Get the values for symbolic analysis.

        Returns:
            Dict[str, float]: Variable values for symbolic analysis.
        """
        return self._var_values.copy()

    @var_values.setter
    @validate_type(dict, allow_none=False)
    @validate_emptiness()
    def var_values(self, val: Dict[str, float]) -> None:
        """*var_values* Set the values for symbolic analysis.

        Args:
            val (Dict[str, float]): Variable values for symbolic analysis.

        Raises:
            ValueError: If values dictionary is invalid or empty.
        """
        self._var_values = val

    @property
    def var_domains(self) -> Optional[np.ndarray]:
        """*var_domains* Get the sample domain for numerical analysis.

        Returns:
            Optional[np.ndarray]: Sample domain (inputs) or None if not computed.
        """
        if self._var_domains is None:
            return None
        return self._var_domains.copy()

    @property
    def var_ranges(self) -> Optional[np.ndarray]:
        """*var_ranges* Get the sample value range for numerical analysis.

        Returns:
            Optional[np.ndarray]: Sample value range (results) or None if not computed.
        """
        if self._var_ranges is None:
            return None
        return self._var_ranges.copy()

    @property
    def results(self) -> Dict[str, Any]:
        """*results* Get the analysis results.

        Returns:
            Dict[str, Any]: Analysis results dictionary.
        """
        return self._results.copy()

    @property
    def experiments(self) -> int:
        """*experiments* Get the number of experiments for analysis.

        Returns:
            int: Number of experiments.
        """
        return self._experiments

    @experiments.setter
    @validate_type(int, allow_none=False)
    @validate_index(allow_zero=False)
    def experiments(self, val: int) -> None:
        """*experiments* Set the number of experiments for analysis.

        Args:
            val (int): Number of experiments (must be >= 1).

        Raises:
            ValueError: If experiments value is invalid or less than 1.
        """
        self._experiments = val

    def clear(self) -> None:
        """*clear()* Reset all attributes to default values.

        Resets all sensitivity analysis properties to their initial state.
        """
        # Reset parent class attributes (Foundation)
        super().clear()
        self._sym = f"SENS_{{\\Pi_{{{self._idx}}}}}"

        # Reset sensitivity-specific attributes
        self._cat = AnaliticMode.SYM.value
        self._pi_expr = None
        self._sym_func = None
        self._exe_func = None
        self._variables = {}
        self._var_names = []
        self._schema = Schema()
        self._coefficient = None
        self._symbols = {}
        self._aliases = {}
        self._latex_to_py = {}
        self._py_to_latex = {}
        self._var_bounds = []
        self._var_values = {}
        self._var_domains = None
        self._var_ranges = None
        self._experiments = -1
        self._results = {}

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert sensitivity analysis to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of sensitivity analysis.
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

            # Skip SymPy objects (not JSON serializable)
            if isinstance(attr_value, sp.Expr):
                # Convert to string representation
                attr_value = str(attr_value)
            elif isinstance(attr_value, dict):
                # Handle dictionaries with SymPy keys/values
                cleaned_dict = {}
                for k, v in attr_value.items():
                    # Convert SymPy keys to strings
                    key = str(k) if isinstance(k, sp.Basic) else k
                    # Convert SymPy values to strings
                    value = str(v) if isinstance(v, sp.Basic) else v
                    cleaned_dict[key] = value
                attr_value = cleaned_dict

            # Skip callables (can't be serialized)
            if callable(attr_value) and not isinstance(attr_value, type):
                continue

            # Skip Schema objects (complex nested structure)
            if attr_name == "_schema":
                continue

            # Remove leading underscore from private attributes
            if attr_name.startswith("_"):
                clean_name = attr_name[1:]  # Remove first character
            else:
                clean_name = attr_name

            result[clean_name] = attr_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Sensitivity:
        """*from_dict()* Create sensitivity analysis from dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary representation of sensitivity analysis.

        Returns:
            Sensitivity: New sensitivity analysis instance.
        """
        # Get all valid field names from the dataclass
        field_names = {f.name for f in fields(cls)}

        # Map keys without underscores to keys with underscores
        mapped_data = {}

        for key, value in data.items():
            # Try the key as-is first (handles both _idx and name)
            if key in field_names:
                mapped_data[key] = value
            # Try adding underscore prefix (handles idx -> _idx)
            elif f"_{key}" in field_names:
                mapped_data[f"_{key}"] = value
            # Try removing underscore prefix (handles _name -> name if needed)
            elif key.startswith("_") and key[1:] in field_names:
                mapped_data[key[1:]] = value
            else:
                # Use as-is for unknown keys (will be validated by dataclass)
                mapped_data[key] = value

        # Convert lists back to numpy arrays for domain/range attributes
        for array_key in ["var_domains", "_var_domains", "var_ranges", "_var_ranges"]:
            if array_key in mapped_data and isinstance(mapped_data[array_key], list):
                mapped_data[array_key] = np.array(mapped_data[array_key])

        return cls(**mapped_data)
