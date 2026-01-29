"""
ProgressPrinter module.

Provides the :class:`ProgressPrinter` class for displaying algorithm progress
information during MemeticSearch execution.

This module handles formatted output to console/loggers, displaying iteration
counters, runtime, best objective values, and other metrics at configurable
intervals. Inspired by PyVRP's ProgressPrinter.

Classes
-------
ProgressPrinter
    Handles printing progress information for MemeticSearch.
"""

from __future__ import annotations

import logging
import time
from importlib.metadata import version as get_version
from typing import TYPE_CHECKING, Optional

from .constants import DEFAULT_DISPLAY_INTERVAL, PACKAGE_LOGGER_NAME

if TYPE_CHECKING:
    from .Result import Result
    from .Statistics import Statistics

_ITERATION_TEMPLATE = (
    "{indicator}Iter {iter:>5} | Time: {elapsed:>6.2f}s | Best: {best_obj:<10.2f} | "
    "Idle: {idle:>4} | PopSize: {pop_size:>3}"
)

_START_TEMPLATE = """PyCNP v{version}

Solving an instance with:
    Problem type: {problem_type_name}
    Budget: {budget}
    Seed:  {seed}
"""

_ITERATION_HEADER_TEMPLATE = """
  Iter        | Time        | Best        | Idle    | PopSize
"""

_END_TEMPLATE = """
----------------------------------------------------------------------
MimeticSearch finished.
    Total iterations: {iters}
    Total runtime: {runtime:.2f} seconds
    Best objective found: {best_obj:.2f}
    Nodes in solution: {nodes_in_solution}
    Best solution found: {best_solution}
"""


class ProgressPrinter:
    """
    Handles formatted progress output during MemeticSearch execution.

    The ProgressPrinter class manages the display of algorithm progress
    information including iteration counts, runtime, best objective values,
    and population statistics. Output can be directed to console or logging
    handlers with configurable display intervals.

    Parameters
    ----------
    should_print : bool
        Whether to enable progress output.
    logger : logging.Logger, optional
        Logger instance for emitting progress messages.
    display_interval : float, default=DEFAULT_DISPLAY_INTERVAL
        Minimum time interval between progress updates, in seconds.

    Notes
    -----
    This class is designed to be used internally by MemeticSearch and is
    not typically instantiated directly by users.

    See Also
    --------
    pycnp.Statistics : For iteration statistics collection.
    pycnp.Result : For storing search results.
    """

    def __init__(
        self,
        should_print: bool,
        logger: Optional[logging.Logger] = None,
        display_interval: float = DEFAULT_DISPLAY_INTERVAL,
    ):
        """
        Parameters
        ----------
        should_print : bool
            Whether to print information to the console.
        logger : logging.Logger, optional
            Logger to emit progress messages to.
        display_interval : float, optional
            Minimum interval between progress messages, in seconds.
        """
        self._print = should_print
        self._logger = logger or logging.getLogger(PACKAGE_LOGGER_NAME)
        self._display_interval = display_interval
        self._last_print_time = time.perf_counter()
        self._last_printed_iter_num = 0
        self._current_best_obj = float("inf")

    def _should_print_now(self) -> bool:
        """Determines if enough time has passed to print again."""
        return time.perf_counter() - self._last_print_time >= self._display_interval

    def start(self, problem_type_name: str, budget: int, seed: int):
        """
        Outputs information about the search settings.
        """
        if not self._print:
            return

        pycnp_version = "unknown"
        try:
            pycnp_version = get_version("pycnp")
        except OSError:
            self._logger.warning(
                "Could not determine pycnp version from installed metadata."
            )

        msg = _START_TEMPLATE.format(
            version=pycnp_version,
            problem_type_name=problem_type_name,
            budget=budget,
            seed=seed,
        )
        self._logger.info(msg)
        self._current_best_obj = float("inf")

    def initializing_population_message(self):
        """
        Prints a message before population initialization starts.
        """
        if not self._print:
            return
        self._logger.info(
            "-----------------------Initializing population-----------------------"
        )
        self._last_print_time = time.perf_counter()

    def print_iterations_start_banner_and_header(self):
        """
        Prints a message before the main iteration loop starts and the header.
        """
        if not self._print:
            return
        self._logger.info(
            "--------------------Starting Population Iterations--------------------"
        )
        self._logger.info(_ITERATION_HEADER_TEMPLATE)
        self._last_print_time = time.perf_counter()

    def iteration(self, stats: "Statistics", force_print: bool = False):
        """
        Outputs relevant information based on the latest statistics.
        Prints periodically or if force_print is True.
        """
        if not self._print or not stats.is_collecting() or not stats.data:
            return

        if not force_print and not self._should_print_now():
            return

        latest_stats = stats.data[-1]
        total_runtime = sum(s.runtime for s in stats.data)

        indicator = " "
        if latest_stats.best_obj_value < self._current_best_obj:
            self._current_best_obj = latest_stats.best_obj_value
            indicator = "*"

        msg = _ITERATION_TEMPLATE.format(
            indicator=indicator,
            iter=stats.num_iterations,
            elapsed=total_runtime,
            best_obj=latest_stats.best_obj_value,
            idle=latest_stats.num_idle_generations,
            pop_size=latest_stats.population_size,
        )
        self._logger.info(msg)
        self._last_print_time = time.perf_counter()
        self._last_printed_iter_num = stats.num_iterations

    def end(self, result: "Result"):
        """
        Outputs information about the search duration and the best-found
        solution.
        """
        if not self._print:
            return

        if (
            result.stats
            and result.stats.data
            and result.stats.num_iterations > self._last_printed_iter_num
        ):
            self.iteration(result.stats, force_print=True)

        msg = _END_TEMPLATE.format(
            iters=result.num_iterations,
            runtime=result.runtime,
            best_obj=result.best_obj_value,
            nodes_in_solution=len(result.best_solution),
            best_solution=str(result.best_solution),
        )
        self._logger.info(msg)
