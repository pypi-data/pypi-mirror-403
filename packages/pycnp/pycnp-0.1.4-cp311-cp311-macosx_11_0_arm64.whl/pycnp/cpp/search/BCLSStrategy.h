#ifndef BCLS_STRATEGY_H
#define BCLS_STRATEGY_H

#include "Graph/Graph.h"
#include "RandomNumberGenerator.h"
#include "SearchStrategy.h"
#include <any>
#include <list>
#include <unordered_map>

/**
 * BCLSStrategy
 *
 * Betweenness centrality-based late-acceptance search strategy.
 *
 * BCLS (Betweenness centrality-based late-acceptance search) strategy
 * uses node betweenness centrality to guide the search.
 */
class BCLSStrategy : public SearchStrategy
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
    BCLSStrategy(Graph &graph,
                 const std::unordered_map<std::string, std::any> &params);

    /**
     * Virtual destructor.
     */
    virtual ~BCLSStrategy() = default;

    /**
     * Execute BCLS search algorithm.
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
    int maxIdleSteps_ = 150;                            ///< Maximum idle steps, default 150
    double selectionProb_ = 0.8;                        ///< Selection probability, default 0.8
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
     * candidateNodes
     *     List of candidate nodes.
     * it_5
     *     Iterator pointing to the 5th element in the candidate nodes list.
     */
    void performMove(Graph &currentGraph,
                     int &currentObjValue,
                     std::list<Node> &candidateNodes,
                     std::list<Node>::iterator &it_5);

    /**
     * Update iterator pointing to the 5th (or last) candidate node.
     */
    void updateIteratorTo5th(std::list<Node> &candidateNodes,
                             std::list<Node>::iterator &it_5);
};

#endif  // BCLS_STRATEGY_H
