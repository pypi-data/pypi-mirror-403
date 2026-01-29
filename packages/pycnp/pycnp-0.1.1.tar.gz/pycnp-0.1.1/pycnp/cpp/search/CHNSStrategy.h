#ifndef CHNS_STRATEGY_H
#define CHNS_STRATEGY_H

#include "Graph/Graph.h"
#include "RandomNumberGenerator.h"
#include "SearchStrategy.h"
#include <any>
#include <unordered_map>

/**
 * CHNSStrategy
 *
 * Component-based Hybrid Neighborhood Search strategy.
 *
 * CHNS (Component-Based Hybrid Neighborhood Search) strategy combines
 * two heuristic methods for search.
 */
class CHNSStrategy : public SearchStrategy
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
    CHNSStrategy(Graph &graph,
                 const std::unordered_map<std::string, std::any> &params);

    /**
     * Virtual destructor.
     */
    virtual ~CHNSStrategy() = default;

    /**
     * Execute CHNS search algorithm.
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
    double theta_ = 0.3;                                ///< Probability of using influence selection, default 0.3
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
    void performMove(Graph &currentGraph, int &currentObjValue, int numSteps);
};

#endif  // CHNS_STRATEGY_H
