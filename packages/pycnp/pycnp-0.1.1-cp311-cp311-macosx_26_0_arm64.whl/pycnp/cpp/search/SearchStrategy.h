#ifndef SEARCH_STRATEGY_H
#define SEARCH_STRATEGY_H

#include "../SearchResult.h"

/**
 * SearchStrategy
 *
 * Search strategy interface.
 *
 * All concrete search algorithms need to implement this interface.
 */
class SearchStrategy
{
public:

    virtual ~SearchStrategy() = default;

    /**
     * Runs the search algorithm implemented by the strategy.
     *
     * Returns
     * -------
     * SearchResult
     *     The result of the search.
     */
    virtual SearchResult execute() = 0;
};

#endif  // SEARCH_STRATEGY_H
