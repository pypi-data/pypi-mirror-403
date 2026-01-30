#ifndef CBNS_STRATEGY_H
#define CBNS_STRATEGY_H

#include "Graph/Graph.h"
#include "RandomNumberGenerator.h"
#include "SearchStrategy.h"
#include <any>
#include <unordered_map>

/**
 * CBNSStrategy
 *
 * Component-based Neighborhood Search strategy.
 *
 * CBNS (Component-Based Neighborhood Search) strategy searches for optimal
 * solutions by operating on connected components of the graph.
 */
class CBNSStrategy : public SearchStrategy
{
public:
    /**
     * Constructor.
     *
     * Parameters
     * ----------
     * graph
     *     Reference to the graph object.
     * params
     *     Algorithm parameters.
     */
    CBNSStrategy(Graph &graph,
                 const std::unordered_map<std::string, std::any> &params);

    /**
     * Virtual destructor.
     */
    virtual ~CBNSStrategy() = default;

    /**
     * Execute CBNS search algorithm.
     *
     * Returns
     * -------
     * SearchResult
     *     Search result.
     */
    SearchResult execute() override;

private:
    Graph &graph_;                                      ///< Reference to graph object
    std::unordered_map<std::string, std::any> params_;  ///< Algorithm parameters
    int maxIdleSteps_ = 1000;                           ///< Maximum idle steps, default 1000
    RandomNumberGenerator rng_;                         ///< Random number generator

    /**
     * Perform one move operation.
     *
     * Parameters
     * ----------
     * currentGraph
     *     Current graph object.
     * currentObjValue
     *     Current objective function value, will be updated.
     * numSteps
     *     Current step count.
     */
    void performMove(Graph &currentGraph, int &currentObjValue, long numSteps);
};

#endif  // CBNS_STRATEGY_H
