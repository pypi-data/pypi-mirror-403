Core concepts
=============

This page explains the key concepts and components of PyCNP's data model and algorithms.


Model
-----

The :class:`~pycnp.Model` class is the main entry point for defining and solving Critical Node Problems.
It provides methods to:

* Add nodes to the graph
* Add edges between nodes (undirected)
* Configure and solve the problem

.. code-block:: python

   from pycnp import Model

   model = Model()
   model.add_node(0)
   model.add_node(1)
   model.add_edge(0, 1)


Reading problem instances
-------------------------

PyCNP provides the :func:`~pycnp.read.read` function to load graph instances from files.
The function automatically detects the file format (adjacency list or edge list) and creates
a :class:`~pycnp.ProblemData` object.

.. code-block:: python

   from pycnp import Model, read

   # Load from file (auto-detects format)
   problem_data = read("graph.txt")
   model = Model.from_data(problem_data)

File formats
^^^^^^^^^^^^

PyCNP supports two graph file formats:

**Adjacency List Format**

Each line contains a node ID followed by its neighbors, separated by spaces.
The first line specifies the total number of nodes.

.. code-block:: text

   235
   0: 215
   1: 22 25 42 67 117 149 192 226
   2: 24 95 220
   3: 26 58
   4: 50 53 66 72 169
   ...

**Edge List Format**

The first line contains the header ``p edge num_nodes num_edges``.
Each subsequent line defines an edge with ``e node1 node2``.

.. code-block:: text

   p edge 36 91
   e 0 5
   e 1 3
   e 1 9
   e 1 12
   e 1 13
   e 1 14
   e 1 27
   e 1 28
   ...


Problem types
-------------

PyCNP supports two problem types:

**CNP (Critical Node Problem)**

   The standard Critical Node Problem on undirected graphs. Given a graph :math:`G = (V, E)` and a budget :math:`k`,
   the objective is to find a subset :math:`S \subseteq V` with :math:`|S| \leq k` that minimizes the number of
   connected pairs of nodes in :math:`G \setminus S`.

**DCNP (Distance-based Critical Node Problem)**

   An extension that introduces a hop distance constraint. Two nodes are only considered connected
   if they are within the specified ``hop_distance`` of each other. This variant is useful for modeling
   network disruption scenarios where only local connectivity matters.


Search strategies
-----------------

PyCNP implements four local search strategies:

**CBNS (Component-Based Neighborhood Search)**

   A component-based neighborhood search that explores connected components of the solution space.
   It identifies connected components in the current solution and performs neighborhood operations
   to improve the objective value.

**CHNS (Component-Based Hybrid Neighborhood Search)**

   A hybrid approach combining component-based search with additional neighborhood structures.
   It provides a balance between intensification and diversification during the search process.

**DLAS (Diversified Late Acceptance Search)**

   A late acceptance search strategy that balances exploration and exploitation by accepting
   non-improving moves based on recent solution quality history.

**BCLS (Betweenness Centrality-based Late Acceptance Search)**

   A strategy using betweenness centrality for guiding the search, specifically designed for
   DCNP problems where node importance is distance-dependent.


Crossover operators
-------------------

Three crossover operators are available for the memetic algorithm's population evolution:

**DBX (Double Backbone Based Crossover)**

   Identifies common nodes between parent solutions (the "backbone") and preserves them
   in the offspring. Uses the backbone structure to guide the creation of new solutions.

   * **Usage**: CNP problems with 2 parents
   * **Strategy**: Preserves common structure, inherits remaining nodes from one parent

**IRR (Inherit-Repair-Recombination)**

   A three-parent crossover designed specifically for DCNP. The operator follows a three-phase process:

   1. **Inherit**: Select nodes from parents based on inheritance probabilities
   2. **Repair**: Fix any constraint violations in the inherited solution
   3. **Recombine**: Combine repaired solutions to form the final offspring

   * **Usage**: DCNP problems with exactly 3 parents
   * **Requirement**: Variable population must be disabled (``is_pop_variable=False``)

**RSC (Reduce-Solve-Combine)**

   The primary crossover operator for CNP that uses problem reduction:

   1. **Reduce**: Identify common nodes between parents and reduce the problem
   2. **Solve**: Apply local search to the reduced subproblem
   3. **Combine**: Merge the solution with non-common nodes from parents

   * **Usage**: CNP problems with problem reduction enabled
   * **Parameter**: ``beta`` controls the fraction of common nodes to preserve


Stopping criteria
-----------------

The solver requires a stopping criterion to terminate the search:

**MaxIterations**

   Stops after a fixed number of algorithm iterations.

   :param max_iterations: Maximum number of iterations to run

**MaxRuntime**

   Stops after a specified amount of time (in seconds).

   :param max_runtime: Maximum runtime in seconds

**NoImprovement**

   Stops if no improving solution is found for a specified number of consecutive iterations.

   :param max_no_improvement: Maximum iterations without improvement before stopping


Memetic algorithm
-----------------

PyCNP uses a Memetic Algorithm (MA), which combines global search with local refinement:

1. **Population-based evolution** - Maintains a population of solutions that evolve over generations
2. **Local search** - Applies problem-specific neighborhood search to improve each offspring
3. **Crossover operators** - Combines parent solutions to create diverse offspring

The :class:`~pycnp.MemeticSearch` class handles the population and evolution process.
Key configuration parameters include:

* ``search`` - The local search strategy (CBNS, CHNS, DLAS, or BCLS)
* ``crossover`` - The crossover operator (DBX, IRR, or RSC)
* ``is_problem_reduction`` - Whether to use problem reduction with RSC crossover
* ``is_pop_variable`` - Whether the population size can adapt during search
* ``initial_pop_size`` - The initial population size (default: 5)


Variable population sizing
---------------------------

PyCNP supports adaptive population sizing through the :class:`~pycnp.VariablePopulationParams` class.
When enabled, the population can expand or contract based on search progress:

* ``max_pop_size`` - Maximum population size (default: 20)
* ``increase_pop_size`` - Number of individuals to add when expanding (default: 3)
* ``max_idle_gens`` - Number of idle generations before triggering population update (default: 20)

The population expands when no improvement is observed for ``max_idle_gens`` consecutive iterations,
injecting diversity into the search process.


C++ ProblemData
---------------

The C++ :class:`~pycnp.ProblemData` class is the underlying data structure used by PyCNP
to store graph information. It is created automatically when loading instances via :func:`~pycnp.read.read`.
