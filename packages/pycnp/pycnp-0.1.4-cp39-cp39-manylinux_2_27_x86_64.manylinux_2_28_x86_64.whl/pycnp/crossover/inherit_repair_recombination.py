from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pycnp._pycnp import Graph

# Crossover constant
IRR = "IRR"


def inherit_repair_recombination(
    orig_graph: Graph,
    parents: list[set[int]],
    seed: int,
) -> Graph:
    """
    Performs an Inherit-Repair-Recombination (IRR) crossover operation.

    This crossover operator uses three parent solutions to create an offspring.

    The algorithm follows a three-phase process:
    1. **Inherit**: Select nodes from parents based on inheritance probabilities
    2. **Repair**: Fix any constraint violations in the inherited solution
    3. **Recombine**: Combine repaired solutions to form the final offspring

    IRR is specifically designed for the Distance-Based Critical Node Problem
    (DCNP) and requires exactly 3 parent solutions.

    Parameters
    ----------
    orig_graph : Graph
        The original graph containing all nodes and edges.
    parents : list[set[int]]
        A list of three parent solutions for DCNP. Each solution is a set of
        node IDs. Must have exactly 3 parents.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    Graph
        A new graph representing the offspring solution.

    Raises
    ------
    ValueError
        If the number of parents is not exactly 3.

    Notes
    -----
    This function is typically called internally by the memetic algorithm
    rather than directly by users.

    This operator requires:
    * Problem type: DCNP (Distance-Based Critical Node Problem)
    * Population size: exactly 3 individuals
    * Variable population: must be disabled (``is_pop_variable=False``)
    """
    from pycnp.crossover._crossover import (
        inherit_repair_recombination as _irr,
    )

    if len(parents) != 3:
        raise ValueError(
            "IRR crossover requires exactly 3 parent solutions. "
            f"Got {len(parents)} parents."
        )

    return _irr(orig_graph, parents, seed)
