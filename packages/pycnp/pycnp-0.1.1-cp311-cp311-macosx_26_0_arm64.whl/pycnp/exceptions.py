"""
Exceptions module.

Provides custom exception and warning classes for the PyCNP package.

These exceptions are raised when invalid or unsupported parameters are
provided to various functions and classes in the package.

Classes
-------
InvalidProblemTypeError
    Raised when an unsupported problem type is provided.
InvalidSearchStrategyError
    Raised when an unsupported search strategy is provided.
"""

from __future__ import annotations


class InvalidProblemTypeError(ValueError):
    """
    Exception raised when an unsupported problem type is provided.

    This error is typically raised by :func:`pycnp.validation.validate_problem_type`
    when the provided problem type is not ``"CNP"`` or ``"DCNP"``.

    Examples
    --------
    >>> from pycnp.exceptions import InvalidProblemTypeError
    >>> raise InvalidProblemTypeError("Unsupported problem type: TEST")
    InvalidProblemTypeError: Unsupported problem type: TEST
    """


class InvalidSearchStrategyError(ValueError):
    """
    Exception raised when an unsupported search strategy is provided.

    This error is typically raised by
    :func:`pycnp.validation.validate_search_strategy` when the provided
    search strategy is not one of ``"CBNS"``, ``"CHNS"``, ``"DLAS"``,
    or ``"BCLS"``.

    Examples
    --------
    >>> from pycnp.exceptions import InvalidSearchStrategyError
    >>> raise InvalidSearchStrategyError("Unsupported search strategy: ABC")
    InvalidSearchStrategyError: Unsupported search strategy: ABC
    """
