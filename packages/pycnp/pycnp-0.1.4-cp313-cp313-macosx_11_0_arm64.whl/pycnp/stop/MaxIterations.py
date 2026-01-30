from __future__ import annotations

from .StoppingCriterion import StoppingCriterion


class MaxIterations(StoppingCriterion):
    """
    A stopping criterion based on the maximum number of iterations.

    The algorithm stops when the number of iterations reaches a predefined limit.
    """

    def __init__(self, max_iterations: int):
        """
        Initializes the MaxIterations criterion.

        Parameters
        ----------
        max_iterations : int
            The maximum number of iterations to allow.

        Raises
        ------
        ValueError
            If max_iterations is not a positive integer.
        """
        if not isinstance(max_iterations, int) or max_iterations <= 0:
            raise ValueError("max_iterations must be a positive integer.")

        self.max_iterations = max_iterations
        self.iterations = 0

    def __call__(self, best_obj_value: float) -> bool:
        """
        Checks if the maximum number of iterations has been reached.

        Increments the iteration counter on each call.

        Parameters
        ----------
        best_obj_value : float
            The current best objective value (not used by this criterion).

        Returns
        -------
        bool
            True if the current number of iterations has reached the maximum,
            False otherwise.
        """
        self.iterations += 1
        return self.iterations >= self.max_iterations

    def get_name(self) -> str:
        """
        Returns the name of the stopping criterion.

        Returns
        -------
        str
            The name of the criterion.
        """
        return "MaxIterations"
