# -*- coding: utf-8 -*-
"""
Module model.py
============================================

Module for **Matrix** to perform Dimensional Analysis in *PyDASA*.

This module provides the Matrix class which implements matrix-based dimensional analysis following the Buckingham Pi theorem methodology.

Classes:
    **Matrix**: Represents a dimensional matrix for performing dimensional analysis, including methods for matrix creation, solving, and coefficient generation.

*IMPORTANT:* Based on the theory from:
    H. Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""

# native python modules
# forward references + postpone eval type hints
from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import List, Dict, Optional, Any, Union
import re

# third-party modules for numeric and symbolic computation
import numpy as np
import sympy as sp
from numpy.typing import NDArray

# custom modules for dimensional analysis imports
from pydasa.core.basic import Foundation
from pydasa.core.setup import Frameworks
from pydasa.core.setup import VarCardinality
from pydasa.core.setup import CoefCardinality
from pydasa.elements.parameter import Variable
from pydasa.dimensional.vaschy import Schema
from pydasa.dimensional.buckingham import Coefficient
# global variables for configuration
from pydasa.core.setup import PYDASA_CFG
from pydasa.validations.patterns import LATEX_RE
from pydasa.validations.patterns import PI_COEF_RE
# useful decorators for validations
from pydasa.validations.decorators import validate_type
from pydasa.validations.decorators import validate_index
from pydasa.validations.decorators import validate_choices
from pydasa.validations.decorators import validate_pattern
from pydasa.validations.decorators import validate_emptiness
from pydasa.validations.decorators import validate_dict_types
# parser functions for dimensional expressions
from pydasa.serialization.parser import parse_dim_expr
from pydasa.serialization.parser import format_numeric_constant

# Matrix global constants
MAX_OUT: int = 1
"""Maximum number of output variables allowed."""

MAX_IN: int = 10
"""Maximum number of input variables allowed."""


@dataclass
class Matrix(Foundation):
    """**Matrix** for Dimensional Analysis in *PyDASA*. Manages the dimensional matrix for performing analysis using the Buckingham Pi theorem methodology.

    Args:
        Foundation: Foundation class for validation of symbols and frameworks.

    Attributes:
        # Core Identification
        name (str): User-friendly name of the dimensional model.
        description (str): Brief summary of the dimensional model.
        _idx (int): Index/precedence of the dimensional model.
        _sym (str): Symbol representation (LaTeX or alphanumeric).
        _alias (str): Python-compatible alias for use in code.
        _fwk (str): Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM).

        # FDU Schema Management
        _schema (Schema): Dimensional domain managing FDUs.
        working_fdus (List[str]): Active FDUs used in current analysis.

        # Variable Management
        _variables (Dict[str, Variable]): All variables in the model.
        _relevant_lt (Dict[str, Variable]): Relevant variables for analysis.
        _output (Optional[Variable]): Output variable for analysis.

        # Variable Statistics
        _n_var (int): Total number of variables.
        _n_relevant (int): Number of relevant variables.
        _n_in (int): Number of input variables.
        _n_out (int): Number of output variables.
        _n_ctrl (int): Number of control variables.

        # Matrix Representations
        _dim_mtx (Optional[NDArray[np.float64]]): Dimensional matrix (FDUs × Variables).
        _dim_mtx_trans (Optional[NDArray[np.float64]]): Transposed dimensional matrix.
        _sym_mtx (Optional[sp.Matrix]): SymPy matrix for symbolic computation.
        _rref_mtx (Optional[NDArray[np.float64]]): Row-Reduced Echelon Form matrix.

        # Analysis Results
        _pivot_cols (List[int]): Pivot columns in the RREF matrix.
        _coefficients (Dict[str, Coefficient]): Dimensionless Pi coefficients.
    """

    # ========================================================================
    # Core Identification
    # ========================================================================
    # :attr: _name
    _name: str = "Dimensional Matrix"
    """User-friendly name of the dimensional matrix."""

    # :attr: description
    description: str = ""
    """Brief summary of the dimensional matrix and its purpose."""

    # :attr: _idx
    _idx: int = -1
    """Index/precedence of the dimensional model."""

    # :attr: _sym
    _sym: str = ""
    """Symbol representation (LaTeX or alphanumeric)."""

    # :attr: _alias
    _alias: str = ""
    """Python-compatible alias for use in code."""

    # :attr: _fwk
    _fwk: str = Frameworks.PHYSICAL.value
    """Frameworks context (PHYSICAL, COMPUTATION, SOFTWARE, CUSTOM)."""

    # ========================================================================
    # Frameworks Management
    # ========================================================================

    # :attr: _schema
    _schema: Schema = field(default_factory=Schema)
    """Dimensional domain managing Fundamental Dimensional Units (FDUs)."""

    # :attr: working_fdus
    working_fdus: List[str] = field(default_factory=list)
    """List of active FDU symbols used in the current analysis."""

    # ========================================================================
    # Variable Management
    # ========================================================================

    # :attr: _variables
    _variables: Dict[str, Variable] = field(default_factory=dict)
    """Dictionary of all parameters/variables in the model.

    Keys are variable symbols (str), values are Variable instances.
    """

    # :attr: _relevant_lt
    _relevant_lt: Dict[str, Variable] = field(default_factory=dict)
    """Dictionary of relevant parameters/variables for dimensional analysis.

    Filtered subset of _variables where Variable.relevant == True. Keys are variable symbols (str), values are Variable instances.

    NOTE: called 'relevant list' by convention.
    """

    # :attr: _output
    _output: Optional[Variable] = None
    """The single output variable for the dimensional analysis.

    Must be a variable with cat == "OUT".
    """

    # ========================================================================
    # Variable Statistics
    # ========================================================================

    # :attr: _n_var
    _n_var: int = 0
    """Total number of variables in the model."""

    # :attr: _n_relevant
    _n_relevant: int = 0
    """Number of variables marked as relevant for analysis."""

    # :attr: _n_in
    _n_in: int = 0
    """Number of input variables (cat == "IN" and relevant == True)."""

    # :attr: _n_out
    _n_out: int = 0
    """Number of output variables (cat == "OUT" and relevant == True)."""

    # :attr: _n_ctrl
    _n_ctrl: int = 0
    """Number of control variables (cat == "CTRL" and relevant == True)."""

    # ========================================================================
    # Matrix Representations
    # ========================================================================

    # :attr: _dim_mtx
    # _dim_mtx: Optional[np.ndarray] = field(default_factory=lambda: np.array([]))
    _dim_mtx: Optional[NDArray[np.float64]] = None
    """Dimensional matrix as NumPy array.

    Shape: (n_fdus, n_relevant_vars)
    Each column represents a variable's dimensional formula.
    Each row represents an FDU's exponent across all variables.
    """

    # :attr: _dim_mtx_trans
    _dim_mtx_trans: Optional[NDArray[np.float64]] = None
    """Transposed dimensional matrix.

    Shape: (n_relevant_vars, n_fdus)
    Transpose of _dim_mtx for alternative operations.
    """

    # :attr: _sym_mtx
    _sym_mtx: Optional[sp.Matrix] = field(default_factory=lambda: sp.Matrix([]))
    """SymPy Matrix representation for symbolic computation.

    Used for RREF calculation and nullspace computation.
    Equivalent to _dim_mtx but in SymPy format.
    """

    # :attr: _rref_mtx
    _rref_mtx: Optional[NDArray[np.float64]] = None
    """Row-Reduced Echelon Form (RREF) of the dimensional matrix.

    Result of Gaussian elimination on _sym_mtx.
    Used to identify pivot columns and compute nullspace.
    """

    # :attr: _nullspace
    _nullspace: List[Union[np.ndarray, sp.Matrix]] = field(default_factory=list)
    """List of nullspace vectors of the dimensional matrix.

    Can be list of arrays or list of sympy vectors"""

    # ========================================================================
    # Analysis Results
    # ========================================================================

    # :attr: _pivot_cols
    _pivot_cols: List[int] = field(default_factory=list)
    """Indices of pivot columns in the RREF matrix.

    Identifies which variables are dependent (pivot) vs. independent (free).
    """

    # :attr: _coefficients
    _coefficients: Dict[str, Coefficient] = field(default_factory=dict)
    """Dictionary of dimensionless Pi coefficients.

    Keys are coefficient symbols (e.g., "\\Pi_{0}"), values are Coefficient instances.
    Generated from the nullspace of the dimensional matrix.
    """

    # ========================================================================
    # Initialization
    # ========================================================================

    def __post_init__(self) -> None:
        """*__post_init__()* Initialize the dimensional matrix.

        Validates variables, sets up the framework, identifies relevant variables, and prepares for dimensional analysis.
        """
        # Initialize base class
        super().__post_init__()

        # Set default symbol if not specified
        if not self._sym:
            self._sym = f"DM_{{{self._idx}}}" if self._idx >= 0 else "DM_{-1}"

        # Process variables if provided
        if self._variables:
            self._prepare_analysis()

        # Ensure proper types
        if not isinstance(self._dim_mtx, np.ndarray):
            self._dim_mtx = np.array([], dtype=float)

        if not isinstance(self._sym_mtx, sp.Matrix):
            self._sym_mtx = sp.Matrix([])

    # ========================================================================
    # Preparation Methods
    # ========================================================================

    def _prepare_analysis(self) -> None:
        """*_prepare_analysis()* Prepare the model for dimensional analysis.

        Sets up relevant variables, computes model statistics, identifies the output variable, and extracts working FDUs.

        Raises:
            ValueError: If variable configuration is invalid.
        """
        # Update variable statistics
        self._update_variable_stats()

        # Identify and sort relevant variables
        self._relevant_lt = {
            k: v for k, v in self._variables.items() if v.relevant
        }
        self._relevant_lt = self._sort_by_category(self._relevant_lt)

        # Find the output variable
        self._find_output_variable()

        # Extract working FDUs from relevant variables
        self.working_fdus = self._extract_fdus()

        # Handle CUSTOM framework
        if self._fwk == Frameworks.CUSTOM.value and self.working_fdus:
            _fwk = self._schema
            _w_fdus = self.working_fdus
            if not all(fdu in _fwk.fdu_symbols for fdu in _w_fdus):
                _msg = f"Invalid CUSTOM FDUs: {_w_fdus}. "
                _msg += f"Must be subset of: {_fwk.fdu_symbols}."
                raise ValueError(_msg)

    def _update_variable_stats(self) -> None:
        """*_update_variable_stats()* Update variable statistics.

        Computes the number of variables, inputs, outputs, and control variables. Validates the model constraints.

        Raises:
            ValueError: If model has invalid variable counts.
        """
        _vars = self._variables.values()

        # Count all variables
        self._n_var = len(_vars)
        self._n_relevant = len([v for v in _vars if v.relevant])

        # Count by category (only relevant ones)
        IN = VarCardinality.IN.value
        OUT = VarCardinality.OUT.value
        self._n_in = len([v for v in _vars if v.cat == IN and v.relevant])
        self._n_out = len([v for v in _vars if v.cat == OUT and v.relevant])
        self._n_ctrl = self._n_relevant - self._n_in - self._n_out

        # Validate output count
        if self._n_out == 0:
            _msg = "No output variable defined. At least one output variable"
            _msg += " (cat='OUT', relevant=True) is required."
            raise ValueError(_msg)

        if self._n_out > MAX_OUT:
            _msg = f"Invalid number of outputs: {self._n_out}. "
            _msg += f"Maximum allowed: {MAX_OUT}."
            raise ValueError(_msg)

        # Validate input count
        if self._n_in == 0:
            _msg = "No input variables defined. "
            _msg += "At least one input variable is required."
            raise ValueError(_msg)

        max_inputs = len(self._schema.fdu_symbols)
        if self._n_in > max_inputs:
            _msg = f"Too many input variables: {self._n_in}. "
            _msg += f"Maximum allowed: {max_inputs} (number of FDUs)."
            raise ValueError(_msg)

    def _sort_by_category(self,
                          vars_lt: Dict[str, Variable]) -> Dict[str, Variable]:
        """*_sort_by_category()* Sorts variables by category.

        Sorts variables in order: IN -> OUT -> CTRL. Updates variable indices to reflect sorted order.

        Args:
            vars_lt (Dict[str, Variable]): Dictionary of variables to sort.

        Returns:
            Dict[str, Variable]: Sorted dictionary of variables.
        """
        # Get category order from global config
        # cat_order = list(PYDASA_CFG.parameter_cardinality)
        cat_order = [c.value for c in PYDASA_CFG.parameter_cardinality]

        # Sort by category precedence
        sorted_items = sorted(vars_lt.items(),
                              key=lambda v: cat_order.index(v[1].cat))

        # # NOTE IA weird lambda function, check later!!!
        # sorted_items = sorted(vars_lt.items(),
        #                       key=lambda v: cat_order.index(v[1].cat) if v[1].cat in cat_order else len(cat_order))

        # Update indices and rebuild dictionary
        sorted_dict = {}
        for i, (k, v) in enumerate(sorted_items):
            v._idx = i
            sorted_dict[k] = v

        return sorted_dict

    def _find_output_variable(self) -> None:
        """*_find_output_variable()* Identifies the output variable.

        Finds the first variable with cat == "OUT" in the relevant list.
        """
        values = self._relevant_lt.values()
        self._output = next((v for v in values if v.cat == "OUT"), None)

    def _extract_fdus(self) -> List[str]:
        """*_extract_fdus()* Extracts FDUs from relevant variables.

        Scans all relevant variables' dimension strings to find which FDUs are actually used.

        Returns:
            List[str]: List of unique FDU symbols used, in precedence order.
        """
        # Collect all dimension strings
        var_dims = [v.std_dims for v in self._relevant_lt.values()]

        # Extract FDU symbols using regex
        fdus = [
            d for d in re.findall(self._schema.fdu_sym_regex, str(var_dims))
        ]

        # Remove duplicates while preserving order
        unique_fdus = list({fdus[i] for i in range(len(fdus))})

        return unique_fdus

    # ========================================================================
    # Matrix Operations
    # ========================================================================

    def create_matrix(self) -> None:
        """*create_matrix()* Builds the dimensional matrix.

        Creates the dimensional matrix by arranging variable dimensions as columns. Each row represents an FDU, each column a variable.

        Raises:
            ValueError: If no relevant variables exist.
            ValueError: If variables have invalid or missing dimensional columns.
        """
        if not self._relevant_lt:
            raise ValueError("No relevant variables to create matrix from.")

        # Validate that all variables have dimensional columns
        invalid_vars = []
        for var in self._relevant_lt.values():
            if not var._dim_col or len(var._dim_col) == 0:
                invalid_vars.append(f"{var._sym} (dims='{var._dims}')")

        if invalid_vars:
            _msg = "Variables with missing or empty dimensional columns detected:\n"
            _msg += "\n".join(f"  - {v}" for v in invalid_vars)
            _msg += "\n\nEnsure all relevant variables have valid '_dims' "
            _msg += "properties (e.g., 'L', 'M*L*T^-2', etc.) and not 'n.a.'"
            raise ValueError(_msg)

        # Get dimensions
        n_fdu = len(self._schema.fdu_symbols)
        n_var = len(self._relevant_lt)

        # Initialize empty matrix
        self._dim_mtx = np.zeros((n_fdu, n_var), dtype=float)

        # Fill matrix with dimension columns
        for var in self._relevant_lt.values():
            # Ensure dimension column has correct length
            dim_col = var._dim_col

            # Pad or truncate to match FDU count
            if len(dim_col) < n_fdu:
                dim_col = dim_col + [0] * (n_fdu - len(dim_col))
            elif len(dim_col) > n_fdu:
                dim_col = dim_col[:n_fdu]

            # Set column in matrix
            self._dim_mtx[:, var._idx] = dim_col

        # Create transposed version
        self._dim_mtx_trans = self._dim_mtx.T

    def solve_matrix(self) -> None:
        """*solve_matrix()* Solves the dimensional matrix.

        Computes the Row-Reduced Echelon Form (RREF) of the matrix, identifies pivot columns, and generates dimensionless coefficients from the nullspace.

        Raises:
            ValueError: If matrix hasn't been created yet.
        """
        # Ensure matrix exists
        if not isinstance(self._dim_mtx, np.ndarray) or self._dim_mtx.size == 0:
            self.create_matrix()

        # Convert to SymPy for symbolic computation
        self._sym_mtx = sp.Matrix(self._dim_mtx)

        # Compute RREF and pivot columns
        rref_result, pivot_cols = self._sym_mtx.rref()

        # Store results
        self._rref_mtx = np.array(rref_result).astype(float)
        self._pivot_cols = list(pivot_cols)

        # Generate coefficients from nullspace
        self._generate_coefficients()

    def _generate_coefficients(self) -> None:
        """*_generate_coefficients()* Generates dimensionless coefficients.

        Creates Coefficient objects from each nullspace vector of the dimensional matrix. Each nullspace vector represents a dimensionless group (Pi coefficient).
        """
        if self._sym_mtx is None:
            _msg = "Symbolic matrix not created. Call solve_matrix() first."
            raise ValueError(_msg)

        # Compute nullspace vectors
        self._nullspace = self._sym_mtx.nullspace()

        # Clear existing coefficients
        self._coefficients.clear()

        # Get variable symbols in order
        var_syms = [var for var in self._relevant_lt.keys()]

        # Create coefficient for each nullspace vector
        for i, vector in enumerate(self._nullspace):
            # Convert to numpy array
            vector_np = np.array(vector).flatten().astype(float)

            # Create variable dictionary for this coefficient
            # NOTE check possible unnecesary code, delete if deprecated
            coef_vars = {}
            for j, val in enumerate(vector_np):
                if j < len(var_syms) and isinstance(val, (int, float)):
                    coef_vars[var_syms[j]] = self._relevant_lt[var_syms[j]]

            # Create Pi coefficient
            pi_sym = f"\\Pi_{{{i}}}"
            coef = Coefficient(
                _idx=i,
                _sym=pi_sym,
                _alias=f"Pi_{i}",
                _fwk=self._fwk,
                _cat=CoefCardinality.COMPUTED.value,
                _variables=self._relevant_lt,
                _dim_col=vector_np.tolist(),
                _pivot_lt=self._pivot_cols,
                _name=f"Pi-{i}",
                description=f"Dimensionless coefficient {i} from nullspace"
            )

            self._coefficients[pi_sym] = coef

    # ========================================================================
    # Coefficient Derivation
    # ========================================================================

    def derive_coefficient(self,
                           expr: str,
                           symbol: str = "",
                           name: str = "",
                           description: str = "",
                           idx: int = -1) -> Coefficient:
        """*derive_coefficient()* Creates a new coefficient derived from existing ones.

        Combines existing dimensionless coefficients using a mathematical expression. The new coefficient is marked as "DERIVED".

        Args:
            expr (str): Mathematical expression using existing coefficients and numeric constants.
                Supports: *, /, ** (power), +, -, and numeric constants
                Examples:
                    - "\\Pi_{0} * \\Pi_{1}" (multiplication: adds exponents)
                    - "\\Pi_{0} / \\Pi_{1}" (division: subtracts exponents)
                    - "\\Pi_{0}**(-1)" (power: multiplies exponents)
                    - "\\Pi_{0} + \\Pi_{1}" (addition: result is dimensionless)
                    - "\\Pi_{0} - \\Pi_{1}" (subtraction: result is dimensionless)
                    - "2 * \\Pi_{0}" (constant multiplication: constant is dimensionless)
                    - "0.5 * \\Pi_{1} * \\Pi_{0}**(-1)" (mixed expression with constant)
                    - "1/\\Pi_{2}" (invert the coefficient - changes both exponents and values)
            symbol (str): Symbol representation (LaTeX or alphanumeric) for the derived coefficient. Default to "" to keep the original (e.g., Pi_{0}).
            name (str, optional): Name for the derived coefficient. Defaults to "Derived-Pi-{idx}".
            description (str, optional): Description of the coefficient. Defaults to "Derived from: {expr}".
            idx (int, optional): Index for the coefficient. If -1, the next available index is used.

        Returns:
            Coefficient: The newly created derived coefficient.

        Raises:
            ValueError: If expression is invalid or references non-existent coefficients.
            ValueError: If expression creates dimensionally inconsistent result.

        Example:
            >>> # Create Reynolds number as ratio of two Pi groups
            >>> Re = model.derive_coefficient(
            ...     expr="\\Pi_{0} / \\Pi_{1}",
            ...     name="Reynolds Number",
            ...     description="Ratio of inertial to viscous forces"
            ... )
            >>> # Create a coefficient with constant multiplier
            >>> scaled = model.derive_coefficient(
            ...     expr="2 * \\Pi_{0}",
            ...     name="Scaled Coefficient",
            ...     description="Twice the original coefficient"
            ... )
        """
        # Validate coefficients exist
        if not self._coefficients:
            _msg = "Cannot derive coefficients. No base coefficients exist yet."
            raise ValueError(_msg)

        # Parse dimensional expression using parser functions
        # TODO improve using sympy + pint later
        _dev_col, _num_const = parse_dim_expr(expr,
                                              self.coefficients,
                                              dim_col_fn=lambda coef: coef._dim_col)

        # Get base coefficient for structure
        _coef_symbols = re.findall(PI_COEF_RE, expr)
        _base_coef = self.coefficients[_coef_symbols[0]]

        # Use the relevant_lt (all relevant variables) instead of just base coef variables
        # This ensures control variables are included even if not in all Pi groups
        _new_vars = self._relevant_lt.copy() if hasattr(self, '_relevant_lt') and self._relevant_lt else _base_coef.variables.copy()

        # Validate all coefficients use same variables
        for sym in _coef_symbols[1:]:
            coef = self.coefficients[sym]
            if set(coef.variables.keys()) != set(_new_vars.keys()):
                _msg = f"Coefficient {sym} uses different variables. "
                _msg += "Cannot derive new coefficient."
                raise ValueError(_msg)

        # Determine next available index for coefficient
        if idx == -1:
            existing_indices = [c._idx for c in self.coefficients.values()]
            idx = max(existing_indices) + 1 if existing_indices else 0

        if name == "":
            name = f"Derived-Pi-{idx}"

        if description == "":
            description = f"Derived from: {expr}"

        if symbol == "":
            symbol = f"\\Pi_{{{idx}}}"

        # Create derived coefficient
        new_sym = symbol
        new_alias = f"Pi_dev_{idx}"
        derived_coef = Coefficient(
            _idx=idx,
            _sym=new_sym,
            _alias=new_alias,
            _fwk=self._fwk,
            _cat=CoefCardinality.DERIVED.value,
            _name=name,
            description=description,
            _variables=_new_vars,
            _dim_col=_dev_col,
            _pivot_lt=self._pivot_cols
        )

        # If there's a numeric constant, prepend it to the expression
        const_str = format_numeric_constant(_num_const)
        if const_str:
            if derived_coef._pi_expr:
                derived_coef._pi_expr = f"{const_str}*{derived_coef._pi_expr}"

        # Add to coefficients dictionary
        self._coefficients[new_sym] = derived_coef

        return derived_coef

    # ========================================================================
    # High-Level Methods
    # ========================================================================

    def analyze(self) -> None:
        """*analyze()* Performs complete dimensional analysis

        Executes the full analysis workflow:
        1. Prepare analysis (validate variables, identify output)
        2. Create dimensional matrix
        3. Solve matrix (compute RREF and nullspace)
        4. Generate dimensionless coefficients

        This is the main entry point for dimensional analysis.
        """
        self._prepare_analysis()
        self.create_matrix()
        self.solve_matrix()

    def clear(self) -> None:
        """*clear()* Resets all dimensional matrix and analysis data.

        Clears all computed results while preserving the framework (_schema).
        Resets all attributes to the same state as __post_init__ leaves them.

        NOTE: Numpy arrays don't have .clear() method, so we reassign. Lists have .clear() method.
        """
        # Reset parent class attributes (Foundation)
        super().clear()
        self._sym = f"DM_{{{self._idx}}}"

        # Reset Matrix-specific attributes
        self._variables = {}
        self._relevant_lt = {}
        self._output = None
        self._n_var = 0
        self._n_relevant = 0
        self._n_in = 0
        self._n_out = 0
        self._n_ctrl = 0
        self._dim_mtx = np.array([], dtype=float)
        self._dim_mtx_trans = None
        self._sym_mtx = sp.Matrix([])
        self._rref_mtx = None
        self._nullspace = []
        self._pivot_cols = []
        self._coefficients = {}
        self.working_fdus = []

    # ========================================================================
    # Properties
    # ========================================================================

    @property
    def variables(self) -> Dict[str, Variable]:
        """*variables* Get the dictionary of variables.

        Returns:
            Dict[str, Variable]: Copy of variables dictionary.
        """
        return self._variables

    @variables.setter
    @validate_type(dict, allow_none=False)
    @validate_emptiness()
    @validate_dict_types(str, Variable)
    def variables(self, val: Dict[str, Variable]) -> None:
        """*variables* Set the dictionary of variables.

        Args:
            val (Dict[str, Variable]): Dictionary of variables.

        Raises:
            ValueError: If input is not a non-empty dictionary.
            ValueError: If any value is not a Variable instance.
        """
        self._variables = val

        # Update relevant variables and prepare for analysis
        self._prepare_analysis()

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

        # Prepare for analysis with new framework
        if self._variables:
            self._prepare_analysis()

    @property
    def relevant_lt(self) -> Dict[str, Variable]:
        """*relevant_lt* Get dictionary of relevant variables.

        Returns:
            Dict[str, Variable]: Dictionary of relevant variables.
        """
        return self._relevant_lt

    @relevant_lt.setter
    @validate_type(dict, allow_none=False)
    @validate_dict_types(str, Variable)
    def relevant_lt(self, val: Dict[str, Variable]) -> None:
        """*relevant_lt* Set the dictionary of relevant variables, otherwise known as 'relevance list'.

        Args:
            val (Dict[str, Variable]): Dictionary of relevant variables.

        Raises:
            ValueError: If the relevant variable dictionary is invalid.
            ValueError: If any of the dictionary variables are invalid.
        """
        # Set relevant variables and prepare for analysis
        # self._relevant_lt = [p for p in val if p.relevant]
        self._relevant_lt = {
            k: v for k, v in self._variables.items() if v.relevant
        }

        # Update relevant variables and prepare for analysis
        self._prepare_analysis()

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

    @property
    def sym(self) -> str:
        """*sym* Get the symbol.

        Returns:
            str: Symbol value.
        """
        return self._sym

    @sym.setter
    @validate_type(str)
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
    def alias(self) -> str:
        """*alias* Get the Python variable alias.

        Returns:
            str: Python variable name alias.
        """
        return self._alias

    @alias.setter
    @validate_type(str)
    @validate_emptiness()
    def alias(self, val: str) -> None:
        """*alias* Set the Python variable alias.

        Args:
            val (str): Python variable name alias.

        Raises:
            ValueError: If alias is empty.
        """
        self._alias = val

    @property
    def fwk(self) -> str:
        """*fwk* Get the framework.

        Returns:
            str: Framework value.
        """
        return self._fwk

    @fwk.setter
    @validate_type(str)
    @validate_choices(PYDASA_CFG.frameworks)
    def fwk(self, val: str) -> None:
        """*fwk* Set the framework with validation.

        Args:
            val (str): Framework value.

        Raises:
            ValueError: If framework is not supported.
        """
        self._fwk = val

    @property
    def coefficients(self) -> Dict[str, Coefficient]:
        """*coefficients* Get dictionary of dimensionless coefficients.

        Returns:
            Dict[str, Coefficient]: Dictionary of dimensionless coefficients.
        """
        return self._coefficients

    @property
    def output(self) -> Optional[Variable]:
        """*output* Get the output variable.

        Returns:
            Optional[Variable]: The output variable, or None if not set.
        """
        return self._output

    @property
    def dim_mtx(self) -> Optional[NDArray[np.float64]]:
        """*dim_mtx* Get the dimensional matrix.

        Returns:
            Optional[NDArray[np.float64]]: Dimensional matrix, or None.
        """
        return self._dim_mtx if self._dim_mtx is not None else None

    @property
    def rref_mtx(self) -> Optional[NDArray[np.float64]]:
        """*rref_mtx* Get the RREF matrix.

        Returns:
            Optional[NDArray[np.float64]]: RREF matrix, or None.
        """
        return self._rref_mtx if self._rref_mtx is not None else None

    @property
    def pivot_cols(self) -> List[int]:
        """*pivot_cols* Get pivot column indices.

        Returns:
            List[int]: Pivot column list.
        """
        return self._pivot_cols

    # ========================================================================
    # Serialization
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """*to_dict()* Convert model to dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        result = {}

        # Get all dataclass fields
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, attr_name)

            # Handle numpy arrays
            if isinstance(attr_value, np.ndarray):
                attr_value = attr_value.tolist()
            # Handle SymPy matrices
            elif isinstance(attr_value, sp.Matrix):
                attr_value = [[float(val) for val in row] for row in attr_value.tolist()]
            # Handle Schema, Variable, Coefficient objects
            elif isinstance(attr_value, (Schema, Variable, Coefficient)):
                attr_value = attr_value.to_dict()
            # Handle dictionaries with Variable or Coefficient values
            elif isinstance(attr_value, dict) and attr_value:
                first_val = next(iter(attr_value.values()), None)
                if isinstance(first_val, (Variable, Coefficient)):
                    attr_value = {k: v.to_dict() for k, v in attr_value.items()}
            # Handle lists
            elif isinstance(attr_value, list):
                # Check if list contains objects with to_dict
                if attr_value and hasattr(attr_value[0], 'to_dict'):
                    attr_value = [item.to_dict() if hasattr(item, 'to_dict') else item for item in attr_value]

            # Skip callables (can't be serialized)
            if callable(attr_value) and not isinstance(attr_value, type):
                continue

            # Remove leading underscore from private attributes
            clean_name = attr_name[1:] if attr_name.startswith("_") else attr_name
            result[clean_name] = attr_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Matrix":
        """*from_dict()* Create model from dictionary representation.

        Args:
            data (Dict[str, Any]): Dictionary representation of the model.

        Returns:
            Matrix: New Matrix instance.
        """
        # Get all valid field names from the dataclass
        field_names = {f.name for f in fields(cls)}

        # Map keys without underscores to keys with underscores
        mapped_data = {}

        for key, value in data.items():
            # Handle special conversions for Schema
            if key == "schema" and isinstance(value, dict):
                mapped_data["_schema"] = Schema.from_dict(value)
                continue
            # Handle dictionary of Variables
            elif key == "variables" and isinstance(value, dict):
                mapped_data["_variables"] = {
                    k: Variable.from_dict(v) if isinstance(v, dict) else v
                    for k, v in value.items()
                }
                continue
            # Handle dictionary of Coefficients
            elif key == "coefficients" and isinstance(value, dict):
                mapped_data["_coefficients"] = {
                    k: Coefficient.from_dict(v) if isinstance(v, dict) else v
                    for k, v in value.items()
                }
                continue
            # Handle single Variable output
            elif key == "output" and isinstance(value, dict):
                mapped_data["_output"] = Variable.from_dict(value)
                continue
            # Handle numpy arrays
            elif key in ["dim_mtx", "dim_mtx_trans", "rref_mtx"] and isinstance(value, list):
                field_key = f"_{key}" if f"_{key}" in field_names else key
                mapped_data[field_key] = np.array(value)
                continue
            # Handle SymPy matrices
            elif key == "sym_mtx" and isinstance(value, list):
                mapped_data["_sym_mtx"] = sp.Matrix(value)
                continue
            # Handle nullspace (list of arrays or matrices)
            elif key == "nullspace" and isinstance(value, list):
                mapped_data["_nullspace"] = [np.array(item) if isinstance(item, list) else item for item in value]
                continue

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

        return cls(**mapped_data)
