#include "DLASStrategy.h"
#include "SearchResult.h"
#include "SearchUtils.h"
#include <algorithm>
#include <vector>

DLASStrategy::DLASStrategy(
    Graph &graph, const std::unordered_map<std::string, std::any> &params)
    : graph_(graph), params_(params)
{
    maxIdleSteps_ = SearchUtils::getParamOr<int>(params, "maxIdleSteps", maxIdleSteps_);
    historyLength_
        = SearchUtils::getParamOr<int>(params, "historyLength", historyLength_);
    SearchUtils::applySeed(params, rng_);
}

SearchResult DLASStrategy::execute()
{

    SearchResult result;

    Graph &currentGraph = graph_;
    Solution bestSolution = currentGraph.getRemovedNodes();

    int currentObjValue = graph_.getObjectiveValue();
    int bestObjValue = currentObjValue;
    long numSteps = 0;
    long numIdleSteps = 0;

    std::vector<int> historyCost(historyLength_, currentObjValue);
    int maxCost = currentObjValue;
    int numMaxCost = historyLength_;

    while (numIdleSteps < maxIdleSteps_)
    {
        numSteps++;

        performMove(currentGraph,
                    currentObjValue,
                    historyCost,
                    maxCost,
                    numMaxCost,
                    numSteps);

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

void DLASStrategy::performMove(Graph &currentGraph,
                               int &currentObjValue,
                               std::vector<int> &historyCost,
                               int &maxCost,
                               int &numMaxCost,
                               long numSteps)
{

    // Save a copy of the current removed nodes to allow rollback if needed
    Solution previousRemovedNodes = currentGraph.getRemovedNodes();
    int previousObjValue = currentObjValue;

    ComponentIndex componentToRemove = currentGraph.selectRemovedComponent();

    Node nodeToRemove
        = currentGraph.randomSelectNodeFromComponent(componentToRemove);

    currentGraph.removeNode(nodeToRemove);
    Node nodeToAdd = currentGraph.greedySelectNodeToAdd();

    if (nodeToAdd != INVALID_NODE)
    {
        currentGraph.addNode(nodeToAdd);
        currentGraph.setNodeAge(nodeToAdd, numSteps);
    }

    currentObjValue = currentGraph.getObjectiveValue();

    int historyLength = historyCost.size();
    int historyIndex = numSteps % historyLength;

    if (currentObjValue == previousObjValue || currentObjValue < maxCost)
    {
    }
    else
    {

        currentGraph.updateGraphByRemovedNodes(previousRemovedNodes);
        currentObjValue = previousObjValue;
    }

    if (currentObjValue > historyCost[historyIndex])
    {

        historyCost[historyIndex] = currentObjValue;
    }
    else if (currentObjValue < historyCost[historyIndex]
             && currentObjValue < previousObjValue)
    {

        historyCost[historyIndex] = currentObjValue;

        if (historyCost[historyIndex] == maxCost)
        {
            numMaxCost--;
        }

        if (numMaxCost == 0)
        {

            maxCost = *std::max_element(historyCost.begin(), historyCost.end());

            numMaxCost
                = std::count(historyCost.begin(), historyCost.end(), maxCost);
        }
    }
}