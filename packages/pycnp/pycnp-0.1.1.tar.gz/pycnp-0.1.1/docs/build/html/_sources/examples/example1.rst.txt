Example 1: A simple example
===========================

This is a simple example for solving CNP problems. All that is required is to specify the necessary problem parameters.

.. code-block:: python

   from pycnp import Model, read
   from pycnp.stop import NoImprovement

   # Load an instance from a file
   problem_data = read("ErdosRenyi_n235.txt")
   model = Model.from_data(problem_data)

   # Solve with minimal configuration
   result = model.solve(
       problem_type="CNP",
       budget=10,
       stopping_criterion=NoImprovement(20),
       seed=42,
   )

   print(f"Best objective: {result.best_obj_value}")
   print(f"Removed nodes: {result.best_solution}")

Results
~~~~~~~

You obtain output similar to::

   Best objective: 17817
   Removed nodes: {96, 226, 66, 198, 103, 233, 42, 113, 86, 26}
   Number of iterations: 20
   Runtime: 2.00 seconds
