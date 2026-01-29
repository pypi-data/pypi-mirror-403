#ifndef SEARCH_H
#define SEARCH_H

// Include necessary dependencies
#include "Graph/Graph.h"
#include "RandomNumberGenerator.h"
#include "SearchResult.h"
#include "SearchStrategy.h"

// Include all concrete strategy headers (factory needs to know they exist)
#include "BCLSStrategy.h"
#include "CBNSStrategy.h"
#include "CHNSStrategy.h"
#include "DLASStrategy.h"

// Standard library dependencies
#include <any>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>

/**
 * Search
 *
 * Manages and executes various search algorithms.
 *
 * This class uses the strategy pattern to implement management and execution
 * of different search algorithms, supporting multiple search strategies such as
 * CBNS (Component-based Neighborhood Search), DLAS (Dynamic Late Acceptance Search),
 * CHNS (Component-based Hybrid Neighborhood Search), and BCLS (Betweenness
 * centrality-based Late-acceptance Search).
 */
class Search
{
public:
    /**
     * Constructor with seed.
     *
     * Parameters
     * ----------
     * graph
     *     Reference to the graph object for search algorithm computation.
     * seed
     *     Random number seed.
     */
    Search(Graph &graph, int seed);

    /**
     * Destructor.
     */
    ~Search();

    /**
     * Set search strategy.
     *
     * Parameters
     * ----------
     * strategyName
     *     Strategy name, such as "CBNS", "DLAS", "CHNS", or "BCLS".
     *
     * Throws
     * ------
     * std::invalid_argument
     *     If strategy name does not exist.
     */
    void setStrategy(const std::string &strategyName);

    /**
     * Set search algorithm parameter.
     *
     * Parameters
     * ----------
     * name
     *     Parameter name.
     * value
     *     Parameter value.
     *
     * Template Parameters
     * -------------------
     * T
     *     Parameter value type.
     */
    template <typename T> void setParam(const std::string &name, const T &value)
    {
        params_[name] = value;
    }

    /**
     * Run search algorithm.
     *
     * Returns
     * -------
     * SearchResult
     *     Search result containing optimal solution and objective function value.
     *
     * Throws
     * ------
     * std::runtime_error
     *     If search strategy is not set.
     */
    SearchResult run();

private:
    Graph &graph_;                                      ///< Reference to graph object
    std::unique_ptr<SearchStrategy> strategy_;          ///< Current search strategy
    std::unordered_map<std::string, std::any> params_;  ///< Search parameters
    int seed_ = 0;                                      ///< Random number seed (initialized to 0)

    /**
     * Register all available search strategies.
     */
    void registerStrategies();

    /**
     * Strategy factory for creating search strategy instances.
     */
    std::unordered_map<
        std::string,
        std::function<std::unique_ptr<SearchStrategy>(
            Graph &, const std::unordered_map<std::string, std::any> &)>>
        strategyFactory_;
};

#endif  // SEARCH_H
