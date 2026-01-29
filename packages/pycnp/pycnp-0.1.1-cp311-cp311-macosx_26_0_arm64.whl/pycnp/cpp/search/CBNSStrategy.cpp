#include "CBNSStrategy.h"
#include "SearchResult.h"
#include "SearchUtils.h"

CBNSStrategy::CBNSStrategy(
    Graph &graph, const std::unordered_map<std::string, std::any> &params)
    : graph_(graph), params_(params)
{
    maxIdleSteps_ = SearchUtils::getParamOr<int>(params, "maxIdleSteps", maxIdleSteps_);
    SearchUtils::applySeed(params, rng_);
}

SearchResult CBNSStrategy::execute()
{

    SearchResult result;

    Graph &currentGraph = graph_;
    Solution bestSolution = graph_.getRemovedNodes();

    int currentObjValue = graph_.getObjectiveValue();
    int bestObjValue = currentObjValue;
    long numIdleSteps = 0;
    long numSteps = 0;

    while (numIdleSteps < maxIdleSteps_)
    {
        numSteps++;

        performMove(currentGraph, currentObjValue, numSteps);

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

void CBNSStrategy::performMove(Graph &currentGraph,
                               int &currentObjValue,
                               int numSteps)
{

    ComponentIndex componentToRemove = currentGraph.selectRemovedComponent();
    Node nodeToRemove
        = currentGraph.ageSelectNodeFromComponent(componentToRemove);

    currentGraph.removeNode(nodeToRemove);
    currentGraph.setNodeAge(nodeToRemove, numSteps);

    Node nodeToAdd = currentGraph.greedySelectNodeToAdd();

    if (nodeToAdd != INVALID_NODE)
    {
        currentGraph.addNode(nodeToAdd);
        currentGraph.setNodeAge(nodeToAdd, numSteps);
    }

    currentObjValue = currentGraph.getObjectiveValue();
}