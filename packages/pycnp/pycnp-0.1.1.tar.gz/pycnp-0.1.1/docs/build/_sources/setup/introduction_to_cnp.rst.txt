A brief introduction to the CNDPs
=================================================

The Critical Node Detection Problems (CNDPs) constitute one of the most extensively studied classes of combinatorial optimization problems. 
A central issue in CNDPs is the selection of an appropriate network connectivity metric, for which a wide range of alternatives has been proposed in the literature. 
According to the adopted metrics, CNDPs can be broadly categorized into two groups: fragmentation-based CNDPs and distance-based CNDPs. 
The PyCNP package currently supports two representative variants, namely the Critical Node Problem (CNP) and the Distance-based Critical Node Problem (DCNP), which belong to the fragmentation-based and distance-based categories, respectively.

Problem formulation
-------------------

The Critical Node Problem (CNP) and its variants can be formally described as optimization problems on an undirected graph :math:`G = (V, E)`, where :math:`V` is the set of nodes and :math:`E` is the set of edges. 
The goal is to find a subset of nodes :math:`S \subseteq V` to remove, such that a specific connectivity metric of the residual graph :math:`G[V \setminus S]` is minimized, subject to a budget constraint.

Supported problem variants
--------------------------

Critical Node Problem (CNP)
^^^^^^^^^^^^^^^^^^^^^^^^^^^


The standard CNP seeks to identify a set of critical nodes :math:`S` whose removal minimizes the pairwise connectivity of the residual graph. The pairwise connectivity metric calculates the total number of node pairs that remain connected by a path.

Formally, the CNP is defined as:

.. math::

   \min_{S \subseteq V} \;
        \sum_{\substack{i,j \in V \setminus S \\ i < j}} w_{ij} \cdot x_{ij}

   \text{s.t.} \qquad
        \sum_{i \in S} c_i \;\leq\; k

**Where:**

* :math:`k`: Budget constraint (maximum cost of removed nodes).
* :math:`w_{ij}`: Weight associated with the connection between nodes :math:`i` and :math:`j`.
* :math:`x_{ij}`: Binary variable, equal to 1 if a path exists between :math:`i` and :math:`j` in :math:`G[V \setminus S]`, and 0 otherwise.
* :math:`c_i`: Cost of removing node :math:`i`.

PyCNP focuses on the **unweighted case** where :math:`c_i = 1` and :math:`w_{ij} = 1`. In this context, the objective simplifies to minimizing the total number of connected node pairs in the residual graph.

Distance-based Critical Node Problem (DCNP)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Distance-based CNP (DCNP) considers the actual pairwise distances between nodes rather than just their connectivity. The objective is to minimize a distance-based connectivity metric.

Formally, the DCNP is defined as:

.. math::

   \min_{S \subseteq V} \;
        \sum_{\substack{i,j \in V \setminus S \\ i < j}} w_{ij} \cdot \phi(d_{ij})

   \text{s.t.} \qquad
        \sum_{i \in S} c_i \;\leq\; k

**Where:**

* :math:`d_{ij}`: Shortest path distance between :math:`i` and :math:`j` in the residual graph :math:`G[V \setminus S]`.
* :math:`\phi(d_{ij})`: Distance-based connectivity measure, defined as:

.. math::

   \phi(d_{ij}) = \begin{cases} 1, & \text{if } d_{ij} < b, \\ 0, & \text{otherwise}. \end{cases}

* :math:`b`: Predefined **hop distance limit**. Two nodes are considered "connected" only if their distance is strictly less than :math:`b`.

Notably, when :math:`b \geq |V|`, the DCNP reduces to the standard CNP.

.. hint::

   Check out the :doc:`quick tutorial </examples/example1>` for step-by-step examples of solving CNP and DCNP instances.
