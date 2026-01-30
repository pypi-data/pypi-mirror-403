from __future__ import annotations

import logging
import sys
from importlib import metadata

from .MemeticSearch import MemeticSearch, MemeticSearchParams, VariablePopulationParams
from .Model import Model
from .Result import Result
from ._pycnp import (  # noqa: F401
    BCLSStrategy,
    CBNSStrategy,
    CHNSStrategy,
    CNP_Graph,
    DCNP_Graph,
    DLASStrategy,
    Graph,
    Population,
    ProblemData,
    Search,
    SearchResult,
    SearchStrategy,
)
from .constants import (
    BCLS,
    CBNS,
    CHNS,
    CNP,
    DBX,
    DCNP,
    DEFAULT_DISPLAY_INTERVAL,
    DEFAULT_HOP_DISTANCE,
    DLAS,
    IRR,
    PACKAGE_LOGGER_NAME,
    PROBLEM_TYPE_CNP,
    PROBLEM_TYPE_DCNP,
    RSC,
    SEARCH_STRATEGY_BCLS,
    SEARCH_STRATEGY_CBNS,
    SEARCH_STRATEGY_CHNS,
    SEARCH_STRATEGY_DLAS,
)
from .crossover import (
    double_backbone_based_crossover,
    inherit_repair_recombination,
    reduce_solve_combine,
)
from .exceptions import (
    InvalidProblemTypeError,
    InvalidSearchStrategyError,
)
from .read import read, read_adjacency_list_format, read_edge_list_format
from .stop import (
    MaxIterations,
    MaxRuntime,
    NoImprovement,
    StoppingCriterion,
)
from .visualization import visualize_graph

# Configure package-wide logger
_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
if not _logger.handlers:
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
_logger.setLevel(logging.INFO)
_logger.propagate = False

try:
    __version__ = metadata.version("pycnp")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "BCLS",
    "CBNS",
    "CHNS",
    "CNP",
    "DBX",
    "DCNP",
    "DEFAULT_DISPLAY_INTERVAL",
    "DEFAULT_HOP_DISTANCE",
    "DLAS",
    "IRR",
    "PROBLEM_TYPE_CNP",
    "PROBLEM_TYPE_DCNP",
    "RSC",
    "SEARCH_STRATEGY_BCLS",
    "SEARCH_STRATEGY_CBNS",
    "SEARCH_STRATEGY_CHNS",
    "SEARCH_STRATEGY_DLAS",
    "BCLSStrategy",
    "CBNSStrategy",
    "CHNSStrategy",
    "CNP_Graph",
    "DCNP_Graph",
    "DLASStrategy",
    "Graph",
    # Exceptions
    "InvalidProblemTypeError",
    "InvalidSearchStrategyError",
    "MaxIterations",
    "MaxRuntime",
    # Population search
    "MemeticSearch",
    "MemeticSearchParams",
    # Model class
    "Model",
    "NoImprovement",
    "Population",
    # C++ binding classes
    "ProblemData",
    # Result class
    "Result",
    "SearchStrategy",
    # Stopping criteria
    "StoppingCriterion",
    "VariablePopulationParams",
    "double_backbone_based_crossover",
    "inherit_repair_recombination",
    # Utility functions
    "read",
    "read_adjacency_list_format",
    "read_edge_list_format",
    "reduce_solve_combine",
    "visualize_graph",
]
