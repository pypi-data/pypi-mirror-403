#ifndef DLAS_STRATEGY_H
#define DLAS_STRATEGY_H
#include "Graph/Graph.h"
#include "RandomNumberGenerator.h"
#include "SearchStrategy.h"
#include <any>
#include <unordered_map>
#include <vector>

/**
 * DLASStrategy
 *
 * Diversified Late Acceptance Search strategy.
 *
 * DLAS (Diversified Late Acceptance Search) strategy uses historical cost
 * acceptance criteria to search for optimal solutions.
 */
class DLASStrategy : public SearchStrategy
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
    DLASStrategy(Graph &graph,
                 const std::unordered_map<std::string, std::any> &params);

    /**
     * Virtual destructor.
     */
    virtual ~DLASStrategy() = default;

    /**
     * Execute DLAS search algorithm.
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
    int historyLength_ = 5;                             ///< Default history length is 5
    int maxIdleSteps_ = 1000;                           ///< Default maximum idle steps is 1000
    RandomNumberGenerator rng_;                         ///< Random number generator

    /**
     * Perform a move operation.
     *
     * Parameters
     * ----------
     * currentGraph
     *     Current graph object.
     * currentObjValue
     *     Current objective function value, will be updated.
     * historyCost
     *     Historical cost array.
     * maxCost
     *     Maximum historical cost.
     * numMaxCost
     *     Number of occurrences of maximum cost.
     * numSteps
     *     Current step number.
     */
    void performMove(Graph &currentGraph,
                     int &currentObjValue,
                     std::vector<int> &historyCost,
                     int &maxCost,
                     int &numMaxCost,
                     int numSteps);
};

#endif  // DLAS_STRATEGY_H
