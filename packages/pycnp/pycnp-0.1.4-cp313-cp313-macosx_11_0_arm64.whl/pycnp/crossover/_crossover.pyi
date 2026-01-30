from pycnp._pycnp import Graph

# Re-export constants for backwards compatibility
DBX: str
IRR: str
RSC: str

def double_backbone_based_crossover(
    orig_graph: Graph,
    parents: list[set[int]],
    seed: int,
) -> Graph: ...

def inherit_repair_recombination(
    orig_graph: Graph,
    parents: list[set[int]],
    seed: int,
) -> Graph: ...

def reduce_solve_combine(
    orig_graph: Graph,
    parents: list[set[int]],
    search: str = "CHNS",
    beta: float = 0.9,
    seed: int = ...,
) -> Graph: ...
