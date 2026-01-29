#include "CNP_Graph.h"
#include <algorithm>
#include <numeric>  // Include for std::iota

CNP_Graph::CNP_Graph(NodeSet nodes,
                     std::vector<NodeSet> adjList,
                     int budget,
                     int seed)
{
    numNodes_ = nodes.size();
    originalNodesSet_ = nodes;
    initialNodesSet_ = nodes;
    nodeAge_.resize(numNodes_, 0);
    currentAdjList_ = adjList;
    originalAdjList_ = adjList;
    initialAdjList_ = adjList;
    numToRemove_ = budget;
    initialNumToRemove_ = budget;
    nodeToComponentIndex_.resize(numNodes_, -1);
    rng_.setSeed(seed);
    initialSeed_ = seed;
    componentVisited_.resize(numNodes_, 0);
    dfsVisitEpoch_.resize(numNodes_, 0);
    dfsStack_.reserve(numNodes_);
}

void CNP_Graph::initializeComponentsAndMapping()
{
    std::fill(nodeToComponentIndex_.begin(), nodeToComponentIndex_.end(), -1);

    connectedComponents_.clear();
    connectedPairs_ = 0;

    ComponentIndex componentIndex = 0;
    if (componentVisited_.size() < static_cast<size_t>(numNodes_))
    {
        componentVisited_.resize(numNodes_, 0);
    }
    std::fill(componentVisited_.begin(),
              componentVisited_.begin() + numNodes_,
              static_cast<char>(0));

    for (Node node : originalNodesSet_)
    {
        if (!componentVisited_[node] && !isNodeRemoved(node))
        {
            Component component = dfsFindComponent(node);
            if (!component.nodes.empty())
            {
                connectedComponents_.push_back(component);

                for (Node componentNode : component.nodes)
                {
                    componentVisited_[componentNode] = 1;
                    nodeToComponentIndex_[componentNode] = componentIndex;
                }
                componentIndex++;

                connectedPairs_ += (component.size * (component.size - 1)) / 2;
            }
        }
    }
}

Component CNP_Graph::dfsFindComponent(Node startNode) const
{
    Component newComponent;
    newComponent.nodes.reserve(numNodes_);

    if (dfsVisitEpoch_.size() < static_cast<size_t>(numNodes_))
    {
        dfsVisitEpoch_.resize(numNodes_, 0);
        dfsCurrentEpoch_ = 0;
    }

    if (++dfsCurrentEpoch_ == 0)
    {
        dfsCurrentEpoch_ = 1;
        std::fill(dfsVisitEpoch_.begin(), dfsVisitEpoch_.begin() + numNodes_, 0);
    }

    dfsStack_.clear();
    dfsStack_.push_back(startNode);

    while (!dfsStack_.empty())
    {
        Node node = dfsStack_.back();
        dfsStack_.pop_back();

        if (dfsVisitEpoch_[node] == dfsCurrentEpoch_ || isNodeRemoved(node))
        {
            continue;
        }

        dfsVisitEpoch_[node] = dfsCurrentEpoch_;
        newComponent.nodes.push_back(node);

        const auto &neighbors = currentAdjList_[node];
        for (const Node &neighbor : neighbors)
        {
            if (dfsVisitEpoch_[neighbor] != dfsCurrentEpoch_
                && !isNodeRemoved(neighbor))
            {
                dfsStack_.push_back(neighbor);
            }
        }
    }

    newComponent.size = newComponent.nodes.size();
    return newComponent;
}

void CNP_Graph::updateGraphByRemovedNodes(const NodeSet &nodesToRemove)
{
    removedNodes.clear();
    currentAdjList_ = originalAdjList_;

    for (Node node : nodesToRemove)
    {
        removedNodes.insert(node);
    }

    for (Node node : nodesToRemove)
    {
        for (Node neighbor : originalAdjList_[node])
        {
            currentAdjList_[neighbor].erase(node);
        }
        currentAdjList_[node].clear();
    }

    initializeComponentsAndMapping();
}

void CNP_Graph::getReducedGraphByRemovedNodes(const NodeSet &removeSet)
{
    removedNodes.clear();
    numToRemove_ -= removeSet.size();

    for (Node node : removeSet)
    {
        originalNodesSet_.erase(node);

        for (Node neighbor : originalAdjList_[node])
        {
            originalAdjList_[neighbor].erase(node);
        }
        originalAdjList_[node].clear();
    }

    currentAdjList_ = originalAdjList_;
    initializeComponentsAndMapping();
}

void CNP_Graph::addNode(Node nodeToAdd)
{
    removedNodes.erase(nodeToAdd);
    ComponentIndex componentIndex = -1;

    for (Node neighbor : originalAdjList_[nodeToAdd])
    {
        if (nodeToComponentIndex_[neighbor] != -1)
        {
            currentAdjList_[nodeToAdd].insert(neighbor);
            currentAdjList_[neighbor].insert(nodeToAdd);

            if (componentIndex == -1)
            {
                componentIndex = nodeToComponentIndex_[neighbor];
            }
        }
    }

    if (componentIndex != -1)
    {
        connectedComponents_[componentIndex].nodes.push_back(nodeToAdd);
        connectedComponents_[componentIndex].size++;
        nodeToComponentIndex_[nodeToAdd] = componentIndex;

        Component newComponent = dfsFindComponent(nodeToAdd);

        if (newComponent.size > connectedComponents_[componentIndex].size)
        {
            connectedComponents_[componentIndex].size--;

            std::set<ComponentIndex> componentsIndexesToMerge;
            for (Node node : newComponent.nodes)
            {
                if (nodeToComponentIndex_[node] != -1)
                {
                    componentsIndexesToMerge.insert(nodeToComponentIndex_[node]);
                }
            }

            std::vector<int> indexMapping(connectedComponents_.size());
            std::iota(indexMapping.begin(), indexMapping.end(), 0);

            for (ComponentIndex idx : componentsIndexesToMerge)
            {
                for (size_t i = idx + 1; i < indexMapping.size(); ++i)
                {
                    indexMapping[i]--;
                }
            }

            for (Node node : originalNodesSet_)
            {
                if (nodeToComponentIndex_[node] != -1)
                {
                    nodeToComponentIndex_[node]
                        = indexMapping[nodeToComponentIndex_[node]];
                }
            }

            for (auto it = componentsIndexesToMerge.rbegin();
                it != componentsIndexesToMerge.rend();
                ++it)
            {
                connectedPairs_ -= (connectedComponents_[*it].size
                                   * (connectedComponents_[*it].size - 1))
                                / 2;
                connectedComponents_.erase(connectedComponents_.begin() + *it);
            }

            connectedComponents_.push_back(newComponent);

            connectedPairs_ += (newComponent.size * (newComponent.size - 1)) / 2;

            for (Node node : newComponent.nodes)
            {
                nodeToComponentIndex_[node] = connectedComponents_.size() - 1;
            }
        }
        else if (newComponent.size == connectedComponents_[componentIndex].size)
        {
            connectedPairs_ += (connectedComponents_[componentIndex].size - 1);
        }
    }
    else
    {
        Component newComponent;
        newComponent.nodes.push_back(nodeToAdd);
        newComponent.size = 1;

        connectedComponents_.push_back(newComponent);

        nodeToComponentIndex_[nodeToAdd] = connectedComponents_.size() - 1;
    }
}

void CNP_Graph::removeNode(Node nodeToRemove)
{
    ComponentIndex componentIndex = nodeToComponentIndex_[nodeToRemove];
    Component originalComponent = connectedComponents_[componentIndex];

    removedNodes.insert(nodeToRemove);

    nodeToComponentIndex_[nodeToRemove] = -1;

    const auto &neighbors = currentAdjList_[nodeToRemove];
    for (Node neighbor : neighbors)
    {
        currentAdjList_[neighbor].erase(nodeToRemove);
    }
    currentAdjList_[nodeToRemove].clear();

    if (originalComponent.size == 1)
    {
        for (size_t i = componentIndex + 1; i < connectedComponents_.size(); i++)
        {
            for (Node node : connectedComponents_[i].nodes)
            {
                nodeToComponentIndex_[node]--;
            }
        }
        connectedComponents_.erase(connectedComponents_.begin() + componentIndex);
        return;
    }

    if (originalComponent.size > 1)
    {
        std::erase(connectedComponents_[componentIndex].nodes, nodeToRemove);
        connectedComponents_[componentIndex].size--;

        std::vector<bool> isVisited(numNodes_, false);

        Node startNode = -1;
        for (Node node : originalComponent.nodes)
        {
            if (node != nodeToRemove)
            {
                startNode = node;
                break;
            }
        }

        Component newComponent = dfsFindComponent(startNode);

        if (newComponent.size < connectedComponents_[componentIndex].size)
        {
            connectedPairs_ -= (connectedComponents_[componentIndex].size
                               * (connectedComponents_[componentIndex].size + 1))
                              / 2;

            connectedComponents_[componentIndex] = newComponent;

            connectedPairs_ += (newComponent.size * (newComponent.size - 1)) / 2;

            for (Node node : newComponent.nodes)
            {
                isVisited[node] = true;
                nodeToComponentIndex_[node] = componentIndex;
            }

            for (Node node : originalComponent.nodes)
            {
                if (isVisited[node] || node == nodeToRemove)
                    continue;

                Component splitComponent = dfsFindComponent(node);
                ComponentIndex newIndex = connectedComponents_.size();

                connectedComponents_.push_back(splitComponent);

                connectedPairs_
                    += (splitComponent.size * (splitComponent.size - 1)) / 2;

                for (Node componentNode : splitComponent.nodes)
                {
                    nodeToComponentIndex_[componentNode] = newIndex;
                    isVisited[componentNode] = true;
                }
            }
        }
        else
        {
            connectedPairs_ -= newComponent.size;
        }
    }
}

ComponentIndex CNP_Graph::selectRemovedComponent() const
{
    size_t numComponents = connectedComponents_.size();
    std::vector<ComponentIndex> largeComponents;
    largeComponents.reserve(numComponents);
    if (FILE* dbg = std::fopen("/tmp/pycnp_debug.log", "a"))
    {
        std::fprintf(dbg, "[DEBUG] selectRemovedComponent numComponents=%zu removed=%zu\n",
                     numComponents, removedNodes.size());
        std::fclose(dbg);
    }

    if (numComponents > 50)
    {
        return selectRemovedLargerComponent();
    }

    int minSize = numNodes_;
    int maxSize = 0;

    for (size_t i = 0; i < numComponents; ++i)
    {
        const size_t size = connectedComponents_[i].size;
        if (size > 2)
        {
            minSize = std::min(minSize, static_cast<int>(size));
            maxSize = std::max(maxSize, static_cast<int>(size));
        }
    }

    const double sizeThreshold
        = maxSize - (maxSize - minSize) * 0.5 - rng_.generateIndex(3);

    for (size_t i = 0; i < numComponents; ++i)
    {
        if (connectedComponents_[i].size >= sizeThreshold)
        {
            largeComponents.push_back(i);
        }
    }

    if (largeComponents.empty())
    {
        // Fallback: choose the largest existing component to avoid hard failure.
        ComponentIndex fallbackIndex = 0;
        size_t fallbackSize = 0;
        for (size_t i = 0; i < numComponents; ++i)
        {
            const size_t size = connectedComponents_[i].size;
            if (size > fallbackSize)
            {
                fallbackSize = size;
                fallbackIndex = static_cast<ComponentIndex>(i);
            }
        }
        if (fallbackSize == 0)
        {
        if (FILE* dbg = std::fopen("/tmp/pycnp_debug.log", "a"))
        {
            std::fprintf(dbg, "[DEBUG] selectRemovedComponent fallback no components available\n");
            std::fclose(dbg);
        }
        throw std::runtime_error("no components available for selection");
    }
        return fallbackIndex;
    }

    return largeComponents[rng_.generateIndex(largeComponents.size())];
}

ComponentIndex CNP_Graph::selectRemovedLargerComponent() const
{
    size_t totalSize = numNodes_ - removedNodes.size();
    size_t numComponents = connectedComponents_.size();
    size_t avgComponentSize = std::max(
        static_cast<size_t>(2),
        static_cast<size_t>(std::round(static_cast<float>(totalSize)
                                    / static_cast<float>(numComponents))));

    std::vector<ComponentIndex> largeComponents;
    std::vector<size_t> componentSizes;
    largeComponents.reserve(numComponents);
    componentSizes.reserve(numComponents);

    size_t totalNodesInBigComponents = 0;
    size_t maxSize = 0;
    size_t maxIndex = 0;
    size_t secondMaxSize = 0;
    size_t secondMaxIndex = 0;

    for (size_t i = 0; i < numComponents; ++i)
    {
        const size_t currentSize = connectedComponents_[i].size;

        if (currentSize > avgComponentSize)
        {
            largeComponents.push_back(i);
            componentSizes.push_back(currentSize);
            totalNodesInBigComponents += currentSize;

            if (currentSize > maxSize)
            {
                secondMaxSize = maxSize;
                secondMaxIndex = maxIndex;
                maxSize = currentSize;
                maxIndex = i;
            }
            else if (currentSize > secondMaxSize)
            {
                secondMaxSize = currentSize;
                secondMaxIndex = i;
            }
        }
    }

    if (largeComponents.empty())
    {
        // Fallback to component with maximum size when heuristic set is empty.
        size_t fallbackIdx = 0;
        size_t fallbackSize = 0;
        for (size_t i = 0; i < connectedComponents_.size(); ++i)
        {
            const size_t currentSize = connectedComponents_[i].size;
            if (currentSize > fallbackSize)
            {
                fallbackSize = currentSize;
                fallbackIdx = i;
            }
        }
        if (fallbackSize == 0)
        {
            throw std::runtime_error("no components available for selection");
        }
        return static_cast<ComponentIndex>(fallbackIdx);
    }

    if (largeComponents.size() == 1)
    {
        return rng_.generateBool(0.5) ? secondMaxIndex : largeComponents[0];
    }

    const int index = rng_.generateIndex(totalNodesInBigComponents);
    int sum = 0;

    for (size_t i = 0; i < largeComponents.size(); ++i)
    {
        sum += componentSizes[i];
        if (index < sum)
        {
            return largeComponents[i];
        }
    }

    return largeComponents.back();
}

Node CNP_Graph::randomSelectNodeFromComponent(
    ComponentIndex componentIndex) const
{
    const auto &component = connectedComponents_[componentIndex];
    if (component.nodes.empty())
    {
        throw std::runtime_error("component is empty, can not select node");
    }
    return component.nodes[rng_.generateIndex(component.size)];
}

Node CNP_Graph::ageSelectNodeFromComponent(ComponentIndex componentIndex) const
{
    const auto &component = connectedComponents_[componentIndex];
    if (component.size == 0)
    {
        throw std::runtime_error("component is empty, can not select node");
    }

    std::vector<Node> candidateNodes;
    candidateNodes.reserve(component.size);

    const Node firstNode = component.nodes[0];
    int minAge = nodeAge_[firstNode];
    candidateNodes.push_back(firstNode);

    for (size_t i = 1; i < component.size; ++i)
    {
        Node currentNode = component.nodes[i];
        if (nodeAge_[currentNode] < minAge)
        {
            minAge = nodeAge_[currentNode];
            candidateNodes.clear();
            candidateNodes.push_back(currentNode);
        }
        else if (nodeAge_[currentNode] == minAge)
        {
            candidateNodes.push_back(currentNode);
        }
    }

    return candidateNodes.size() == 1
               ? candidateNodes[0]
               : candidateNodes[rng_.generateIndex(candidateNodes.size())];
}

Node CNP_Graph::impactSelectNodeFromComponent(
    ComponentIndex componentIndex) const
{
    const auto &component = connectedComponents_[componentIndex];
    if (component.size == 0)
    {
        throw std::runtime_error("component is empty, can not select node");
    }

    std::vector<int> nodeToIdx(numNodes_, -1);
    for (size_t i = 0; i < component.size; ++i)
    {
        nodeToIdx[component.nodes[i]] = i;
    }

    const int size = component.size;
    dfn_.assign(size + 1, 0);
    lowVec_.assign(size + 1, 0);
    stSizeVec_.assign(size + 1, 1);
    cutSizeVec_.assign(size + 1, 1);
    impactVec_.assign(size + 1, 0);
    flagVec_.assign(size + 1, 0);
    isCutVec_.assign(size + 1, false);

    std::vector<Node> candidateNodes;
    candidateNodes.reserve(size);

    timeStamp_ = 0;
    nodeRoot_ = 1;

    tarjanInComponent(componentIndex, nodeRoot_, nodeToIdx);

    int minImpact = std::numeric_limits<int>::max();
    candidateNodes.clear();

    for (int i = 1; i <= size; ++i)
    {
        int currentImpact = impactVec_[i];

        if (isCutVec_[i])
        {
            currentImpact += ((timeStamp_ - cutSizeVec_[i])
                              * (timeStamp_ - cutSizeVec_[i] - 1))
                             / 2;
        }
        else
        {
            currentImpact += ((timeStamp_ - 1) * (timeStamp_ - 2)) / 2;
        }

        if (currentImpact < minImpact)
        {
            minImpact = currentImpact;
            candidateNodes.clear();
            candidateNodes.push_back(component.nodes[i - 1]);
        }
        else if (currentImpact == minImpact)
        {
            candidateNodes.push_back(component.nodes[i - 1]);
        }
    }

    return candidateNodes.size() == 1
               ? candidateNodes[0]
               : candidateNodes[rng_.generateIndex(candidateNodes.size())];
}

void CNP_Graph::tarjanInComponent(ComponentIndex compIndex,
                                int nodeIdx,
                                const std::vector<int> &nodeToIdx) const
{
    dfn_[nodeIdx] = lowVec_[nodeIdx] = ++timeStamp_;

    Node nodeId = connectedComponents_[compIndex].nodes[nodeIdx - 1];

    for (Node neighbor : currentAdjList_[nodeId])
    {
        if (!isNodeRemoved(neighbor)
            && nodeToComponentIndex_[neighbor] == compIndex)
        {
            int neighborIdx = nodeToIdx[neighbor] + 1;

            if (dfn_[neighborIdx] == 0)
            {
                tarjanInComponent(compIndex, neighborIdx, nodeToIdx);

                lowVec_[nodeIdx]
                    = std::min(lowVec_[nodeIdx], lowVec_[neighborIdx]);

                if (dfn_[nodeIdx] < dfn_[neighborIdx])
                {
                    stSizeVec_[nodeIdx] += stSizeVec_[neighborIdx];
                }

                if (lowVec_[neighborIdx] >= dfn_[nodeIdx])
                {
                    flagVec_[nodeIdx]++;

                    if (nodeIdx != nodeRoot_)
                    {
                        isCutVec_[nodeIdx] = true;
                        cutSizeVec_[nodeIdx] += stSizeVec_[neighborIdx];
                        impactVec_[nodeIdx] += (stSizeVec_[neighborIdx]
                                               * (stSizeVec_[neighborIdx] - 1))
                                              / 2;
                    }
                    else if (nodeIdx == nodeRoot_ && flagVec_[nodeIdx] > 1)
                    {
                        isCutVec_[nodeIdx] = true;
                    }
                }
            }
            else
            {
                lowVec_[nodeIdx] = std::min(lowVec_[nodeIdx], dfn_[neighborIdx]);
            }
        }
    }
}

Node CNP_Graph::greedySelectNodeToAdd() const
{
    if (removedNodes.empty())
    {
        throw std::runtime_error("no removed nodes can be added");
    }

    std::vector<Node> candidateNodes;
    candidateNodes.reserve(removedNodes.size());

    auto it = removedNodes.begin();
    const Node firstNode = *it;
    int minDelta = calculateConnectionGain(firstNode);
    candidateNodes.push_back(firstNode);

    ++it;
    for (; it != removedNodes.end(); ++it)
    {
        Node currentNode = *it;
        int connectionGain = calculateConnectionGain(currentNode);

        if (connectionGain < minDelta)
        {
            minDelta = connectionGain;
            candidateNodes.clear();
            candidateNodes.push_back(currentNode);
        }
        else if (connectionGain == minDelta)
        {
            candidateNodes.push_back(currentNode);
        }
    }

    return candidateNodes.size() == 1
               ? candidateNodes[0]
               : candidateNodes[rng_.generateIndex(candidateNodes.size())];
}

Node CNP_Graph::randomSelectNodeToRemove() const
{
    ComponentIndex compIndex = rng_.generateIndex(connectedComponents_.size());
    const Component &selectedComponent = connectedComponents_[compIndex];

    if (selectedComponent.size == 0 || selectedComponent.nodes.empty())
    {
        throw std::runtime_error("selected component is empty, can not select node");
    }

    return selectedComponent.nodes[rng_.generateIndex(selectedComponent.size)];
}

int CNP_Graph::calculateConnectionGain(Node node) const
{
    std::vector<size_t> componentSizes(connectedComponents_.size(), 0);

    int totalSize = 1;

    const auto &neighbors = originalAdjList_[node];
    for (Node neighbor : neighbors)
    {
        if (nodeToComponentIndex_[neighbor] != -1)
        {
            ComponentIndex compIndex = nodeToComponentIndex_[neighbor];

            if (componentSizes[compIndex] == 0)
            {
                componentSizes[compIndex] = connectedComponents_[compIndex].size;
                totalSize += componentSizes[compIndex];
            }
        }
    }

    int oldConnectionsSum = 0;
    for (int size : componentSizes)
    {
        if (size > 0)
        {
            oldConnectionsSum += (size * (size - 1)) / 2;
        }
    }

    int newConnections = (totalSize * (totalSize - 1)) / 2;

    return newConnections - oldConnectionsSum;
}

std::unique_ptr<CNP_Graph> CNP_Graph::getRandomFeasibleGraph() const
{
    auto tempGraph = std::make_unique<CNP_Graph>(*this);
    Solution randomSolution;
    std::vector<Node> availableNodes(originalNodesSet_.begin(),
                                     originalNodesSet_.end());

    for (int i = 0; i < numToRemove_ && !availableNodes.empty(); ++i)
    {
        int randomIndex = rng_.generateIndex(availableNodes.size());
        Node node = availableNodes[randomIndex];

        randomSolution.insert(node);

        availableNodes[randomIndex] = availableNodes.back();
        availableNodes.pop_back();
    }

    tempGraph->updateGraphByRemovedNodes(randomSolution);
    return tempGraph;
}

std::unique_ptr<CNP_Graph> CNP_Graph::clone() const
{
    return std::make_unique<CNP_Graph>(*this);
}

bool CNP_Graph::isNodeRemoved(Node node) const
{
    return removedNodes.find(node) != removedNodes.end();
}

int CNP_Graph::getNumNodes() const
{
    return numNodes_;
}

const NodeSet& CNP_Graph::getRemovedNodes() const
{
    return removedNodes;
}

void CNP_Graph::setNodeAge(Node node, Age age)
{
    nodeAge_[node] = age;
}

int CNP_Graph::getObjectiveValue() const
{
    return connectedPairs_;
}