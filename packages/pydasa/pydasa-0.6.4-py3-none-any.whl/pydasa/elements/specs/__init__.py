# -*- coding: utf-8 -*-
"""
Variable specifications module.

Four compositional perspectives for variable representation:
- ConceptualSpecs: Identity and classification
- SymbolicSpecs: Mathematical notation and dimensions
- NumericalSpecs: Computational values and ranges
- StatisticalSpecs: Probabilistic distributions
"""

from .conceptual import ConceptualSpecs
from .symbolic import SymbolicSpecs
from .numerical import NumericalSpecs
from .statistical import StatisticalSpecs

__all__ = [
    'ConceptualSpecs',
    'SymbolicSpecs',
    'NumericalSpecs',
    'StatisticalSpecs',
]
