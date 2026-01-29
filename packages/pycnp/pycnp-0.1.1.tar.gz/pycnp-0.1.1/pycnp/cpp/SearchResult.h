#ifndef SEARCH_RESULT_H
#define SEARCH_RESULT_H

#include "Graph/Graph.h"  
#include <climits>       

/**
 * SearchResult
 *
 * Result container for search algorithms.
 *
 * Stores the outcome of a search algorithm, including the found solution
 * and its objective value. Supports move semantics for efficiency.
 */
class SearchResult
{
public:
    /**
     * Default constructor.
     *
     * Initializes the objective value to INT_MAX, indicating no valid solution.
     */
    SearchResult() : objValue(INT_MAX) {}

    /**
     * Construct with solution and objective value.
     *
     * Parameters
     * ----------
     * sol
     *     Solution as a set of nodes.
     * obj
     *     Objective value of the solution.
     */
    SearchResult(NodeSet sol, int obj) : solution(std::move(sol)), objValue(obj) {}

    // Use default copy and move constructors/assignments
    SearchResult(const SearchResult&) = default;
    SearchResult(SearchResult&&) = default;
    SearchResult& operator=(const SearchResult&) = default;
    SearchResult& operator=(SearchResult&&) = default;

    /// Found solution, represented as a set of nodes
    NodeSet solution;

    /// Objective value of the solution
    int objValue;

    /**
     * Check whether this is a valid solution.
     *
     * Returns
     * -------
     * bool
     *     True if the objective value is not INT_MAX, false otherwise.
     */
    bool isValid() const noexcept { return objValue != INT_MAX; }
};

#endif  // SEARCH_RESULT_H