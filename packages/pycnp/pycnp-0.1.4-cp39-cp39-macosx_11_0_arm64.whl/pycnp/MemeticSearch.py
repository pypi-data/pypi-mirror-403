"""
MemeticSearch module

Provides the :class:`MemeticSearch` class that implements a memetic algorithm
for solving Critical Node Problems.

The memetic algorithm combines population-based global search with local
refinement, using crossover operators to create offspring and local search
strategies to improve solutions.
"""

from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING, Optional, Union

from pycnp.ProgressPrinter import ProgressPrinter
from pycnp.Result import Result
from pycnp.Statistics import Statistics
from pycnp.crossover.double_backbone_based_crossover import (
    double_backbone_based_crossover,
)
from pycnp.crossover.inherit_repair_recombination import (
    inherit_repair_recombination,
)
from pycnp.crossover.reduce_solve_combine import reduce_solve_combine
from pycnp.params import MemeticSearchParams, VariablePopulationParams
from pycnp.validation import (
    validate_crossover_strategy,
    validate_problem_type,
    validate_reduce_params,
    validate_search_strategy,
)

from ._pycnp import Population, ProblemData, Search
from .constants import (
    DEFAULT_DISPLAY_INTERVAL,
    DEFAULT_HOP_DISTANCE,
    PACKAGE_LOGGER_NAME,
)

if TYPE_CHECKING:
    from pycnp.stop import StoppingCriterion

logger = logging.getLogger(PACKAGE_LOGGER_NAME)


class MemeticSearch:
    """
    Memetic algorithm implementation for Critical Node Problems.

    The MemeticSearch class implements a population-based evolutionary algorithm
    that combines global search through crossover operations with local search
    refinement. It supports both CNP and DCNP problem types with configurable
    search strategies and crossover operators.

    The algorithm maintains a population of solutions that evolves over generations:
    * **Initialization**: Creates initial solutions using local search
    * **Selection**: Selects parent solutions using tournament selection
    * **Crossover**: Creates offspring by combining parent solutions
    * **Local Search**: Improves offspring using a configured search strategy
    * **Population Update**: Updates population based on fitness and diversity
    * **Variable Population**: Optionally adapts population size based on progress

    Parameters
    ----------
    problem_data : ProblemData
        The graph problem data containing nodes and edges.
    problem_type : str
        Either "CNP" for Critical Node Problem or "DCNP" for Distance-based CNP.
    budget : int
        Maximum number of nodes that can be removed.
    seed : int
        Random seed for reproducibility.
    """

    def __init__(
        self,
        problem_data: "ProblemData",
        problem_type: Union[str, int],
        budget: int,
        seed: int,
        memetic_search_params: Optional[MemeticSearchParams] = None,
        variable_population_params: Optional[VariablePopulationParams] = None,
        hop_distance: int = DEFAULT_HOP_DISTANCE,
        display_interval: float = DEFAULT_DISPLAY_INTERVAL,
    ):
        """
        Initialize the memetic search algorithm.

        Parameters
        ----------
        problem_data : ProblemData
            The problem data reference containing graph structure.
        problem_type : str or int
            Problem type: "CNP" or "DCNP". Can also use pycnp.CNP or
            pycnp.DCNP constants.
        budget : int
            Number of nodes to remove from the graph.
        seed : int
            Random seed for reproducibility.
        memetic_search_params : MemeticSearchParams, optional
            Configuration for the memetic algorithm including search strategy,
            crossover operator, and population settings. If ``None``, defaults
            are used.
        variable_population_params : VariablePopulationParams, optional
            Configuration for adaptive population sizing. If ``None``, defaults
            are used.
        hop_distance : int, default=DEFAULT_HOP_DISTANCE
            Distance limit for DCNP problems. Two nodes are considered connected
            only if within this hop distance. Ignored for CNP.
        display_interval : float, default=DEFAULT_DISPLAY_INTERVAL
            Time interval (seconds) between progress display updates.

        Raises
        ------
        ValueError
            If ``display_interval`` is not positive.
        """
        self.problem_data = problem_data
        self._logger = logger

        if display_interval <= 0:
            raise ValueError("display_interval must be positive.")
        self.display_interval = display_interval

        self.problem_type = validate_problem_type(problem_type)

        self.budget = budget
        self.hop_distance = hop_distance

        self._memetic_search_params = memetic_search_params or MemeticSearchParams()
        self._variable_population_params = (
            variable_population_params or VariablePopulationParams()
        )

        self.search_strategy = validate_search_strategy(
            self._memetic_search_params.search, self.problem_type
        )
        self.search_name = self.search_strategy

        self.seed = seed
        random.seed(seed)

        self.is_problem_reduction = self._memetic_search_params.is_problem_reduction
        self.crossover_strategy = validate_crossover_strategy(
            self._memetic_search_params, self.problem_type
        )

        self.reduce_params = validate_reduce_params(
            self._memetic_search_params.reduce_params, self.problem_type
        )

        self.best_solution: set[int] = set()
        self.best_obj_value = float("inf")
        self.best_found_at_time = 0.0

        try:
            self.original_graph = self.problem_data.create_original_graph(
                self.problem_type, self.budget, self.seed, self.hop_distance
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create original graph: {e}") from e

        self.population: Optional[Population] = None

    def run(
        self,
        stopping_criterion: StoppingCriterion,
        collect_stats: bool = True,
        display: bool = False,
    ) -> "Result":
        """
        Execute the memetic search algorithm.

        This method runs the main optimization loop, repeatedly generating
        offspring solutions through crossover and improving them through local
        search until the stopping criterion is satisfied.

        Parameters
        ----------
        stopping_criterion : StoppingCriterion
            The criterion that determines when to stop the search.
            Common options: :class:`MaxIterations`, :class:`MaxRuntime`,
            or :class:`NoImprovement`.
        collect_stats : bool, default=True
            Whether to collect iteration-by-iteration statistics.
        display : bool, default=False
            Whether to display progress information during the search.

        Returns
        -------
        Result
            A Result object containing:
            * ``best_solution`` - Set of node IDs to remove
            * ``best_obj_value`` - Connectivity after removal (lower is better)
            * ``num_iterations`` - Number of iterations performed
            * ``runtime`` - Total runtime in seconds
            * ``best_found_at_time`` - Time when best solution was found
            * ``stats`` - Statistics object if ``collect_stats=True``

        Examples
        --------
        >>> from pycnp import read, MemeticSearchParams
        >>> from pycnp.stop import MaxIterations
        >>>
        >>> problem_data = read("graph.txt")
        >>> search = MemeticSearch(
        ...     problem_data=problem_data,
        ...     problem_type="CNP",
        ...     budget=5,
        ...     seed=42
        ... )
        >>> result = search.run(
        ...     stopping_criterion=MaxIterations(100),
        ...     display=True
        ... )
        """
        start_time_run = time.perf_counter()

        stats = Statistics(collect_stats=collect_stats)
        printer = ProgressPrinter(
            should_print=display,
            logger=self._logger,
            display_interval=self.display_interval,
        )

        printer.start(self.problem_type, self.budget, self.seed)

        printer.initializing_population_message()

        self.population = Population(
            self.original_graph,
            self.search_name,
            self._memetic_search_params.is_pop_variable,
            self._memetic_search_params.initial_pop_size,
            self._variable_population_params.max_pop_size,
            self._variable_population_params.increase_pop_size,
            self._variable_population_params.max_idle_gens,
            self.seed,
        )

        init_stopping_criterion = None
        if stopping_criterion.get_name() == "MaxRuntime":
            init_stopping_criterion = stopping_criterion

        best_solution_init, best_obj_value_init = self.population.initialize(
            display, init_stopping_criterion
        )

        if best_obj_value_init < self.best_obj_value:
            self.best_obj_value = best_obj_value_init
            self.best_solution = best_solution_init
            self.best_found_at_time = time.perf_counter() - start_time_run

        if stopping_criterion.get_name() == "MaxRuntime":
            if not stopping_criterion(self.best_obj_value):
                printer.print_iterations_start_banner_and_header()
        else:
            printer.print_iterations_start_banner_and_header()

        num_idle_generations = 0
        iterations = 0

        while not stopping_criterion(self.best_obj_value):
            iterations += 1

            if self.crossover_strategy == "RSC":
                parent1, parent2 = self.population.select()
                parent_ptrs = [parent1, parent2]
                offspring_graph = reduce_solve_combine(
                    self.original_graph,
                    parent_ptrs,
                    self.reduce_params["search"],
                    self.reduce_params["beta"],
                    self.seed,
                )
                self.seed += 1
            elif self.crossover_strategy == "DBX":
                parent1, parent2 = self.population.select()
                parent_ptrs = [parent1, parent2]
                offspring_graph = double_backbone_based_crossover(
                    self.original_graph, parent_ptrs, self.seed
                )
                self.seed += 1
            elif self.crossover_strategy == "IRR":
                parent1, parent2, parent3 = self.population.get_all_three_solutions()
                parent_ptrs = [parent1, parent2, parent3]
                offspring_graph = inherit_repair_recombination(
                    self.original_graph, parent_ptrs, self.seed
                )
                self.seed += 1
            else:
                raise ValueError(
                    f"Unknown crossover strategy: {self.crossover_strategy}"
                )

            local_search = Search(offspring_graph, self.seed)
            self.seed += 1
            local_search.set_strategy(self.search_strategy)
            ls_result = local_search.run()

            self.population.update(
                ls_result.solution, ls_result.obj_value, num_idle_generations, display
            )

            if ls_result.obj_value < self.best_obj_value:
                self.best_solution = ls_result.solution
                self.best_obj_value = ls_result.obj_value
                self.best_found_at_time = time.perf_counter() - start_time_run
                num_idle_generations = 0
            else:
                num_idle_generations += 1

            stats.collect(
                best_obj_value=self.best_obj_value,
                population_size=self.population.get_size(),
                num_idle_generations=num_idle_generations,
            )

            printer.iteration(stats)

        final_runtime = time.perf_counter() - start_time_run
        result = Result(
            best_solution=self.best_solution,
            best_obj_value=self.best_obj_value,
            num_iterations=iterations,
            runtime=final_runtime,
            best_found_at_time=self.best_found_at_time,
            stats=stats,
        )

        printer.end(result)

        return result
