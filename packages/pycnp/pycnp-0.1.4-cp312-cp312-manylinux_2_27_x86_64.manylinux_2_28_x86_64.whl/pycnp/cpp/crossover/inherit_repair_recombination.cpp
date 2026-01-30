#include "inherit_repair_recombination.h"

#include <algorithm>
#include <memory>
#include <tuple>
#include <vector>

namespace
{
    constexpr double TARGET_RATIO = 0.9;
    constexpr double P2 = 0.5;
    constexpr double P1 = 0.9;
}

std::unique_ptr<Graph> inherit_repair_recombination(
    const Graph &originalGraph,
    const std::tuple<const Solution *, const Solution *, const Solution *> &parents,
    int seed)
{
    RandomNumberGenerator rng;
    rng.setSeed(seed);

    const auto &parent1Nodes = *std::get<0>(parents);
    const auto &parent2Nodes = *std::get<1>(parents);
    const auto &parent3Nodes = *std::get<2>(parents);

    int numToRemove = static_cast<int>(parent1Nodes.size());

    auto offspring = originalGraph.clone();

    int maxNodeId = 0;
    for (const auto &parentNodes : {parent1Nodes, parent2Nodes, parent3Nodes})
    {
        for (Node node : parentNodes)
        {
            maxNodeId = std::max(maxNodeId, node);
        }
    }

    std::vector<int> nodeFrequency(static_cast<size_t>(maxNodeId) + 1, 0);
    Solution nodesToRemove;
    nodesToRemove.reserve(numToRemove);

    for (const auto &parentNodes : {parent1Nodes, parent2Nodes, parent3Nodes})
    {
        for (Node node : parentNodes)
        {
            nodeFrequency[node]++;

            if (nodeFrequency[node] == 3)
            {
                nodesToRemove.insert(node);
            }
        }
    }

    std::vector<Node> freq2Candidates, freq1Candidates, freq0Candidates;
    for (Node node = 0; node <= maxNodeId; node++)
    {

        if (!nodesToRemove.contains(node))
        {
            if (nodeFrequency[node] == 2)
            {
                freq2Candidates.push_back(node);
            }
            else if (nodeFrequency[node] == 1)
            {
                freq1Candidates.push_back(node);
            }
            else if (nodeFrequency[node] == 0)
            {
                freq0Candidates.push_back(node);
            }
        }
    }

    int targetPhase2 = static_cast<int>(TARGET_RATIO * numToRemove);
    while (static_cast<int>(nodesToRemove.size()) < targetPhase2)
    {
        double r = rng.generateProbability();
        Node nodeToRemove = INVALID_NODE;

        if (r < P2 && !freq2Candidates.empty())
        {

            int idx = rng.generateInt(0, static_cast<int>(freq2Candidates.size() - 1));
            nodeToRemove = freq2Candidates[idx];
            freq2Candidates.erase(freq2Candidates.begin() + idx);
        }
        else if (r < P2 + (1 - P2) * P1 && !freq1Candidates.empty())
        {

            int idx = rng.generateInt(0, static_cast<int>(freq1Candidates.size() - 1));
            nodeToRemove = freq1Candidates[idx];
            freq1Candidates.erase(freq1Candidates.begin() + idx);
        }
        else if (!freq0Candidates.empty())
        {

            int idx = rng.generateInt(0, static_cast<int>(freq0Candidates.size() - 1));
            nodeToRemove = freq0Candidates[idx];
            freq0Candidates.erase(freq0Candidates.begin() + idx);
        }

        if (nodeToRemove != INVALID_NODE)
        {
            nodesToRemove.insert(nodeToRemove);
        }
    }

    offspring->updateGraphByRemovedNodes(nodesToRemove);

    while (static_cast<int>(nodesToRemove.size()) < numToRemove)
    {

        Node nodeToRemove = offspring->findBestNodeToRemove();
        offspring->removeNode(nodeToRemove);
        nodesToRemove.insert(nodeToRemove);
    }

    return offspring;
}
