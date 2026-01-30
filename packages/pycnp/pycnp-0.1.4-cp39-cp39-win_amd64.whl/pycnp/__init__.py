from __future__ import annotations


# start delvewheel patch
def _delvewheel_patch_1_12_0():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'pycnp.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-pycnp-0.1.4')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-pycnp-0.1.4')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_12_0()
del _delvewheel_patch_1_12_0
# end delvewheel patch

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
