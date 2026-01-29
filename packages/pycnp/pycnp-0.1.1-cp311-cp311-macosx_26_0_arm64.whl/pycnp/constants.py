from __future__ import annotations

"""
Centralised constants used across the pycnp package.
"""

DEFAULT_HOP_DISTANCE = 2**30
"""
Sentinel value representing "no hop limit" for DCNP problems.

Using 2^30 as it exceeds any realistic graph diameter (graph with 2^30
nodes would require terabytes of memory), effectively meaning unlimited
hop distance when not explicitly set.
"""

# Problem types
PROBLEM_TYPE_CNP = "CNP"
PROBLEM_TYPE_DCNP = "DCNP"

# Search strategies
SEARCH_STRATEGY_CBNS = "CBNS"
SEARCH_STRATEGY_CHNS = "CHNS"
SEARCH_STRATEGY_DLAS = "DLAS"
SEARCH_STRATEGY_BCLS = "BCLS"

# Progress and logging
DEFAULT_DISPLAY_INTERVAL = 1.0
PACKAGE_LOGGER_NAME = "pycnp"


# Public-facing constants with docstrings for Sphinx documentation
# These duplicate the C++ constants but provide proper Python docstrings

CNP = "CNP"
"""Critical Node Problem (CNP).

Minimize pairwise connectivity in undirected graphs.
"""

DCNP = "DCNP"
"""Distance-based Critical Node Problem (DCNP).

CNP variant with hop distance constraints.
"""

CBNS = "CBNS"
"""Component-Based Neighborhood Search.

A local search strategy operating on connected components.
"""

CHNS = "CHNS"
"""Component-Based Hybrid Neighborhood Search.

A hybrid local search strategy combining multiple approaches.
"""

DLAS = "DLAS"
"""Diversified Late Acceptance Search.

A late acceptance hill climbing strategy with diversification.
"""

BCLS = "BCLS"
"""Betweenness Centrality Late Acceptance Search.

Uses betweenness centrality to guide the local search.
"""

DBX = "DBX"
"""Double Backbone Based Crossover.

Identifies common nodes between parent solutions (the "backbone").
"""

IRR = "IRR"
"""Inherit-Repair-Recombination Crossover.

Uses three parents to create offspring through inheritance and repair.
"""

RSC = "RSC"
"""Reduce-Solve-Combine Crossover.

Reduces common nodes, solves subproblem, and combines results.
"""
