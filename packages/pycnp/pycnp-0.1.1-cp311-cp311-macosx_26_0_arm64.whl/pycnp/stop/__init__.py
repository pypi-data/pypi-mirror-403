"""
This module provides a collection of stopping criteria for iterative algorithms.

It includes common criteria such as:

- ``MaxIterations``: Stop after a fixed number of iterations.
- ``MaxRuntime``: Stop after a certain amount of time has elapsed.
- ``NoImprovement``: Stop when the solution has not improved for a given
  number of iterations.

These criteria can be used to control the termination of optimization or
search algorithms.
"""

from __future__ import annotations

from .MaxIterations import MaxIterations
from .MaxRuntime import MaxRuntime
from .NoImprovement import NoImprovement
from .StoppingCriterion import StoppingCriterion

__all__ = [
    "MaxIterations",
    "MaxRuntime",
    "NoImprovement",
    "StoppingCriterion",
]
