# -*- coding: utf-8 -*-
"""
Module latex.py
===========================================

Module for default global variables and comparison functions for use by all *PyDASA* and its Data Structs.
"""
# python native modules
# from dataclasses import dataclass
# from typing import TypeVar
from typing import Tuple, Dict, List, Optional, Any, Callable, Sequence
import re

# custom modules
from sympy.parsing.latex import parse_latex
from sympy import Symbol, symbols

# import global variables
from pydasa.validations.patterns import LATEX_RE
from pydasa.validations.patterns import PI_POW_RE
from pydasa.validations.patterns import PI_COEF_RE
from pydasa.validations.patterns import BASIC_OPS_RE
# Global vars for special Latex symbos and functions to ignore
from pydasa.validations.patterns import IGNORE_EXPR


# Latex Parsing Functions

def latex_to_python(expr: str) -> str:
    """*latex_to_python()* Convert a LaTeX expression to a Python-compatible string.

    Args:
        expr (str): The LaTeX expression to convert.

    Returns:
        str: The Python-compatible string.
    """
    # Replace LaTeX subscript with Python style
    if expr.isalnum():
        return expr
    # TODO this regex doesnt work, check latter
    # ans = re.sub(r"\\([a-zA-Z]+)_{(\d+)}", r"\1_\2", expr)
    alias = expr.replace("\\", "")
    alias = alias.replace("_{", "_").replace("}", "")
    return alias


def extract_latex_vars(expr: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """*extract_latex_vars()* Extract variable names in LaTeX format with their Python equivalents.

    Args:
        expr (str): The LaTeX expression to parse.

    Returns:
        tuple [dict]: A tuple containing two dictionaries:
                - The first dictionary maps LaTeX variable names to their Python equivalents.
                - The second dictionary maps Python variable names to their LaTeX equivalents.
    """
    # Extract latex variable names with regex
    matches = re.findall(LATEX_RE, expr)

    # Filter out ignored LaTeX commands
    matches = [m for m in matches if m not in IGNORE_EXPR]

    # Create mappings both ways
    latex_to_py = {}
    py_to_latex = {}

    for m in matches:
        # Keep original LaTeX notation for external reference
        latex_var = m
        # Convert to Python style for internal use
        py_var = m.lstrip("\\")
        py_var = py_var.replace("_{", "_")
        py_var = py_var.replace("}", "")

        latex_to_py[latex_var] = py_var
        py_to_latex[py_var] = latex_var

    return latex_to_py, py_to_latex


def create_latex_mapping(expr: str) -> Tuple[Dict[Symbol, Symbol],  # symbol_map
                                             Dict[str, Symbol],  # py_symbol_map
                                             Dict[str, str],     # latex_to_py
                                             Dict[str, str]      # py_to_latex
                                             ]:
    """*create_latex_mapping()* Create a mapping between LaTeX symbols and Python symbols.

    Args:
        expr (str): The LaTeX expression to parse.

    Returns:
        tuple[dict]: A tuple containing:
            - A dictionary mapping LaTeX symbols to Python symbols for internal substitution.
            - A dictionary mapping Python variable names to their corresponding sympy symbols for lambdify.
            - A dictionary mapping LaTeX variable names to their Python equivalents.
            - A dictionary mapping Python variable names to their LaTeX equivalents.
    """
    # Get LaTeX<->Python variable mappings
    latex_to_py, py_to_latex = extract_latex_vars(expr)

    # Parse to get LaTeX symbols
    sym_expr = parse_latex(expr)

    # Create mapping for sympy substitution
    symbol_map = {}         # For internal substitution
    py_symbol_map = {}      # For lambdify

    for latex_sym in sym_expr.free_symbols:
        latex_name = str(latex_sym)

        # Find corresponding Python name
        for latex_var, py_var in latex_to_py.items():
            # Check for various forms of equivalence
            con1 = (latex_name == latex_var)
            con2 = (latex_name == py_var)
            con3 = (latex_name.replace("_{", "_").replace("}", "") == py_var)
            if con1 or con2 or con3:
                # Create symbol for this variable
                sym = symbols(py_var)
                # Store mappings
                symbol_map[latex_sym] = sym  # For substitution
                py_symbol_map[py_var] = sym  # For lambdify args
                break

    return symbol_map, py_symbol_map, latex_to_py, py_to_latex


# ============================================================================
# Dimensional Expression Parsing Functions
# TODO improve using sympy + pint later
# ============================================================================

def extract_coeff_syms(expr: str, patt: str = PI_COEF_RE) -> List[str]:
    """*extract_coeff_syms()* Extract Pi coefficient symbols from expression.

    Args:
        expr (str): Mathematical expression containing Pi coefficients.
        patt (str): Regex pattern to match coefficients. Defaults to Pi notation.

    Returns:
        List[str]: List of unique coefficient symbols (e.g., ['\\Pi_{0}', '\\Pi_{1}']).

    Example:
        >>> extract_coeff_syms("\\Pi_{0} * \\Pi_{1}**(-1)")
        ['\\Pi_{0}', '\\Pi_{1}']
    """
    # Use finditer to get full match instead of captured groups
    matches = re.finditer(patt, expr)
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for match in matches:
        sym = match.group(0)  # Get full match, not captured group
        if sym not in seen:
            seen.add(sym)
            unique.append(sym)
    return unique


def extract_powered_coeffs(expr: str,
                           pow_patt: str = PI_POW_RE) -> Tuple[str, Dict[str, Tuple[str, float]]]:
    """*extract_powered_coeffs()* Parse and replace power expressions with placeholders.

    Identifies patterns like \\Pi_{0}**(-1) and replaces them with temporary
    placeholders for easier parsing.

    Args:
        expr (str): Mathematical expression with potential power operations.
        pow_patt (str): Regex pattern to match power expressions.

    Returns:
        Tuple[str, Dict[str, Tuple[str, float]]]:
            - Modified expression with placeholders
            - Dictionary mapping placeholders to (coefficient_symbol, power) tuples

    Raises:
        ValueError: If power expression is invalid.

    Example:
        >>> expr = "\\Pi_{0}**(-1) * \\Pi_{1}**(2)"
        >>> new_expr, transforms = extract_powered_coeffs(expr)
        >>> # new_expr: "__PHLR_0__ * __PHLR_1__"
        >>> # transforms: {"__PHLR_0__": ("\\Pi_{0}", -1), "__PHLR_1__": ("\\Pi_{1}", 2)}
    """
    pow_transforms = {}
    n_placeholder = 0

    for match in re.finditer(pow_patt, expr):
        coef_sym = match.group(1)
        pow_str = match.group(2)

        try:
            power = float(pow_str)
        except ValueError:
            raise ValueError(f"Invalid power expression: {pow_str}")

        # Create placeholder and store transformation
        placeholder = f"__PHLR_{n_placeholder}__"
        pow_transforms[placeholder] = (coef_sym, power)
        expr = expr.replace(match.group(0), placeholder, 1)
        n_placeholder += 1

    return expr, pow_transforms


def extract_num_consts(expr: str) -> List[float]:
    """*extract_num_consts()* Extract numeric constants from expression.

    Args:
        expr (str): Mathematical expression containing numeric values.

    Returns:
        List[float]: List of numeric constants found in expression.

    Example:
        >>> extract_num_consts("2 * \\Pi_{0} + 0.5")
        [2.0, 0.5]
    """
    pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
    matches = re.findall(pattern, expr)
    return [float(m) for m in matches]


def compute_dims_opn(dim_col_a: Sequence[int | float],
                     dim_col_b: Sequence[int | float],
                     opn: str) -> List[int]:
    """*compute_dims_opn()* Compute result of dimensional operation.

    Applies dimensional analysis rules:
        - Multiplication (*): Add exponents
        - Division (/): Subtract exponents
        - Addition (+) / Subtraction (-): Result is dimensionless (all zeros)

    Args:
        dim_col_a (Sequence[int | float]): First dimensional column.
        dim_col_b (Sequence[int | float]): Second dimensional column.
        opn (str): Operation to perform ('*', '/', '+', '-').

    Returns:
        List[int]: Resulting dimensional column.

    Example:
        >>> compute_dims_opn([1, 2, 0], [0, 1, -1], "*")
        [1, 3, -1]  # L^1 * M^2 * L^0 * M^1 * T^-1 = L^1 * M^3 * T^-1
    """
    if opn == "*":
        return [int(a + b) for a, b in zip(dim_col_a, dim_col_b)]
    elif opn == "/":
        return [int(a - b) for a, b in zip(dim_col_a, dim_col_b)]
    elif opn in ("+", "-"):
        # Addition/subtraction: result is dimensionless
        return [0] * len(dim_col_a)
    else:
        raise ValueError(f"Unknown operation: {opn}")


def apply_pow_to_dims(dim_col: Sequence[int | float], pwr: float) -> List[int]:
    """*apply_pow_to_dims()* Apply power operation to dimensional column.

    Args:
        dim_col (Sequence[int | float]): Dimensional column.
        pwr (float): Power to apply.

    Returns:
        List[int]: Dimensional column with power applied.

    Example:
        >>> apply_pow_to_dims([1, 2, -1], -1)
        [-1, -2, 1]  # (L^1 * M^2 * T^-1)^-1 = L^-1 * M^-2 * T^1
    """
    return [int(exp * pwr) for exp in dim_col]


def validate_coeff_expr(expr: str,
                        avail_coeffs: Dict[str, Any],
                        pattern: str = PI_COEF_RE) -> None:
    """*validate_coeff_expr()* Validate coefficient expression.

    Checks that:
        1. Expression contains valid coefficient references
        2. All referenced coefficients exist

    Args:
        expr (str): Expression to validate.
        avail_coeffs (Dict[str, Any]): Available coefficients.
        pattern (str): Regex pattern to match coefficients.

    Raises:
        ValueError: If expression is invalid or references missing coefficients.
    """
    # Extract coefficient symbols
    coef_symbols = extract_coeff_syms(expr, pattern)

    if not coef_symbols:
        raise ValueError(
            f"Expression '{expr}' does not contain any valid "
            f"coefficient references (format: \\Pi_{{n}})."
        )

    # Check all coefficients exist
    for sym in coef_symbols:
        if sym not in avail_coeffs:
            raise ValueError(f"Referenced coefficient {sym} does not exist.")


def parse_dim_expr(expr: str,
                   coeffs: Dict[str, Any],
                   dim_col_fn: Callable[[Any], List[float | int]],
                   coef_patt: str = PI_COEF_RE,
                   pow_patt: str = PI_POW_RE,
                   ops_patt: str = BASIC_OPS_RE) -> Tuple[List[int], Optional[float]]:
    """*parse_dim_expr()* Parse and evaluate dimensional expression.

    Main parsing function that processes a dimensional expression containing
    Pi coefficients, operations, and numeric constants.

    Args:
        expr (str): Mathematical expression to parse.
        coeffs (Dict[str, Any]): Available coefficients dictionary.
        dim_col_fn (Callable[[Any], List[float]]): Function to extract dimension column from coefficient. Signature: dim_col_fn(coef) -> List[float]
        coef_patt (str): Regex pattern to match coefficients.
        pow_patt (str): Regex pattern to match power expressions.
        ops_patt (str): Regex pattern to match operations.

    Returns:
        Tuple[List[int], Optional[float]]:
            - Resulting dimensional column
            - Numeric constant multiplier (None if no constant or constant = 1.0)

    Raises:
        ValueError: If expression parsing fails.

    Example:
        >>> def get_dims(c): return c._dim_col
        >>> result_dims, constant = parse_dim_expr(
        ...     "2 * \\Pi_{0}**(-1) * \\Pi_{1}",
        ...     coeffs,
        ...     get_dims
        ... )
    """
    # Validate expression first
    validate_coeff_expr(expr, coeffs, coef_patt)

    # Extract powered coefficients and replace with placeholders
    expr, pow_transforms = extract_powered_coeffs(expr, pow_patt)

    # Parse expression into tokens
    parts = re.split(ops_patt, expr)

    # Initialize state
    _cur_op = "*"
    _res_dim_col: List[int] = []
    numeric_constant: Optional[float] = None
    is_first = True

    for part in parts:
        part = part.strip()

        # Skip empty parts
        if not part:
            continue

        # Check if it's an operator
        if part in ("*", "/", "^", "+", "-"):
            _cur_op = part
            continue

        # Check if it's a placeholder for powered coefficient
        if part.startswith("__PHLR_"):
            coef_sym, power = pow_transforms[part]
            coef = coeffs[coef_sym]

            # Get and apply power to dimensions
            dim_col = dim_col_fn(coef)
            _pow_dims = apply_pow_to_dims(dim_col, power)

            if is_first:
                _res_dim_col = _pow_dims
                is_first = False
            else:
                _res_dim_col = compute_dims_opn(_res_dim_col,
                                                _pow_dims,
                                                _cur_op)

        # Check if it's a numeric constant
        elif re.match(r"^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?$", part):
            constant = float(part)

            # Initialize with zeros if first element
            if is_first and not _res_dim_col:
                # Get dimension count from first coefficient
                coef_symbols = extract_coeff_syms(expr, coef_patt)
                if coef_symbols:
                    ref_coef = coeffs[coef_symbols[0]]
                    _res_dim_col = [0] * len(dim_col_fn(ref_coef))
                    is_first = False

            # Track numeric constants
            if _cur_op == "*":
                numeric_constant = constant if numeric_constant is None else numeric_constant * constant
            elif _cur_op == "/":
                numeric_constant = 1.0 / constant if numeric_constant is None else numeric_constant / constant

        # Check if it's a regular coefficient
        elif re.match(coef_patt, part):
            coef = coeffs[part]
            _dim_col = dim_col_fn(coef)

            if is_first:
                _res_dim_col = [int(x) for x in _dim_col]
                is_first = False
            else:
                _res_dim_col = compute_dims_opn(_res_dim_col,
                                                _dim_col,
                                                _cur_op)

    # Validate result
    if not _res_dim_col:
        _msg = f"Failed to derive dimensions from expression '{expr}'. "
        _msg += "Expression must contain valid coefficient references."
        raise ValueError(_msg)
    # Return result
    return _res_dim_col, numeric_constant


def format_numeric_constant(constant: Optional[float]) -> str:
    """*format_numeric_constant()* Format numeric constant for display.

    Args:
        constant (Optional[float]): Numeric constant to format.

    Returns:
        str: Formatted constant string, empty if None or 1.0.

    Example:
        >>> format_numeric_constant(2.0)
        '2'
        >>> format_numeric_constant(0.5)
        '0.5'
        >>> format_numeric_constant(None)
        ''
    """
    if constant is None or constant == 1.0:
        return ""

    if constant == int(constant):
        return str(int(constant))

    return str(constant)
