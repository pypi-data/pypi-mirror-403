#ifndef DOUBLE_BACKBONE_BASED_CROSSOVER_H
#define DOUBLE_BACKBONE_BASED_CROSSOVER_H

#include "../Graph/Graph.h"
#include "../RandomNumberGenerator.h"
#include <memory>
#include <utility>

/**
 * @brief Double Backbone Based (DBX) crossover operator.
 *
 * Identifies common nodes between parent solutions (the "backbone") and
 * constructs an offspring by preserving these common nodes and probabilistically
 * inheriting others.
 *
 * @param originalGraph The original problem graph.
 * @param parents Pair of parent solutions to cross over.
 * @param seed Random seed for the operation.
 * @return Unique pointer to the new offspring graph.
 */
std::unique_ptr<Graph> doubleBackboneBasedCrossover(
    const Graph &originalGraph,
    const std::pair<const Solution *, const Solution *> &parents,
    int seed);

#endif  // DOUBLE_BACKBONE_BASED_CROSSOVER_H
