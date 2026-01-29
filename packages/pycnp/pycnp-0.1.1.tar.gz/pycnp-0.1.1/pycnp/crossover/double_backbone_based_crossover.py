from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pycnp._pycnp import Graph

# Crossover constant
DBX = "DBX"


def double_backbone_based_crossover(
    orig_graph: Graph,
    parents: list[set[int]],
    seed: int,
) -> Graph:
    """
    Performs a Double Backbone Based (DBX) crossover operation.

    This crossover operator identifies common nodes between parent solutions
    and constructs an offspring solution based on the backbone structure.

    The algorithm:
    1. Finds nodes present in both parent solutions (the "backbone")
    2. Preserves these backbone nodes in the offspring
    3. Inherits remaining nodes from one parent

    This operator is particularly effective for problems where solutions
    share common structural elements.

    Parameters
    ----------
    orig_graph : Graph
        The original graph containing all nodes and edges.
    parents : list[set[int]]
        A list of two parent solutions, where each solution is a set of node IDs.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    Graph
        A new graph representing the offspring solution.

    Notes
    -----
    This function is typically called internally by the memetic algorithm
    rather than directly by users.
    """
    from pycnp.crossover._crossover import (
        double_backbone_based_crossover as _dbx,
    )

    return _dbx(orig_graph, parents, seed)