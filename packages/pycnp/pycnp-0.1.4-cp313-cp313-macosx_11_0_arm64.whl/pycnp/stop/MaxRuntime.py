from __future__ import annotations

import time

from .StoppingCriterion import StoppingCriterion


class MaxRuntime(StoppingCriterion):
    """
    A stopping criterion based on the maximum allowed runtime.

    The algorithm stops when the elapsed time since initialization
    exceeds a predefined limit.
    """

    def __init__(self, max_runtime_in_sec: float):
        """
        Initializes the MaxRuntime criterion.

        Parameters
        ----------
        max_runtime_in_sec : float
            The maximum allowed runtime in seconds.

        Raises
        ------
        ValueError
            If max_runtime_in_sec is not a positive number.
        """
        if not isinstance(max_runtime_in_sec, (int, float)) or max_runtime_in_sec <= 0:
            raise ValueError("max_runtime_in_sec must be a positive number.")

        self.max_runtime = max_runtime_in_sec
        self.start_time = time.perf_counter()

    def __call__(self, best_obj_value: float) -> bool:
        """
        Checks if the maximum runtime has been exceeded.

        Parameters
        ----------
        best_obj_value : float
            The current best objective value (not used by this criterion).

        Returns
        -------
        bool
            True if the elapsed time is greater than or equal to the maximum
            allowed runtime, False otherwise.
        """
        elapsed_time = time.perf_counter() - self.start_time
        return elapsed_time >= self.max_runtime

    def get_name(self) -> str:
        """
        Returns the name of the stopping criterion.

        Returns
        -------
        str
            The name of the criterion.
        """
        return "MaxRuntime"
