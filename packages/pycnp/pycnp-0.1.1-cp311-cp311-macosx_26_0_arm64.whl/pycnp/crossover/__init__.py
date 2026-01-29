"""
Crossover operators for the Critical Node Problem.

This module provides three crossover operators for evolutionary search:

- :func:`double_backbone_based_crossover`: DBX crossover for CNP
- :func:`inherit_repair_recombination`: IRR crossover for DCNP
- :func:`reduce_solve_combine`: RSC crossover for CNP

Each crossover operator can be imported directly from this module or from
their respective submodules.
"""

from __future__ import annotations

# Import C++ bindings submodule for documentation purposes
from . import _crossover
from .double_backbone_based_crossover import (
    DBX,
    double_backbone_based_crossover,
)
from .inherit_repair_recombination import (
    IRR,
    inherit_repair_recombination,
)
from .reduce_solve_combine import (
    RSC,
    reduce_solve_combine,
)

__all__ = [
    "DBX",
    "IRR",
    "RSC",
    "_crossover",
    "double_backbone_based_crossover",
    "inherit_repair_recombination",
    "reduce_solve_combine",
]
