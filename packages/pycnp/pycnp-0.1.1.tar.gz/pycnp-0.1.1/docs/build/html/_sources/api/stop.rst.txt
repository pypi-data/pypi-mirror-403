.. _api_stop:

Stopping Criteria
=================

The :mod:`pycnp.stop` module provides stopping criteria for controlling when the memetic algorithm terminates.

.. contents::
   :local:
   :depth: 1

.. class:: StoppingCriterion

    Protocol for algorithm stopping criteria.

    .. method:: __call__(best_obj_value: float) -> bool

        Determines whether the algorithm should stop.

        :param best_obj_value: The best objective value found so far.
        :return: ``True`` if the stopping condition is met.

    .. method:: get_name() -> str

        Returns the name of the stopping criterion.

        :return: The criterion name as a string.

.. autoclass:: pycnp.stop.MaxIterations
   :members:

.. autoclass:: pycnp.stop.MaxRuntime
   :members:

.. autoclass:: pycnp.stop.NoImprovement
   :members:
