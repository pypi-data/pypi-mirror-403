"""
Result module

Provides the :class:`Result` dataclass for storing algorithm execution outcomes.

The Result class encapsulates all information about a solver run including
the best solution found, its objective value, runtime statistics, and
iteration-by-iteration performance data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Set

if TYPE_CHECKING:
    from .Statistics import Statistics


@dataclass
class Result:
    """
    Container for the results of a Critical Node Problem solver run.

    This dataclass stores all relevant information about an algorithm execution,
    including the best solution found, associated metrics, and optional detailed
    statistics collected during the search process.

    The result object is returned by :meth:`Model.solve` and :meth:`MemeticSearch.run`.

    Examples
    --------
    Access result properties:

    >>> result = model.solve("CNP", 5, MaxIterations(100))
    >>> print(f"Removed nodes: {result.best_solution}")
    >>> print(f"Connectivity after removal: {result.best_obj_value}")
    >>> print(f"Iterations: {result.num_iterations}")

    Check statistics if available:

    >>> if result.stats:
    ...     df = result.stats.to_dataframe()
    ...     df.plot(x="iteration", y="best_obj_value")
    """

    best_solution: Set[int] = field(default_factory=set)
    best_obj_value: float = math.inf
    num_iterations: int = 0
    runtime: float = 0.0
    best_found_at_time: float = 0.0
    stats: Optional["Statistics"] = None
