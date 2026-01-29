"""
Model module

Provides the :class:`Model` class for defining and solving Critical Node Problems.

The Model class serves as the main entry point for users to construct graph problems,
configure solver parameters, and obtain solutions. It integrates with the underlying
C++ implementation through the :class:`ProblemData` class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .MemeticSearch import (
    MemeticSearch,
    MemeticSearchParams,
    VariablePopulationParams,
)
from ._pycnp import ProblemData
from .constants import DEFAULT_DISPLAY_INTERVAL, DEFAULT_HOP_DISTANCE

if TYPE_CHECKING:
    from .Result import Result
    from .stop import StoppingCriterion


class Model:
    """
    Graph problem modeling and solving class for Critical Node Problems.

    The Model class provides a unified interface for:

    - Building undirected graph instances by adding nodes and edges
    - Configuring solver parameters (search strategy, crossover operator,
      population settings)
    - Executing the memetic algorithm to solve CNP and DCNP problems
    - Retrieving solutions with associated statistics

    The class internally manages a :class:`ProblemData` object that is passed to the
    C++ solver backend. This ProblemData can be created from the model's internal
    representation or provided directly via :meth:`from_data`.

    Examples
    --------
    Create a simple graph and solve the CNP problem:

    >>> from pycnp import Model
    >>> from pycnp.stop import MaxIterations
    >>>
    >>> model = Model()
    >>> for i in range(10):
    ...     model.add_node(i)
    >>> model.add_edge(0, 1)
    >>> model.add_edge(1, 2)
    >>> model.add_edge(2, 3)
    >>>
    >>> result = model.solve(
    ...     problem_type="CNP",
    ...     budget=2,
    ...     stopping_criterion=MaxIterations(100),
    ...     seed=42
    ... )
    >>> print(f"Removed nodes: {result.best_solution}")
    """

    def __init__(self) -> None:
        """
        Initialize an empty graph model.

        Creates a new Model instance with no nodes or edges. Use :meth:`add_node`
        and :meth:`add_edge` to populate the model.
        """
        self.nodes: set[int] = set()
        self.adj_list: list[set[int]] = []
        self._problem_data: ProblemData | None = None

    def add_node(self, node: int) -> None:
        """
        Add a node to the graph.

        If the node already exists in the graph, this method has no effect.
        The adjacency list is automatically expanded to accommodate the new node ID.

        Parameters
        ----------
        node : int
            The ID of the node to add. Must be a non-negative integer.
        """
        self.nodes.add(node)

        while len(self.adj_list) <= node:
            self.adj_list.append(set())

    def add_edge(self, u: int, v: int) -> None:
        """
        Add an undirected edge between two nodes.

        If either endpoint does not exist, it will be automatically added to the graph.
        Adding the same edge multiple times has no additional effect (edges are stored
        as sets).

        Parameters
        ----------
        u : int
            The ID of the first endpoint.
        v : int
            The ID of the second endpoint.
        """
        if u not in self.nodes:
            self.add_node(u)
        if v not in self.nodes:
            self.add_node(v)

        while len(self.adj_list) <= max(u, v):
            self.adj_list.append(set())

        self.adj_list[u].add(v)
        self.adj_list[v].add(u)

    @staticmethod
    def from_data(problem_data: "ProblemData") -> "Model":
        """
        Create a Model instance from an existing ProblemData object.

        This factory method is useful when working with ProblemData obtained
        from external sources (e.g., file I/O via :func:`pycnp.read`).
        The created model holds a reference to the provided ProblemData.

        Parameters
        ----------
        problem_data : ProblemData
            The ProblemData object to wrap.

        Returns
        -------
        Model
            A new Model instance that wraps the provided ProblemData.

        Examples
        --------
        >>> from pycnp import read, Model
        >>> problem_data = read("graph.txt")
        >>> model = Model.from_data(problem_data)
        """
        model = Model()
        model._problem_data = problem_data
        return model

    @property
    def problem_data(self) -> "ProblemData":
        """
        Get the ProblemData object for visualization.

        Creates the ProblemData from the model's graph representation if it
        doesn't exist yet.

        Returns
        -------
        ProblemData
            The ProblemData object representing the graph.
        """
        if self._problem_data is None:
            self._problem_data = self._create_problem_data()
        return self._problem_data

    def _create_problem_data(self) -> "ProblemData":
        """
        Create a ProblemData object from the model's internal representation.

        This method converts the Python-level graph representation (nodes and
        adjacency list) into a C++ ProblemData object that can be used by the
        solver backend.

        Returns
        -------
        ProblemData
            A newly created ProblemData object containing the graph structure.
        """
        max_node_id = max(self.nodes) if self.nodes else 0
        problem_data = ProblemData(max_node_id + 1)

        for node in self.nodes:
            problem_data.add_node(node)

        for u in range(len(self.adj_list)):
            for v in self.adj_list[u]:
                if u < v:
                    problem_data.add_edge(u, v)

        return problem_data

    def solve(
        self,
        problem_type: str,
        budget: int,
        stopping_criterion: StoppingCriterion,
        seed: int = 0,
        memetic_search_params: MemeticSearchParams | None = None,
        variable_population_params: VariablePopulationParams | None = None,
        hop_distance: int = DEFAULT_HOP_DISTANCE,
        display_interval: float = DEFAULT_DISPLAY_INTERVAL,
        display: bool = True,
        collect_stats: bool = True,
    ) -> "Result":
        """
        Solve the Critical Node Problem defined by this model.

        This method executes the memetic algorithm to find a set of nodes to remove
        that minimizes connectivity while respecting the budget constraint.

        Parameters
        ----------
        problem_type : str
            The type of problem to solve. Either ``"CNP"`` for the standard
            Critical Node Problem or ``"DCNP"`` for the Distance-based variant.
        budget : int
            The maximum number of nodes that can be removed. Must be non-negative
            and not exceed the total number of nodes.
        stopping_criterion : StoppingCriterion
            The criterion used to determine when to stop the search.
            Common options include :class:`MaxIterations`,
            :class:`MaxRuntime`, or :class:`NoImprovement`.
        seed : int, default=0
            Random seed for reproducibility. The same seed will produce the
            same results when all other parameters are identical.
        memetic_search_params : MemeticSearchParams, optional
            Configuration for the memetic algorithm. If ``None``, default
            values are used. See :class:`MemeticSearchParams` for options.
        variable_population_params : VariablePopulationParams, optional
            Configuration for adaptive population sizing. If ``None``,
            default values are used. See :class:`VariablePopulationParams`
            for details.
        hop_distance : int, default=DEFAULT_HOP_DISTANCE
            The hop distance limit for DCNP problems. Ignored for CNP.
            Two nodes are considered connected only if within this distance.
        display_interval : float, default=DEFAULT_DISPLAY_INTERVAL
            Time interval (in seconds) between progress updates when ``display=True``.
        display : bool, default=True
            Whether to print progress information during the search.
        collect_stats : bool, default=True
            Whether to collect detailed iteration-by-iteration statistics.

        Returns
        -------
        Result
            A Result object containing the best solution found, its
            objective value, runtime statistics, and optionally iteration
            statistics if ``collect_stats=True``.

        Raises
        ------
        ValueError
            If ``budget`` exceeds the number of nodes or if ``problem_type`` is invalid.

        Examples
        --------
        Solve a CNP problem with a time limit:

        >>> from pycnp import Model
        >>> from pycnp.stop import MaxRuntime
        >>>
        >>> model = Model()
        >>> # ... build graph ...
        >>> result = model.solve(
        ...     problem_type="CNP",
        ...     budget=5,
        ...     stopping_criterion=MaxRuntime(60),  # 60 seconds
        ...     seed=42
        ... )
        >>> print(f"Objective: {result.best_obj_value}")
        """
        if hasattr(self, "_problem_data") and self._problem_data is not None:
            problem_data = self._problem_data
        else:
            problem_data = self._create_problem_data()
            self._problem_data = problem_data

        if memetic_search_params is None:
            memetic_search_params = MemeticSearchParams()

        if variable_population_params is None:
            variable_population_params = VariablePopulationParams()

        search = MemeticSearch(
            problem_data=problem_data,
            problem_type=problem_type,
            budget=budget,
            seed=seed,
            memetic_search_params=memetic_search_params,
            variable_population_params=variable_population_params,
            hop_distance=hop_distance,
            display_interval=display_interval,
        )

        return search.run(
            stopping_criterion=stopping_criterion,
            display=display,
            collect_stats=collect_stats,
        )
