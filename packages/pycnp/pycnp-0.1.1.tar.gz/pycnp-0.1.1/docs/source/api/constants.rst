.. _api_constants:

Constants
=========

This page lists the constants used throughout PyCNP for configuring problems, search strategies, and operators.

Problem Types
-------------

Constants used to specify the type of problem to solve.

.. py:data:: CNP
   :value: "CNP"
   :no-index:

   Critical Node Problem (Minimize pairwise connectivity).

.. py:data:: DCNP
   :value: "DCNP"
   :no-index:

   Distance-based Critical Node Problem (Minimize pairwise connectivity with distance constraint).

Search Strategies
-----------------

Constants used to specify the local search strategy.

.. py:data:: CBNS
   :value: "CBNS"
   :no-index:

   Component-Based Neighborhood Search.

.. py:data:: CHNS
   :value: "CHNS"
   :no-index:

   Component-Based Hybrid Neighborhood Search.

.. py:data:: DLAS
   :value: "DLAS"
   :no-index:

   Diversified Late Acceptance Search.

.. py:data:: BCLS
   :value: "BCLS"
   :no-index:

   Betweenness Centrality Late Acceptance Search.

Crossover Operators
-------------------

Constants used to specify the crossover operator in Memetic Search.

.. py:data:: DBX
   :value: "DBX"
   :no-index:

   Double Backbone Based Crossover.

.. py:data:: IRR
   :value: "IRR"
   :no-index:

   Inherit-Repair-Recombination Crossover.

.. py:data:: RSC
   :value: "RSC"
   :no-index:

   Reduce-Solve-Combine Crossover.

Configuration & Logging
-----------------------

General configuration constants.

.. py:data:: DEFAULT_HOP_DISTANCE
   :value: 1073741824
   :no-index:

   Default hop distance for CNP (effectively infinite).

.. py:data:: DEFAULT_DISPLAY_INTERVAL
   :value: 1.0
   :no-index:

   Default time interval (in seconds) for updating progress display.
