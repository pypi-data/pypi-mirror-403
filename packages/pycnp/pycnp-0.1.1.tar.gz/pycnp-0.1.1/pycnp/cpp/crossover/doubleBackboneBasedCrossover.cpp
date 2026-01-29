#include "doubleBackboneBasedCrossover.h"

#include <algorithm>
#include <memory>
#include <unordered_set>

namespace
{
    constexpr double THETA = 0.85;
}

std::unique_ptr<Graph> doubleBackboneBasedCrossover(
    const Graph &originalGraph,
    const std::pair<const Solution *, const Solution *> &parents,
    int seed)
{
    RandomNumberGenerator rng;
    rng.setSeed(seed);

    const auto &MSolution = *parents.first;
    const auto &FSolution = *parents.second;

    Solution nodesToRemove;
    nodesToRemove.reserve(MSolution.size());

    for (Node node : MSolution)
    {
        if (FSolution.contains(node))
        {
            nodesToRemove.insert(node);
        }
        else if (rng.generateProbability() < THETA)
        {
            nodesToRemove.insert(node);
        }
    }
    for (Node node : FSolution)
    {
        if (nodesToRemove.contains(node))
            continue;

        if (rng.generateProbability() < THETA)
        {
            nodesToRemove.insert(node);
        }
    }

    auto offspring = originalGraph.clone();
    offspring->updateGraphByRemovedNodes(nodesToRemove);

    int currentCount = static_cast<int>(nodesToRemove.size());
    int targetCount = static_cast<int>(MSolution.size());

    if (currentCount < targetCount)
    {
        for (int i = 0; i < targetCount - currentCount; ++i)
        {
            ComponentIndex componentIndex = offspring->selectRemovedComponent();
            Node nodeToRemove = offspring->randomSelectNodeFromComponent(componentIndex);
            offspring->removeNode(nodeToRemove);
        }
    }
    else if (currentCount > targetCount)
    {
        for (int i = 0; i < currentCount - targetCount; ++i)
        {
            Node nodeToAdd = offspring->greedySelectNodeToAdd();
            offspring->addNode(nodeToAdd);
        }
    }

    return offspring;
}
