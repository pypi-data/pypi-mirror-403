#include "reduceSolveCombine.h"
#include "../search/Search.h"
#include <algorithm>
#include <stdexcept>

std::unique_ptr<Graph> reduceSolveCombine(
    const Graph &originalGraph,
    const std::pair<const Solution *, const Solution *> &parents,
    const std::string &search_strategy,
    double beta,
    int seed)
{
    if (beta < 0.0 || beta > 1.0)
    {
        throw std::invalid_argument("beta for RSC crossover must be in [0, 1]");
    }

    RandomNumberGenerator rng;
    rng.setSeed(seed);

    const auto &MSolution = *parents.first;
    const auto &FSolution = *parents.second;

    Solution nodesToRemove;
    nodesToRemove.reserve(std::min(MSolution.size(), FSolution.size()));

    for (Node node : MSolution)
    {
        if (FSolution.contains(node) && rng.generateProbability() < beta)
        {
            nodesToRemove.insert(node);
        }
    }

    auto workingGraph = originalGraph.clone();
    workingGraph->getReducedGraphByRemovedNodes(nodesToRemove);

    std::unique_ptr<Graph> reducedGraph(workingGraph->getRandomFeasibleGraph());

    Search local_search(*reducedGraph, seed);
    const bool is_dcnp = originalGraph.isDCNP();
    
    // Set search strategy (validation is done on Python side)
    local_search.setStrategy(search_strategy.empty() 
        ? (is_dcnp ? "BCLS" : "CHNS") 
        : search_strategy);
    SearchResult result = local_search.run();

    Solution finalNodes = nodesToRemove;
    finalNodes.insert(result.solution.begin(), result.solution.end());

    auto improvedGraph = originalGraph.clone();
    improvedGraph->updateGraphByRemovedNodes(finalNodes);

    return improvedGraph;
}
