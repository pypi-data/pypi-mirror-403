from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pycnp._pycnp import Graph

# Crossover constant
RSC = "RSC"

# Valid search strategies
SEARCH_STRATEGIES = Literal["CBNS", "CHNS", "DLAS", "BCLS"]


def reduce_solve_combine(
    orig_graph: Graph,
    parents: list[set[int]],
    search: SEARCH_STRATEGIES = "CHNS",
    beta: float = 0.9,
    seed: int = 0,
) -> Graph:
    """
    Performs a Reduce-Solve-Combine (RSC) crossover operation.

    This is the primary crossover operator for the Critical Node Problem (CNP)
    that uses a problem reduction strategy.

    The algorithm:
    1. **Reduce**: Identify common nodes between parents and reduce the problem
    2. **Solve**: Apply local search to the reduced subproblem
    3. **Combine**: Merge the solution with non-common nodes from parents

    RSC is used when ``is_problem_reduction=True`` in MemeticSearchParams.

    Parameters
    ----------
    orig_graph : Graph
        The original graph containing all nodes and edges.
    parents : list[set[int]]
        A list of two parent solutions. Each solution is a set of node IDs.
    search : str, optional
        The local search strategy to use on the reduced subproblem.
        Options: "CBNS", "CHNS", "DLAS" (for CNP), "BCLS" (for DCNP).
        Defaults to "CHNS".
    beta : float, optional
        The fraction of common nodes to preserve from parents.
        Must be in range [0, 1]. Higher values preserve more common nodes.
        Defaults to 0.9.
    seed : int, optional
        Random seed for reproducibility. Defaults to 0.

    Returns
    -------
    Graph
        A new graph representing the offspring solution.

    Notes
    -----
    This function is typically called internally by the memetic algorithm
    rather than directly by users.

    For DCNP problems, the search strategy must be "BCLS".
    """
    from pycnp.crossover._crossover import (
        reduce_solve_combine as _rsc,
    )

    return _rsc(orig_graph, parents, search, beta, seed)