from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

# Default RSC crossover parameters
_DEFAULT_RSC_SEARCH = "CHNS"
"""Default search strategy for RSC crossover."""
_DEFAULT_RSC_BETA = 0.9
"""Default fraction of common nodes to preserve in RSC crossover."""


@dataclass
class MemeticSearchParams:
    """
    Memetic search parameter configuration class.

    Used to configure various parameters of the MemeticSearch algorithm.
    Implemented using dataclass to maintain interface compatibility with the
    original C++ version.

    Examples
    --------
    >>> from pycnp import MemeticSearchParams
    >>> params = MemeticSearchParams(
    ...     search="CHNS",
    ...     is_problem_reduction=True,
    ...     is_pop_variable=True,
    ...     initial_pop_size=5,
    ...     reduce_params={"search": "CHNS", "beta": 0.9}
    ... )
    """

    def __init__(
        self,
        search: Union[int, str] = "CHNS",
        crossover: Optional[Union[int, str]] = None,
        is_problem_reduction: bool = True,
        is_pop_variable: bool = True,
        initial_pop_size: int = 5,
        reduce_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Parameters
        ----------
        search : Union[int, str], default="CHNS"
            The local search strategy to use. Valid options are:
            ``"CBNS"``, ``"CHNS"``, ``"DLAS"`` (for CNP), or ``"BCLS"`` (for DCNP).
        crossover : Optional[Union[int, str]], optional
            The crossover operator when ``is_problem_reduction=False``.
            Valid options are ``"DBX"`` or ``"IRR"``. Required only when
            ``is_problem_reduction`` is False.
        is_problem_reduction : bool, default=True
            If True, uses RSC (Reduce-Solve-Combine) crossover.
            If False, requires explicit ``crossover`` setting.
        is_pop_variable : bool, default=True
            Whether to enable adaptive population sizing.
        initial_pop_size : int, default=5
            Initial number of individuals in the population.
        reduce_params : Dict[str, Any], optional
            Parameters for RSC crossover. Contains ``"search"`` (search strategy)
            and ``"beta"`` (fraction of common nodes to preserve). Defaults to
            ``{"search": "CHNS", "beta": 0.9}``.
        """
        self.search = search
        self.crossover = crossover
        self.is_problem_reduction = is_problem_reduction
        self.is_pop_variable = is_pop_variable
        self.initial_pop_size = initial_pop_size
        if reduce_params is None:
            self.reduce_params = {
                "search": _DEFAULT_RSC_SEARCH,
                "beta": _DEFAULT_RSC_BETA
            }
        else:
            self.reduce_params = reduce_params

    search: Union[int, str] = field(default=_DEFAULT_RSC_SEARCH)
    crossover: Optional[Union[int, str]] = None
    is_problem_reduction: bool = True
    is_pop_variable: bool = True
    initial_pop_size: int = 5
    reduce_params: Dict[str, Any] = field(
        default_factory=lambda: {
            "search": _DEFAULT_RSC_SEARCH,
            "beta": _DEFAULT_RSC_BETA
        }
    )


@dataclass
class VariablePopulationParams:
    """
    Parameter configuration for the variable population size mechanism.

    Controls how the population size adapts during the memetic algorithm
    execution based on convergence behavior.

    Examples
    --------
    >>> from pycnp import VariablePopulationParams
    >>> params = VariablePopulationParams(
    ...     max_pop_size=30,
    ...     increase_pop_size=5,
    ...     max_idle_gens=15
    ... )
    """

    def __init__(
        self,
        max_pop_size: int = 20,
        increase_pop_size: int = 3,
        max_idle_gens: int = 20,
    ) -> None:
        """
        Parameters
        ----------
        max_pop_size : int, default=20
            Maximum number of individuals the population can contain.
        increase_pop_size : int, default=3
            Number of new individuals to add when expanding the population
            during idle periods.
        max_idle_gens : int, default=20
            Maximum number of consecutive generations without improvement
            before triggering population update or expansion.
        """
        self.max_pop_size = max_pop_size
        self.increase_pop_size = increase_pop_size
        self.max_idle_gens = max_idle_gens

    max_pop_size: int = 20
    increase_pop_size: int = 3
    max_idle_gens: int = 20
