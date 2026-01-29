.. _api_read:

Read
=========

.. autofunction:: pycnp.read

.. autofunction:: pycnp.read_adjacency_list_format

.. autofunction:: pycnp.read_edge_list_format

File Formats
------------

Adjacency List Format
~~~~~~~~~~~~~~~~~~~~~

In adjacency list format, the first line contains the number of nodes.
Each subsequent line represents a node and its neighbors in the format: ``node_id: neighbor1 neighbor2 ...``

**Example file: ``graph.txt``**

.. code-block:: text

   4
   0: 1 2 3
   1: 0 2
   2: 0 1 3
   3: 0 2

This represents a graph with 4 nodes where:

- Node 0 is connected to nodes 1, 2, 3
- Node 1 is connected to nodes 0, 2
- Node 2 is connected to nodes 0, 1, 3
- Node 3 is connected to nodes 0, 2

**Usage example:**

.. code-block:: python

   import pycnp

   problem = pycnp.read_adjacency_list_format("graph.txt")

.. note::

   This format is used by instances such as ``ErdosRenyi_n235.txt``.

Edge List Format
~~~~~~~~~~~~~~~~

In edge list format, the first line is a header ``p edge num_nodes num_edges``,
followed by edge definitions ``e node1 node2``.

**Example file: ``graph.txt``**

.. code-block:: text

   p edge 4 5
   e 0 1
   e 0 2
   e 0 3
   e 1 2
   e 2 3

This represents a graph with 4 nodes and 5 edges:

- Edge between node 0 and node 1
- Edge between node 0 and node 2
- Edge between node 0 and node 3
- Edge between node 1 and node 2
- Edge between node 2 and node 3

**Usage example:**

.. code-block:: python

   import pycnp

   problem = pycnp.read_edge_list_format("graph.txt")

.. note::

   This format is used by instances such as ``hi_tech.txt``.
   The :func:`~pycnp.read` function automatically detects the format based on
   the presence of the ``p`` header line, so you typically only need to use it.
