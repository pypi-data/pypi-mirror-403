"""
Validation module.

Provides validation functions for checking problem types, search strategies,
crossover operators, and other parameters used in the PyCNP package.

This module ensures that user-provided parameters are valid and compatible
with the algorithm constraints before execution begins.

Functions
---------
validate_problem_type
    Validates and normalizes problem type strings.
validate_search_strategy
    Validates search strategy strings with problem type compatibility.
validate_crossover_strategy
    Validates crossover operator settings.
validate_reduce_params
    Validates reduce parameters for RSC crossover.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Union

from .constants import (
    PROBLEM_TYPE_CNP,
    PROBLEM_TYPE_DCNP,
    SEARCH_STRATEGY_BCLS,
    SEARCH_STRATEGY_CBNS,
    SEARCH_STRATEGY_CHNS,
    SEARCH_STRATEGY_DLAS,
)
from .exceptions import InvalidProblemTypeError, InvalidSearchStrategyError

if TYPE_CHECKING:
    from .params import MemeticSearchParams


def validate_problem_type(problem_type: Union[str, int]) -> str:
    """
    Validates and normalizes the problem type parameter.

    Converts string problem type identifiers to their canonical uppercase form
    and validates that the provided type is supported.

    Parameters
    ----------
    problem_type : Union[str, int]
        The problem type to validate. Can be a string (``"CNP"`` or ``"DCNP"``)
        or an integer constant.

    Returns
    -------
    str
        The validated problem type in canonical uppercase form.

    Raises
    ------
    InvalidProblemTypeError
        If the problem type is not a supported string or integer value.

    Examples
    --------
    >>> from pycnp.validation import validate_problem_type
    >>> validate_problem_type("CNP")
    'CNP'
    >>> validate_problem_type("dcnp")
    'DCNP'
    """
    if isinstance(problem_type, str):
        normalized_type = problem_type.upper()
        if normalized_type in (PROBLEM_TYPE_CNP, PROBLEM_TYPE_DCNP):
            return normalized_type
        raise InvalidProblemTypeError(
            f"Unsupported problem type string: {problem_type}. "
            f"Valid options are: {PROBLEM_TYPE_CNP}, {PROBLEM_TYPE_DCNP}"
        )
    raise InvalidProblemTypeError(
        f"Unsupported problem type: {problem_type}. Must be one of "
        f"'{PROBLEM_TYPE_CNP}' or '{PROBLEM_TYPE_DCNP}'."
    )


def validate_search_strategy(search: Union[int, str], problem_type: str) -> str:
    """
    Validates the search strategy with problem type compatibility checks.

    Ensures that the provided search strategy is valid and compatible with
    the specified problem type. DCNP only supports BCLS, while CNP supports
    CBNS, CHNS, and DLAS.

    Parameters
    ----------
    search : Union[int, str]
        The search strategy to validate. Can be a string (``"CBNS"``, ``"CHNS"``,
        ``"DLAS"``, ``"BCLS"``) or an integer constant.
    problem_type : str
        The problem type (``"CNP"`` or ``"DCNP"``) to validate against.

    Returns
    -------
    str
        The validated search strategy in canonical uppercase form.

    Raises
    ------
    InvalidSearchStrategyError
        If the search strategy is not a supported string or integer value.
    ValueError
        If the search strategy is incompatible with the problem type.

    Examples
    --------
    >>> from pycnp.validation import validate_search_strategy
    >>> validate_search_strategy("CHNS", "CNP")
    'CHNS'
    >>> validate_search_strategy("bcls", "DCNP")
    'BCLS'
    """
    search_strategy = ""
    if isinstance(search, str):
        search_value = search.upper()
        if search_value in (
            SEARCH_STRATEGY_CBNS,
            SEARCH_STRATEGY_CHNS,
            SEARCH_STRATEGY_DLAS,
            SEARCH_STRATEGY_BCLS,
        ):
            search_strategy = search_value
        else:
            raise InvalidSearchStrategyError(
                f"Unsupported search strategy string: {search}. "
                f"Valid options are: {SEARCH_STRATEGY_CBNS}, {SEARCH_STRATEGY_CHNS}, "
                f"{SEARCH_STRATEGY_DLAS}, {SEARCH_STRATEGY_BCLS}"
            )
    else:
        raise InvalidSearchStrategyError(
            f"Invalid search strategy value: {search}. "
            f"Must be one of '{SEARCH_STRATEGY_CBNS}', '{SEARCH_STRATEGY_CHNS}', "
            f"'{SEARCH_STRATEGY_DLAS}', or '{SEARCH_STRATEGY_BCLS}'."
        )

    # Check compatibility
    if problem_type == PROBLEM_TYPE_DCNP and search_strategy != SEARCH_STRATEGY_BCLS:
        raise ValueError(
            "DCNP problem type currently only supports BCLS search strategy"
        )
    if problem_type == PROBLEM_TYPE_CNP and search_strategy == SEARCH_STRATEGY_BCLS:
        raise ValueError("CNP problem type does not support BCLS search strategy")

    return search_strategy


def validate_crossover_strategy(
    memetic_search_params: MemeticSearchParams, problem_type: str
) -> str:
    """
    Validates crossover operator configuration and constraints.

    Checks that the crossover operator is properly configured based on the
    ``is_problem_reduction`` flag and validates compatibility with problem type.
    For IRR crossover, additional constraints are checked (DCNP only, fixed
    population size of 3).

    Parameters
    ----------
    memetic_search_params : MemeticSearchParams
        The memetic search parameters containing crossover configuration.
    problem_type : str
        The problem type (``"CNP"`` or ``"DCNP"``).

    Returns
    -------
    str
        The validated crossover strategy string (``"RSC"``, ``"DBX"``, or ``"IRR"``).

    Raises
    ------
    ValueError
        If crossover configuration is invalid or incompatible with problem type.

    Notes
    -----
    When ``is_problem_reduction=True``, RSC is always used. When False,
    explicit crossover must be set to DBX or IRR.

    IRR crossover has additional requirements:

    - Problem type must be DCNP
    - Population size must be exactly 3
    - Variable population must be disabled
    """
    is_problem_reduction = memetic_search_params.is_problem_reduction
    crossover_choice = memetic_search_params.crossover

    if is_problem_reduction:
        crossover_strategy = "RSC"
    else:
        if crossover_choice is None:
            raise ValueError(
                "When is_problem_reduction is False, crossover must be "
                "explicitly set to DBX or IRR."
            )

        if isinstance(crossover_choice, str):
            normalized = crossover_choice.upper()
        else:
            raise ValueError(
                f"Unsupported crossover value: {crossover_choice}. "
                f"Valid options: 'DBX', 'IRR' when is_problem_reduction=False."
            )

        if normalized not in ("DBX", "IRR", "RSC"):
            raise ValueError(
                f"Unsupported crossover strategy string: {normalized}. "
                "Valid options: DBX, IRR."
            )

        crossover_strategy = normalized

        if crossover_strategy == "RSC":
            raise ValueError(
                "When is_problem_reduction is False, crossover must be DBX "
                "or IRR (RSC is reserved for problem reduction mode)."
            )

    # Validate crossover vs problem type constraints
    if crossover_strategy == "IRR" and problem_type != "DCNP":
        raise ValueError("IRR crossover is only supported for DCNP problems.")

    # IRR constraints
    if crossover_strategy == "IRR":
        if memetic_search_params.initial_pop_size != 3:
            raise ValueError(
                "IRR (Inherit-Repair-Recombination crossover) strategy "
                "requires exactly 3 individuals in population, "
                f"but got initial_pop_size="
                f"{memetic_search_params.initial_pop_size}. "
                "Please set initial_pop_size=3 when using IRR crossover "
                "(is_problem_reduction=False, problem_type=DCNP)."
            )

        if memetic_search_params.is_pop_variable:
            raise ValueError(
                "IRR (Inherit-Repair-Recombination crossover) strategy "
                "does not support variable population size. "
                "Please set is_pop_variable=False when using IRR crossover "
                "(is_problem_reduction=False, problem_type=DCNP)."
            )

    return crossover_strategy


def validate_reduce_params(reduce_params_in: Any, problem_type: str) -> Dict[str, Any]:
    """
    Validates and normalizes reduce parameters for RSC crossover.

    Checks that ``reduce_params`` contains valid ``search`` and ``beta`` values
    and validates compatibility with the problem type.

    Parameters
    ----------
    reduce_params_in : Any
        The reduce parameters to validate. Must be a dict containing:

        * ``search`` (str): Local search strategy (``"CBNS"``, ``"CHNS"``,
          ``"DLAS"``, or ``"BCLS"``). Defaults to ``"CHNS"``.
        * ``beta`` (float): Fraction of common nodes to preserve in [0, 1].
          Defaults to ``0.9``.

    problem_type : str
        The problem type (``"CNP"`` or ``"DCNP"``).

    Returns
    -------
    Dict[str, Any]
        The validated and normalized reduce parameters dict.

    Raises
    ------
    TypeError
        If ``reduce_params`` is not a dict.
    ValueError
        If search strategy or beta value is invalid, or if search strategy
        is incompatible with problem type.

    Notes
    -----
    For DCNP problems, the search strategy must be ``"BCLS"``.
    For CNP problems, ``"BCLS"`` is not supported.

    Examples
    --------
    >>> from pycnp.validation import validate_reduce_params
    >>> validate_reduce_params({"search": "CHNS", "beta": 0.9}, "CNP")
    {'search': 'CHNS', 'beta': 0.9}
    >>> validate_reduce_params({"search": "bcls", "beta": 0.5}, "DCNP")
    {'search': 'BCLS', 'beta': 0.5}
    """
    if not isinstance(reduce_params_in, dict):
        raise TypeError("reduce_params must be a dict with keys 'search' and 'beta'.")

    reduce_params = dict(reduce_params_in)
    reduce_search = reduce_params.get("search", "CHNS")
    reduce_beta = reduce_params.get("beta", 0.9)

    if isinstance(reduce_search, str):
        reduce_search_name = reduce_search.upper()
    else:
        raise ValueError(
            f"Unsupported search strategy for reduce_params: {reduce_search}. "
            f"Valid options are: 'CBNS', 'CHNS', 'DLAS', or 'BCLS'."
        )

    if reduce_search_name not in (
        SEARCH_STRATEGY_CBNS,
        SEARCH_STRATEGY_CHNS,
        SEARCH_STRATEGY_DLAS,
        SEARCH_STRATEGY_BCLS,
    ):
        raise ValueError(
            f"Unsupported search strategy for reduce_params: {reduce_search}. "
            f"Valid options are: 'CBNS', 'CHNS', 'DLAS', or 'BCLS'."
        )

    reduce_params["search"] = reduce_search_name

    if not (0.0 <= reduce_beta <= 1.0):
        raise ValueError("reduce_params['beta'] must be in [0, 1].")
    reduce_params["beta"] = reduce_beta

    if problem_type == PROBLEM_TYPE_DCNP and reduce_search_name != SEARCH_STRATEGY_BCLS:
        raise ValueError(
            "For DCNP, reduce_params['search'] must be 'BCLS' when using RSC crossover."
        )
    if problem_type == PROBLEM_TYPE_CNP and reduce_search_name == SEARCH_STRATEGY_BCLS:
        raise ValueError(
            "reduce_params['search']='BCLS' is only supported for DCNP "
            "in RSC crossover."
        )

    return reduce_params
