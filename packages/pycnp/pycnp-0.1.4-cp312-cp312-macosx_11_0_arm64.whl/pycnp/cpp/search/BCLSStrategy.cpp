#include "BCLSStrategy.h"
#include "SearchResult.h"
#include "SearchUtils.h"
#include <algorithm>
#include <iostream>
#include <iterator>
#include <list>
#include <stdexcept>
#include <vector>

BCLSStrategy::BCLSStrategy(
    Graph &graph, const std::unordered_map<std::string, std::any> &params)
    : graph_(graph), params_(params)
{
    maxIdleSteps_ = SearchUtils::getParamOr<int>(params, "maxIdleSteps", maxIdleSteps_);
    selectionProb_
        = SearchUtils::getParamOr<double>(params, "selectionProb", selectionProb_);
    SearchUtils::applySeed(params, rng_);
}

SearchResult BCLSStrategy::execute()
{

    SearchResult result;

    Graph &currentGraph = graph_;
    Solution bestSolution = graph_.getRemovedNodes();

    DCNP_Graph *dcnpGraph = currentGraph.asDCNP();
    if (!dcnpGraph)
    {
        throw std::runtime_error("BCLSStrategy requires a DCNP graph");
    }

    bestSolution = dcnpGraph->getRemovedNodes();

    int currentObjValue = graph_.getObjectiveValue();
    int bestObjValue = currentObjValue;
    long numIdleSteps = 0;

    std::vector<Node> sortedNodes;
    sortedNodes.reserve(currentGraph.getNumNodes());
    for (Node i = 0; i < currentGraph.getNumNodes(); ++i)
    {
        sortedNodes.push_back(i);
    }

    const std::vector<double> &centrality
        = currentGraph.calculateBetweennessCentrality();
    std::sort(sortedNodes.begin(),
            sortedNodes.end(),
            [&centrality](int a, int b)
            { return centrality[a] > centrality[b]; });

    std::list<Node> candidateNodes(sortedNodes.begin(), sortedNodes.end());

    auto it_5 = candidateNodes.begin();
    updateIteratorTo5th(candidateNodes, it_5);

    while (numIdleSteps < maxIdleSteps_)
    {
        performMove(currentGraph, currentObjValue, candidateNodes, it_5);

        if (currentObjValue < bestObjValue)
        {
            // getRemovedNodes now returns a const reference; this creates a copy of the current best solution
            bestSolution = currentGraph.getRemovedNodes();
            bestObjValue = currentObjValue;
            numIdleSteps = 0;
        }
        else
        {
            numIdleSteps++;
        }
    }

    result.solution = bestSolution;
    result.objValue = bestObjValue;

    return result;
}

void BCLSStrategy::performMove(Graph &currentGraph,
                            int &currentObjValue,
                            std::list<Node> &candidateNodes,
                            std::list<Node>::iterator &it_5)
{

    if (candidateNodes.empty())
    {
        std::cout << "candidate nodes list is empty, can not perform move" << std::endl;
        return;
    }

    while (!candidateNodes.empty())
    {

        double r = rng_.generateProbability();

        Node removedNode = candidateNodes.front();
        candidateNodes.pop_front();

        updateIteratorTo5th(candidateNodes, it_5);

        if (currentGraph.isNodeRemoved(removedNode))
        {
            continue;
        }

        if (r < selectionProb_)
        {
            currentGraph.removeNode(removedNode);
            Node BestNodeToAdd = currentGraph.findBestNodeToAdd();

            if (BestNodeToAdd != INVALID_NODE)
            {
                currentGraph.addNode(BestNodeToAdd);
                candidateNodes.push_back(BestNodeToAdd);
                updateIteratorTo5th(candidateNodes, it_5);
            }
            else
            {
                candidateNodes.push_front(removedNode);
                updateIteratorTo5th(candidateNodes, it_5);
                continue;
            }
            currentObjValue = currentGraph.getObjectiveValue();
            return;
        }
        else
        {

            if (candidateNodes.size() >= 5 && it_5 != candidateNodes.end())
            {
                candidateNodes.insert(std::next(it_5), removedNode);
            }
            else
            {
                candidateNodes.push_back(removedNode);
            }
            updateIteratorTo5th(candidateNodes, it_5);
        }
    }
}

void BCLSStrategy::updateIteratorTo5th(std::list<Node> &candidateNodes,
                                    std::list<Node>::iterator &it_5)
{
    if (candidateNodes.size() >= 5)
    {
        it_5 = candidateNodes.begin();
        std::advance(it_5, 4);
    }
    else if (!candidateNodes.empty())
    {
        it_5 = std::prev(candidateNodes.end());
    }
    else
    {
        it_5 = candidateNodes.end();
    }
}