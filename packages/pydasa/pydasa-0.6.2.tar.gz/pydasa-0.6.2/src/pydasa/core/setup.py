# -*- coding: utf-8 -*-
"""
Module config.py
===========================================

Configuration module for basic *PyDASA* configuration parameters related to Dimensional Analysis (DA) of complex phenomena.

This module provides type-safe configuration through Enums and frozen dataclasses, replacing the previous mutable dictionary-based approach with immutable, type-checked alternatives.

NOTE: in the future the enum should be configurated via external files (e.g., JSON, YAML) to allow user customization.

Key Features:
    - Type-safe Enum definitions for frameworks, categories, and modes
    - Immutable configuration via frozen dataclass with singleton pattern
    - Backward compatibility with legacy dict-based access

    Supported Frameworks:
        - PHYSICAL: Traditional physical dimensional framework.
        - COMPUTATION: Computer science dimensional framework.
        - SOFTWARE: Software architecture dimensional framework.
        - CUSTOM: User-defined dimensional framework.

    Supported Variable Categories:
        - IN: Input variables influencing the system.
        - OUT: Output variables representing analysis results.
        - CTRL: Control variables constraining the system.

    Supported Analysis Modes:
        - SYM: Analysis for symbolic processable Parameters (e.g., 'x + y').
        - NUM: Analysis for numeric Variables (e.g., 1.0, 2.5).

*IMPORTANT* Based on:
    # H.Gorter, *Dimensionalanalyse: Eine Theoririe der physikalischen Dimensionen mit Anwendungen*
"""
# native python modules
from enum import Enum
# dataclass imports
from dataclasses import dataclass, field
# data type imports
from typing import ClassVar

# custom modules
from pydasa.core.io import Path, load     # , save
from pydasa.core.constants import DFLT_CFG_FOLDER, DFLT_CFG_FILE

# checking custom modules
assert load
assert DFLT_CFG_FOLDER
assert DFLT_CFG_FILE

# =============================================================================
# *PyDASA* Enum Definitions
# =============================================================================


class Frameworks(str, Enum):
    """**Frameworks** Enum for Fundamental Dimensional Units (FDUs) frameworks in *PyDASA*.

    Purpose:
        - Defines the dimensional frameworks supported in *PyDASA*.

    Args:
        str (class): Python native str class.
        Enum (class): Python native Enum class.

    Returns:
        Frameworks: Enum member representing the FDU framework.
    """

    PHYSICAL = "PHYSICAL"
    COMPUTATION = "COMPUTATION"
    SOFTWARE = "SOFTWARE"
    CUSTOM = "CUSTOM"

    @property
    def description(self) -> str:
        """*description* Get human-readable description of the framework.

        Returns:
            str: Human-readable framework's description.
        """

        descriptions = {
            Frameworks.PHYSICAL: "Traditional physical dimensional framework (e.g., Length, Mass, Time).",
            Frameworks.COMPUTATION: "Computer science dimensional framework (e.g., Time, Space, Complexity).",
            Frameworks.SOFTWARE: "Software architecture dimensional framework (e.g., Time, Data, Connectivity).",
            Frameworks.CUSTOM: "User-defined dimensional framework for specific use cases.",
        }
        return descriptions[self]


class VarCardinality(str, Enum):
    """**VarCardinality** Enum for Variable cardinality in *PyDASA*.

    Purpose:
        - Defines the variable categories supported in *PyDASA*.
        - Used to classify variables in the dimensional matrix.

    Args:
        str (class): Python native str class.
        Enum (class): Python native Enum class.

    Returns:
        VarCardinality: Enum member representing the variable cardinality.
    """
    IN = "IN"
    OUT = "OUT"
    CTRL = "CTRL"

    @property
    def description(self) -> str:
        """*description* Get human-readable description of the variable cardinality.

        Returns:
            str: Human-readable variable cardinality description.
        """
        descriptions = {
            VarCardinality.IN: "Variables that influence the system (e.g., known inputs).",
            VarCardinality.OUT: "Variable that represent the results of the analysis.",
            VarCardinality.CTRL: "Variables used to control or constrain the system (e.g., constants).",
        }
        return descriptions[self]


class CoefCardinality(str, Enum):
    """**CoefCardinality** Enum for Dimensionless Coefficient/Numbers/Groups (DC/DN/DG) cardinality in *PyDASA*.

    Purpose:
        - Defines the categories of dimensionless coefficients supported in *PyDASA*.
        - Used to classify dimensionless coefficients in formulas and equations.
        - Helps in organizing and managing dimensionless coefficients in the analysis.

    Args:
        str (class): Python native str class.
        Enum (class): Python native Enum class.

    Returns:
        CoefCardinality: Enum member representing the coefficient cardinality.
    """
    COMPUTED = "COMPUTED"
    DERIVED = "DERIVED"

    @property
    def description(self) -> str:
        """*description* Get human-readable description of the coefficient cardinality.

        Returns:
            str: Human-readable coefficient cardinality description.
        """
        descriptions = {
            CoefCardinality.COMPUTED: "Coefficients directly calculated using the Dimensional Matrix.",
            CoefCardinality.DERIVED: "Coefficients obtained by combining or manipulating Computed Coefficients.",
        }
        return descriptions[self]


class AnaliticMode(str, Enum):
    """**AnaliticMode** Enum for analysis modes (e.g. sensitivity analysis, Monte Carlo simulation) in *PyDASA*.

    Purpose:
        - Defines the analysis modes supported in *PyDASA*.
        - Used to specify the type of analysis to be performed on variables, coefficients, or functions.

    Args:
        str (class): Python native str class.
        Enum (class): python native Enum class.

    Returns:
        AnaliticMode: Enum member representing the analysis mode.
    """
    SYM = "SYM"
    NUM = "NUM"

    @property
    def description(self) -> str:
        descriptions = {
            AnaliticMode.SYM: "Analysis for symbolic processable parameters (e.g., 'z = x + y').",
            AnaliticMode.NUM: "analysis for numeric variable ranges (e.g., 1.0, 2.5).",
        }
        return descriptions[self]


class SimulationMode(str, Enum):
    """**SimulationMode** Enum for simulation modes in *PyDASA*.

    Attributes:
        DIST: Generate samples using distribution functions (Monte Carlo).
        DATA: Use pre-existing data from Variable._data attributes.
    """
    DIST = "DIST"
    DATA = "DATA"

    @property
    def description(self) -> str:
        descriptions = {
            SimulationMode.DIST: "Generate samples using distribution functions (Monte Carlo).",
            SimulationMode.DATA: "Use pre-existing data from Variable._data attributes.",
        }
        return descriptions[self]

# =============================================================================
# Immutable Configuration Singleton
# =============================================================================


@dataclass(frozen=True)
class PyDASAConfig:
    """ **PyDASAConfig** Singleton class for PyDASA configuration. It uses dataclass decorator to freeze the data.

    Returns:
        PyDASAConfig: frozen singleton configuration instance.
    """

    # :attr: _instance
    _instance: ClassVar["PyDASAConfig | None"] = None
    """Singleton instance of PyDASAConfig."""

    # :attr: SPT_FDU_FWKS
    SPT_FDU_FWKS: dict = field(default_factory=dict)
    """Supported Fundamental Dimensional Units (FDUs) frameworks and their configurations."""

    def __post_init__(self):
        """*__post_init__()* Post-initialization to load configuration from file."""
        # Load configuration from default file (relative to this module's directory)
        module_dir = Path(__file__).parent
        fp = module_dir / DFLT_CFG_FOLDER / DFLT_CFG_FILE
        cfg_data = load(fp)

        # Since the dataclass is frozen, use object.__setattr__ to set attributes
        object.__setattr__(self,
                           "SPT_FDU_FWKS",
                           cfg_data.get("frameworks", {}))

    @classmethod
    def get_instance(cls) -> "PyDASAConfig":
        """*get_instance()* Get the singleton instance of PyDASAConfig.

        Returns:
            PyDASAConfig: Singleton instance of PyDASAConfig.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def frameworks(self) -> tuple[Frameworks, ...]:
        """*frameworks* Get supported frameworks.

        Returns:
            tuple[Frameworks, ...]: Tuple of supported Frameworks.
        """
        return tuple(Frameworks)

    @property
    def parameter_cardinality(self) -> tuple[VarCardinality, ...]:
        """*parameter_cardinality* Get supported variable cardinalities.

        Returns:
            tuple[VarCardinality, ...]: Tuple of supported VarCardinality.
        """
        return tuple(VarCardinality)

    @property
    def coefficient_cardinality(self) -> tuple[CoefCardinality, ...]:
        """*coefficient_cardinality* Get supported coefficient cardinalities.

        Returns:
            tuple[CoefCardinality, ...]: Tuple of supported CoefCardinality.
        """
        return tuple(CoefCardinality)

    @property
    def analitic_modes(self) -> tuple[AnaliticMode, ...]:
        """*analitic_modes* Get supported analysis modes.

        Returns:
            tuple[AnaliticMode, ...]: Tuple of supported AnaliticMode.
        """
        return tuple(AnaliticMode)

    @property
    def simulation_modes(self) -> tuple[SimulationMode, ...]:
        """*simulation_modes* Get supported simulation modes.

        Returns:
            tuple[SimulationMode, ...]: Tuple of supported SimulationMode.
        """
        return tuple(SimulationMode)


# Get singleton instance for configuration
# :attr: PYDASA_CFG
PYDASA_CFG: PyDASAConfig = PyDASAConfig()
"""
Singleton instance of PyDASAConfig for accessing global configuration.
"""
