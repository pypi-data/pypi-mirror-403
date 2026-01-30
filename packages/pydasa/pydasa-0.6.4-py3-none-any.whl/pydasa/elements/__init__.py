# -*- coding: utf-8 -*-
"""
Module elements
===========================================

Module for representing **Variable** entities and their compositional specifications
in Dimensional Analysis for *PyDASA*.

Classes:
    **Variable**: Main class combining all perspectives (Conceptual, Symbolic, Numerical, Statistical).

Submodules:
    **parameter**: Variable class implementation.
    **specs**: Compositional perspective specifications (ConceptualSpecs, SymbolicSpecs, NumericalSpecs, StatisticalSpecs).
"""

from pydasa.elements.parameter import Variable

__all__ = ['Variable']
