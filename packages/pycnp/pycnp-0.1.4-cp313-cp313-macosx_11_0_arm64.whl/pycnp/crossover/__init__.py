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

import importlib
from typing import Any

import pycnp._pycnp  # noqa: F401

from .double_backbone_based_crossover import DBX
from .double_backbone_based_crossover import (
    double_backbone_based_crossover as double_backbone_based_crossover,
)
from .inherit_repair_recombination import IRR
from .inherit_repair_recombination import (
    inherit_repair_recombination as inherit_repair_recombination,
)
from .reduce_solve_combine import RSC
from .reduce_solve_combine import reduce_solve_combine as reduce_solve_combine

_crossover: Any = importlib.import_module("pycnp.crossover._crossover")

__all__ = [
    "DBX",
    "IRR",
    "RSC",
    "_crossover",
    "double_backbone_based_crossover",
    "inherit_repair_recombination",
    "reduce_solve_combine",
]
