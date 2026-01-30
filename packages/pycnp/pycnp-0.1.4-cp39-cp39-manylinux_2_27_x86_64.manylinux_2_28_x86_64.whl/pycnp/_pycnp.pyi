from typing import overload

BCLS: str
CBNS: str
CHNS: str
CNP: str
DBX: str
DCNP: str
DLAS: str
IRR: str
RSC: str

class CNP_Graph:
    """
    Graph implementation for the Critical Node Problem (CNP).

    Represents a graph where the objective is to minimize connectivity after node removal.
    """
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self, nodes: set[int], adj_list: list[set[int]], budget: int, seed: int
    ) -> None: ...
    def add_node(self, node_to_add: int) -> None:
        """Adds a node back to the graph."""
        ...
    def remove_node(self, node_to_remove: int) -> None:
        """Removes a node from the graph."""
        ...
    @property
    def removed_nodes(self) -> set[int]:
        """Returns the set of removed nodes."""
        ...

class DCNP_Graph:
    """
    Graph implementation for the Distance-Based Critical Node Problem (DCNP).

    Represents a graph where the objective is to maximize pairwise distance after node removal.
    """
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(
        self,
        nodes: set[int],
        K: int,
        adj_list: list[set[int]],
        num_to_remove: int,
        seed: int,
    ) -> None: ...
    def add_node(self, node_to_add: int) -> None:
        """Adds a node back to the DCNP graph."""
        ...
    def build_tree(self) -> None:
        """
        Builds the k-hop tree structure for DCNP calculations.

        Used for computing distances and betweenness centrality.
        """
        ...
    def calculate_khop_tree_size(self) -> int:
        """
        Calculates the size of the k-hop neighborhood.

        Returns
        -------
        int
            The total size of nodes within k hops.
        """
        ...
    def remove_node(self, node_to_remove: int) -> None:
        """Removes a node from the DCNP graph."""
        ...

class Graph:
    """
    Lightweight wrapper over concrete graph implementations (CNP_Graph / DCNP_Graph).
    """
    def __init__(self, *args, **kwargs) -> None: ...

class Population:
    """
    Manages population of solutions for memetic algorithm.

    The Population class handles evolutionary operations:
    - Initialization of diverse solutions using local search
    - Parent selection via tournament selection
    - Solution evaluation based on fitness (cost + diversity)
    - Population updates maintaining quality and diversity
    - Optional adaptive population sizing
    """
    def __init__(
        self,
        original_graph: Graph,
        search: str,
        is_pop_variable: bool,
        initial_pop_size: int,
        max_pop_size: int,
        increase_pop_size: int,
        max_idle_gens: int,
        seed: int,
    ) -> None:
        """
        Construct a Population instance.

        Parameters
        ----------
        original_graph : Graph
            Reference to the graph problem
        search : str
            Search strategy name (CBNS, CHNS, DLAS, or BCLS)
        is_pop_variable : bool
            Whether adaptive population sizing is enabled
        initial_pop_size : int
            Initial population size
        max_pop_size : int
            Maximum population size
        increase_pop_size : int
            Number of individuals to add when expanding
        max_idle_gens : int
            Idle generations before triggering expansion
        seed : int
            Random seed for reproducibility
        """
        ...
    def add(self, solution: set, obj_value: int) -> None:
        """
        Add a solution directly to the population.

        Parameters
        ----------
        solution : set
            The solution to add
        obj_value : int
            Objective value of the solution
        """
        ...
    def expand(self) -> None:
        """
        Expand the population with new diverse solutions.

        Adds new individuals when the population has stagnated.
        Called automatically when variable population sizing is enabled
        and no improvement is observed.
        """
        ...
    def get_all_three_solutions(self) -> tuple:
        """
        Get up to three prominent solutions from the population.

        Returns the best solution and two diverse alternatives.
        Used by the IRR crossover operator which requires three parents.

        Returns
        -------
        tuple
            Tuple of (solution1, solution2, solution3)
        """
        ...
    def get_memory_stats(self) -> tuple[int, int]: ...
    def get_size(self) -> int:
        """
        Get the current population size.

        Returns
        -------
        int
            Number of solutions in the population
        """
        ...
    def initialize(
        self, display: bool = ..., stopping_criterion: object = ...
    ) -> tuple[set, int]:
        """
        Initializes the population with diverse solutions.

        Generates initial solutions using local search with random starting points.

        Returns
        -------
        tuple[set, int]
            Pair of (best initial solution, its objective value)
        """
        ...
    def is_duplicate(self, solution: set[int]) -> bool:
        """
        Check if a solution already exists in the population.

        Parameters
        ----------
        solution : set[int]
            The solution to check

        Returns
        -------
        bool
            True if an identical solution is in the population
        """
        ...
    def rebuild(self) -> None:
        """
        Rebuild the population from scratch.

        Clears and reinitializes the population with new random solutions.
        Used as a diversification mechanism when search is stuck.
        """
        ...
    def select(self) -> tuple:
        """
        Select two parent solutions using tournament selection.

        Performs k-ary tournament selection twice to choose two distinct parents.
        Higher fitness solutions are more likely to be selected.

        Returns
        -------
        tuple
            Pair of (first parent, second parent) as solution sets
        """
        ...
    def update(
        self,
        solution: set,
        obj_value: int,
        num_idle_generations: int,
        verbose: bool = ...,
    ) -> None:
        """
        Update population with a new offspring solution.

        Evaluates the new solution and updates the population if the solution
        is sufficiently good or diverse. May expand population if enabled
        and no improvement is observed.

        Parameters
        ----------
        solution : set
            The offspring solution
        obj_value : int
            Objective value of the offspring
        num_idle_generations : int
            Number of generations without improvement
        verbose : bool, default=False
            Whether to print detailed information
        """
        ...

class ProblemData:
    """
    Stores the data for a graph problem instance.

    Contains node information, adjacency list, and provides methods to create graph objects.
    """
    def __init__(self, num_nodes: int) -> None:
        """
        Creates a ProblemData instance with the specified number of nodes.

        Parameters
        ----------
        num_nodes : int
            The number of nodes.
        """
        ...
    def add_edge(self, u: int, v: int) -> None:
        """
        Adds an edge between two nodes.

        Parameters
        ----------
        u : int
            The ID of the first node.
        v : int
            The ID of the second node.
        """
        ...
    def add_node(self, node_id: int) -> None:
        """
        Adds a node to the problem data.

        Parameters
        ----------
        node_id : int
            The ID of the node to add.
        """
        ...
    def add_node_weight(self, node_id: int, weight: float) -> None: ...
    def create_original_graph(
        self, problem_type: str, budget: int, seed: int, hop_distance: int = ...
    ) -> Graph:
        """
        Creates an original graph from the problem data.

        Parameters specify the problem type, number of nodes to remove, seed, and hop distance.

        Parameters
        ----------
        problem_type : str
            The type of problem ("CNP" or "DCNP").
        budget : int
            The number of nodes to remove.
        seed : int
            Random seed for reproducibility.
        hop_distance : int, optional
            Maximum hop distance for DCNP.

        Returns
        -------
        Graph
            A unique pointer to the created graph.
        """
        ...
    def get_adj_list(self) -> list[set[int]]:
        """
        Returns the adjacency list representation of the graph.

        Returns
        -------
        list[set[int]]
            Adjacency list where each index contains the neighbors of that node.
        """
        ...
    def get_node_weight(self, node_id: int) -> float: ...
    def get_nodes_set(self) -> set[int]:
        """
        Returns the set of all nodes.

        Returns
        -------
        set[int]
            Set of node IDs.
        """
        ...
    def num_nodes(self) -> int:
        """
        Returns the number of nodes in the problem data.

        Returns
        -------
        int
            Number of nodes.
        """
        ...
    @classmethod
    def read_from_adjacency_list_file(cls, filename: str) -> ProblemData:
        """
        Reads problem data from an adjacency list format file.

        Adjacency list format: each line represents a node and its neighbors.

        Parameters
        ----------
        filename : str
            Path to the adjacency list file.

        Returns
        -------
        ProblemData
            The loaded problem data.
        """
        ...
    @classmethod
    def read_from_edge_list_format(cls, filename: str) -> ProblemData:
        """
        Reads problem data from an edge list format file.

        Edge list format: contains a header line with node/edge counts,
        followed by edge definitions.

        Parameters
        ----------
        filename : str
            Path to the edge list file.

        Returns
        -------
        ProblemData
            The loaded problem data.
        """
        ...
    def read_node_weights_from_file(self, filename: str) -> None: ...

class Search:
    """
    Manages and executes various search algorithms.

    This class uses the strategy pattern to implement management and execution
    of different search algorithms.
    """
    def __init__(self, graph: Graph, seed: int) -> None:
        """
        Constructor with seed.

        Parameters
        ----------
        graph : Graph
            Reference to the graph object for search algorithm computation.
        seed : int
            Random number seed.
        """
        ...
    def run(self) -> SearchResult:
        """
        Run search algorithm.

        Returns
        -------
        SearchResult
            Search result containing optimal solution and objective function value.
        """
        ...
    def set_strategy(self, strategy: str) -> None:
        """
        Set search strategy.

        Parameters
        ----------
        strategy : str
            Strategy name, such as "CBNS", "DLAS", "CHNS", or "BCLS".
        """
        ...

class SearchResult:
    """
    Result container for search algorithms.

    Stores the outcome of a search algorithm, including the found solution
    and its objective value.
    """
    obj_value: int
    """Objective value of the solution."""
    def __init__(self) -> None: ...
    @property
    def solution(self) -> set:
        """Found solution, represented as a set of nodes."""
        ...

class SearchStrategy:
    """Base class for search strategies."""
    ...

class CBNSStrategy(SearchStrategy):
    """Component-Based Neighborhood Search strategy."""
    ...

class CHNSStrategy(SearchStrategy):
    """Component-Based Hybrid Neighborhood Search strategy."""
    ...

class DLASStrategy(SearchStrategy):
    """Diversified Late Acceptance Search strategy."""
    ...

class BCLSStrategy(SearchStrategy):
    """Betweenness Centrality-based Late Acceptance Search strategy."""
    ...