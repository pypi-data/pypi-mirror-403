PyCNP
=====

PyCNP is an open-source, high-performance Python solver for the Critical Node Problem (CNP) and Distance-based Critical Node Problem (DCNP).

The Critical Node Problem asks: which nodes should be removed from a network to minimize connectivity while respecting a budget constraint? This problem has applications in network security, epidemiology, and social network analysis.

PyCNP currently supports:

* **Critical Node Problem (CNP)** - Minimize pairwise connectivity in undirected graphs
* **Distance-based Critical Node Problem (DCNP)** - CNP variant with hop distance constraints
* **Multiple search strategies** - CBNS, CHNS, DLAS, and BCLS
* **Multiple crossover operators** - DBX, IRR, and RSC

The package provides a flexible Python interface backed by efficient C++ implementations.

Installation
------------

PyCNP can be installed via *pip*:

.. code-block:: shell

   pip install pycnp

Quick start
-----------

.. code-block:: python

   from pycnp import Model
   from pycnp.stop import NoImprovement

   # 1. Create a model
   model = Model()

   # 2. Add 20 nodes (0-19)
   for i in range(20):
       model.add_node(i)

   # 3. Add edges 
   edges = [
       (0, 4), (1, 4), (2, 4), (2, 6), (3, 4),
       (4, 9), (5, 9), (6, 9), (7, 9), (7, 11),
       (8, 9), (9, 14), (10, 14), (11, 14), (12, 14),
       (12, 16), (13, 14), (14, 19), (15, 19),
       (16, 19), (17, 19), (18, 19)
   ]
   for u, v in edges:
       model.add_edge(u, v)

   # 4. Solve the Critical Node Problem (CNP)
   # Remove 3 nodes, stop after 20 generations of no improvement
   result = model.solve(
       problem_type="CNP",
       budget=3,
       stopping_criterion=NoImprovement(20),
       seed=6
   )

   print(f"Removed nodes: {result.best_solution}")

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   setup/introduction_to_cnp
   setup/introduction_to_ma
   setup/concepts
   setup/installation
   setup/getting_help

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/index

.. toctree::
   :maxdepth: 1
   :caption: API reference

   api/index

.. toctree::
   :maxdepth: 1
   :caption: Developing PyCNP

   dev/contributing
