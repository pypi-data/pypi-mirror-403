A brief introduction to MA
==========================

PyCNP employs a **Memetic Algorithm (MA)** framework to solve both CNP and DCNP. Originally proposed by Moscato (1989), MAs integrate **Local Search (LS)** techniques into a population-based **Genetic Algorithm (GA)**. This hybrid approach combines the exploration capabilities of evolutionary algorithms with the exploitation strengths of local optimization.

The canonical memetic algorithm implemented in PyCNP follows this general procedure:

1.  **Initialization**: A population :math:`P` of solutions is generated.
2.  **Evolutionary Loop**:
    
    *   **Crossover**: Two parent solutions are selected to produce an offspring solution :math:`S'`.
    *   **Local Search**: The offspring :math:`S'` is improved using a problem-specific local search heuristic.
    *   **Population Update**: The improved solution is incorporated back into the population, potentially replacing a less fit individual.

3.  **Termination**: The process repeats until a stopping criterion (e.g., time limit, maximum generations) is met.

**Pseudocode:**

.. code-block:: text
   :caption: Canonical Memetic Algorithm

   Input: Problem instance I, population size θ
   Output: The best found solution S*

   1:  P ← PopInitialize(θ)                 // Build an initial population
   2:  S* ← argmin_{S_i ∈ P} f(S_i)         // Record the best solution found so far
   3:  while stopping criteria is not met do
   4:      Randomly select two individuals S^a, S^b ∈ P
   5:      S' ← Crossover(S^a, S^b)         // Perform solution recombination
   6:      S' ← LocalSearch(S')             // Perform local optimization
   7:      if f(S') < f(S*) then
   8:          S* ← S'                      // Update the best solution
   9:      end if
   10:     P ← PopUpdate(P, S')             // Update the population
   11: end while
   12: return S*

PyCNP implements four state-of-the-art memetic algorithms based on this framework:

*   **Standard Memetic Search (MS)**: Uses component-based neighborhood search (CBNS) and double backbone-based crossover (DBX).
*   **Variable Population Memetic Search (VPMS)**: Dynamically adjusts population size to balance exploration and exploitation.
*   **Instance Reduction Memetic Search (IRMS)**: Uses a problem reduction strategy to simplify large instances before solving.
*   **Fast Tri-individual Memetic Search (FTMS)**: A specialized algorithm for DCNP that maintains a small elite population.
