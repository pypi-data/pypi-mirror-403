# -*- coding: utf-8 -*-
"""
PyDASA Package
===========================================
Main package initializer for PyDASA library, exposing core functionalities, data structures, dimensional analysis tools, unit conversion utilities, and workflow management components.
"""
# expose version
from ._version import __version__

# expose imports
# exposing analytics modules
from .analysis.scenario import Sensitivity
from .analysis.simulation import MonteCarlo

# TODO conversion still in development
# exposing unit conversion modules
# from .context.conversion import UnitStandarizer
# from .context.system import MeasureSystem
# from .context.measurements import Unit

# exposing pi-theorem/dimensional analysis modules
from .dimensional.buckingham import Coefficient
from .dimensional.fundamental import Dimension
from .dimensional.vaschy import Schema
from .dimensional.model import Matrix

# exposing core modules
# exposing basic elements/variables modules
from .elements.parameter import Variable
# exposing parser/io modules
from .core.io import load, save

# exposing custom data structure modules
# TODO measurement still in development
# lists
from .structs.lists.arlt import ArrayList
from .structs.lists.sllt import SingleLinkedList
from .structs.lists.ndlt import Node, SLNode, DLNode
# from .structs.lists.dllt import DoubleLinkedList
# tables
from .structs.tables.htme import MapEntry
from .structs.tables.scht import Bucket, SCHashTable

# exposing validation, error and decorator modules
# exposing workflow modules
from .workflows.basic import WorkflowBase
from .workflows.influence import SensitivityAnalysis
from .workflows.practical import MonteCarloSimulation
from .workflows.phenomena import AnalysisEngine

# asserting all imports
# asserting analytics modules
assert Sensitivity
assert MonteCarlo

# asserting unit conversion modules
# assert UnitStandarizer
# assert MeasureSystem
# assert Unit
# asserting pi-theorem/dimensional analysis modules
assert Coefficient
assert Dimension
assert Schema
assert Matrix
# asserting elements/variables modules
assert Variable
# asserting parser/io modules
assert load
assert save
# asserting custom data structure modules
# lists
assert ArrayList
assert SingleLinkedList
assert Node
assert SLNode
assert DLNode
# tables
assert MapEntry
assert Bucket
assert SCHashTable
# asserting workflow modules
assert WorkflowBase
assert SensitivityAnalysis
assert MonteCarloSimulation
assert AnalysisEngine

# Define __all__ for wildcard imports
__all__ = [
    "__version__",
    "Sensitivity",
    "MonteCarlo",
    # "UnitStandarizer",
    # "MeasureSystem",
    # "Unit",
    "Coefficient",
    "Dimension",
    "Schema",
    "Matrix",
    "Variable",
    "load",
    "save",
    "WorkflowBase",
    "SensitivityAnalysis",
    "MonteCarloSimulation",
    "AnalysisEngine",
]
