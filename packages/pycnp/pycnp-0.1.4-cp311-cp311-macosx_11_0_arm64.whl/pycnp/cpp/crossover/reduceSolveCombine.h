#ifndef REDUCE_SOLVE_COMBINE_H
#define REDUCE_SOLVE_COMBINE_H

#include "../Graph/Graph.h"
#include "../RandomNumberGenerator.h"
#include <memory>
#include <string>
#include <utility>

/**
 * @brief Reduce-Solve-Combine (RSC) crossover operator.
 *
 * Reduces common nodes between parents, solves the reduced subproblem
 * via local search, and combines the results to form an offspring.
 *
 * @param originalGraph The original problem graph.
 * @param parents Pair of parent solutions.
 * @param search_strategy The local search strategy to use on the subproblem.
 * @param beta Parameter controlling the reduction intensity.
 * @param seed Random seed for the operation.
 * @return Unique pointer to the new offspring graph.
 */
std::unique_ptr<Graph> reduceSolveCombine(
    const Graph &originalGraph,
    const std::pair<const Solution *, const Solution *> &parents,
    const std::string &search_strategy,
    double beta,
    int seed);

#endif  // REDUCE_SOLVE_COMBINE_H
