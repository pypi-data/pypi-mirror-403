#ifndef INHERIT_REPAIR_RECOMBINATION_H
#define INHERIT_REPAIR_RECOMBINATION_H

#include "../Graph/Graph.h"
#include "../RandomNumberGenerator.h"
#include <memory>
#include <tuple>

/**
 * @brief Inherit-Repair-Recombination (IRR) crossover operator.
 *
 * Uses three parents to create offspring through a process of inheritance
 * followed by repair operations to maintain feasibility.
 *
 * @param originalGraph The original problem graph.
 * @param parents Tuple of three parent solutions.
 * @param seed Random seed for the operation.
 * @return Unique pointer to the new offspring graph.
 */
std::unique_ptr<Graph> inherit_repair_recombination(
    const Graph &originalGraph,
    const std::tuple<const Solution *, const Solution *, const Solution *> &parents,
    int seed);

#endif  // INHERIT_REPAIR_RECOMBINATION_H
