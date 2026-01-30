"""
Statistics module.

Provides the :class:`Statistics` class for collecting and managing iteration
metrics during a MemeticSearch run.

This module tracks runtime, best objective value, population size, and idle
generation counts for each iteration, enabling post-hoc analysis of algorithm
performance.

Classes
-------
Statistics
    Collects and manages iteration statistics during search execution.
_IterationStats
    Internal dataclass storing statistics for a single iteration.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .constants import PACKAGE_LOGGER_NAME

logger = logging.getLogger(PACKAGE_LOGGER_NAME)


@dataclass
class _IterationStats:
    """
    Internal container for statistics from a single iteration.

    This dataclass is used internally by :class:`Statistics` to store
    per-iteration metrics.
    """

    runtime: float
    best_obj_value: float
    population_size: int
    num_idle_generations: int


class Statistics:
    """
    Collects and manages statistics during a MemeticSearch run.

    The Statistics class provides functionality to record runtime, best
    objective value, population size, and idle generation counts for each
    iteration of the memetic algorithm.

    Attributes
    ----------
    data : List[_IterationStats]
        List of iteration statistics collected during the search.
    num_iterations : int
        Total number of iterations recorded.

    Examples
    --------
    >>> from pycnp import Statistics
    >>> stats = Statistics(collect_stats=True)
    >>> # During search...
    >>> stats.collect(best_obj_value=100.5, population_size=10, num_idle_generations=0)
    >>> stats.collect(best_obj_value=98.2, population_size=10, num_idle_generations=0)
    >>> print(f"Iterations: {stats.num_iterations}")
    Iterations: 2
    """

    def __init__(self, collect_stats: bool = True):
        """
        Parameters
        ----------
        collect_stats : bool, default=True
            Whether to collect statistics.
        """
        self._collect_stats = collect_stats
        self._clock = time.perf_counter()
        self.data: list[_IterationStats] = []
        self.num_iterations = 0

    def is_collecting(self) -> bool:
        """
        Returns whether statistics are being collected.

        Returns
        -------
        bool
            True if statistics are being collected, False otherwise.
        """
        return self._collect_stats

    def collect(
        self, best_obj_value: float, population_size: int, num_idle_generations: int
    ):
        """
        Collects statistics for the current iteration.

        Parameters
        ----------
        best_obj_value : float
            The best objective value found in the current iteration.
        population_size : int
            The current population size.
        num_idle_generations : int
            The number of idle generations (no improvement).
        """
        if not self._collect_stats:
            return

        now = time.perf_counter()
        runtime = now - self._clock
        self._clock = now

        self.num_iterations += 1
        datum = _IterationStats(
            runtime=runtime,
            best_obj_value=best_obj_value,
            population_size=population_size,
            num_idle_generations=num_idle_generations,
        )
        self.data.append(datum)
