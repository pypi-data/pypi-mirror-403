from __future__ import annotations

from .StoppingCriterion import StoppingCriterion


class NoImprovement(StoppingCriterion):
    """
    A stopping criterion based on the number of iterations without improvement.

    The algorithm stops if the best objective value has not improved for a
    specified number of consecutive iterations.
    """

    def __init__(self, max_idle_iterations: int):
        """
        Initializes the NoImprovement criterion.

        Parameters
        ----------
        max_idle_iterations : int
            The maximum number of consecutive iterations without improvement
            before stopping.

        Raises
        ------
        ValueError
            If max_idle_iterations is not a positive integer.
        """
        if not isinstance(max_idle_iterations, int) or max_idle_iterations <= 0:
            raise ValueError("max_idle_iterations must be a positive integer.")

        self.max_idle_iterations = max_idle_iterations
        self.idle_iterations = 0
        self.last_best_obj_value = float("inf")

    def __call__(self, best_obj_value: float) -> bool:
        """
        Checks if the no-improvement condition is met.

        Compares the current best objective value with the one from the previous
        iteration. If there is no improvement, the idle iteration counter is
        incremented.

        Parameters
        ----------
        best_obj_value : float
            The best objective value found so far.

        Returns
        -------
        bool
            True if the number of idle iterations has reached the maximum,
            False otherwise.
        """
        if best_obj_value < self.last_best_obj_value:
            self.last_best_obj_value = best_obj_value
            self.idle_iterations = 0
        else:
            self.idle_iterations += 1

        return self.idle_iterations >= self.max_idle_iterations

    def get_name(self) -> str:
        """
        Returns the name of the stopping criterion.

        Returns
        -------
        str
            The name of the criterion.
        """
        return "NoImprovement"
