
#include "DCNP_Graph.h"
#include <algorithm>

namespace
{
inline size_t treeIndex(int numNodes, Node row, Node col)
{
    return static_cast<size_t>(row) * static_cast<size_t>(numNodes)
        + static_cast<size_t>(col);
}
}

DCNP_Graph::DCNP_Graph(NodeSet nodes,
                    int K,
                    std::vector<NodeSet> adjList,
                    int numToRemove,
                    int seed)
{
    numNodes_ = nodes.size();
    kHops_ = K;
    originalNodesSet_ = nodes;
    initialNodesSet_ = nodes;
    originalAdjList_ = adjList;
    currentAdjList_ = adjList;
    initialAdjList_ = adjList;
    numToRemove_ = numToRemove;
    initialNumToRemove_ = numToRemove;
    initialKHops_ = K;
    rng_.setSeed(seed);
    initialSeed_ = seed;

    nodeAge_.resize(numNodes_, 0);

    intree_.assign(static_cast<size_t>(numNodes_) * static_cast<size_t>(numNodes_),
                  0);

    treeSize_.resize(numNodes_, 0);
    bfsVisited_.resize(numNodes_, 0);
    bfsLevel_.resize(numNodes_, 0);
    bfsQueue_.resize(numNodes_);

    buildTree();
}

void DCNP_Graph::bfsKTree(Node v)
{

    auto rowBegin = intree_.begin()
        + treeIndex(numNodes_, v, 0);
    std::fill(rowBegin,
              rowBegin + static_cast<size_t>(numNodes_),
              static_cast<uint8_t>(0));

    if (isNodeRemoved(v))
    {
        treeSize_[v] = 0;
        return;
    }

    if (bfsVisited_.size() < static_cast<size_t>(numNodes_))
    {
        bfsVisited_.resize(numNodes_, 0);
    }
    else
    {
        std::fill(bfsVisited_.begin(),
                  bfsVisited_.begin() + numNodes_,
                  static_cast<uint8_t>(0));
    }
    if (bfsLevel_.size() < static_cast<size_t>(numNodes_))
    {
        bfsLevel_.resize(numNodes_, 0);
    }
    if (bfsQueue_.size() < static_cast<size_t>(numNodes_))
    {
        bfsQueue_.resize(numNodes_);
    }

    size_t head = 0;
    size_t tail = 0;
    bfsQueue_[tail++] = v;
    bfsVisited_[v] = 1;
    bfsLevel_[v] = 0;

    size_t visitedCount = 0;

    while (head < tail)
    {
        Node currentNode = bfsQueue_[head++];

        if (bfsLevel_[currentNode] < kHops_)
        {

            for (Node neighbor : currentAdjList_[currentNode])
            {
                if (isNodeRemoved(neighbor) || bfsVisited_[neighbor])
                {
                    continue;
                }
                bfsQueue_[tail++] = neighbor;
                bfsVisited_[neighbor] = 1;
                bfsLevel_[neighbor] = bfsLevel_[currentNode] + 1;
            }
        }

        intree_[treeIndex(numNodes_, v, currentNode)] = static_cast<uint8_t>(1);
        ++visitedCount;
    }

    treeSize_[v]
        = visitedCount > 0 ? static_cast<int>(visitedCount - 1) : 0;
}

void DCNP_Graph::buildTree()
{
    for (int i = 0; i < numNodes_; i++)
    {
        bfsKTree(i);
    }
}

void DCNP_Graph::updateGraphByRemovedNodes(const NodeSet &nodesToRemove)
{

    removedNodes_.clear();

    currentAdjList_ = originalAdjList_;

    for (Node node : nodesToRemove)
    {
        removedNodes_.insert(node);
    }

    buildTree();
}

void DCNP_Graph::getReducedGraphByRemovedNodes(const NodeSet &removeSet)
{

    removedNodes_.clear();

    numToRemove_ -= removeSet.size();

    for (Node node : removeSet)
    {

        originalNodesSet_.erase(node);

        for (Node neighbor : currentAdjList_[node])
        {
            originalAdjList_[neighbor].erase(node);
        }

        originalAdjList_[node].clear();
    }

    currentAdjList_ = originalAdjList_;

    buildTree();
}

void DCNP_Graph::addNode(Node nodeToAdd)
{

    removedNodes_.erase(nodeToAdd);

    bfsKTree(nodeToAdd);

    for (int i = 0; i < numNodes_; i++)
    {

        if (intree_[treeIndex(numNodes_, nodeToAdd, i)])
        {
            bfsKTree(i);
        }
    }
}

void DCNP_Graph::removeNode(Node nodeToRemove)
{

    removedNodes_.insert(nodeToRemove);

    for (int i = 0; i < numNodes_; i++)
    {

        if (intree_[treeIndex(numNodes_, i, nodeToRemove)])
        {
            bfsKTree(i);
        }
    }
}

const std::vector<double> &DCNP_Graph::calculateBetweennessCentrality() const
{

    static std::vector<double> betweenness;
    betweenness.resize(numNodes_, 0.0);

    for (int s = 0; s < numNodes_; s++)
    {
        if (isNodeRemoved(s))
            continue;

        std::stack<int> S;

        std::vector<std::list<int>> P(numNodes_);

        std::vector<int> d(numNodes_, -1);

        std::vector<int> sigma(numNodes_, 0);

        sigma[s] = 1;
        d[s] = 0;

        std::queue<int> Q;
        Q.push(s);

        while (!Q.empty())
        {
            int v = Q.front();
            Q.pop();

            S.push(v);

            for (Node w : currentAdjList_[v])
            {

                if (isNodeRemoved(w))
                    continue;

                if (d[w] < 0)
                {
                    Q.push(w);
                    d[w] = d[v] + 1;
                }

                if (d[w] == d[v] + 1)
                {

                    sigma[w] += sigma[v];

                    P[w].push_back(v);
                }
            }
        }

        std::vector<double> delta(numNodes_, 0.0);

        while (!S.empty())
        {
            int w = S.top();
            S.pop();

            for (auto v : P[w])
            {

                delta[v] += (static_cast<double>(sigma[v]) / sigma[w])
                            * (1.0 + delta[w]);
            }

            if (w != s)
            {
                betweenness[w] += delta[w];
            }
        }
    }

    return betweenness;
}

int DCNP_Graph::calculateKhopTreeSize() const
{
    int sum = 0;

    for (int i = 0; i < numNodes_; i++)
    {
        if (!isNodeRemoved(i))
        {
            sum += treeSize_[i];
        }
    }

    return sum / 2;
}

std::unique_ptr<DCNP_Graph> DCNP_Graph::getRandomFeasibleGraph() const
{
    auto tempGraph = std::make_unique<DCNP_Graph>(*this);

    NodeSet nodesToRemove;

    std::vector<Node> availableNodes(originalNodesSet_.begin(),
                                    originalNodesSet_.end());

    for (int i = 0; i < numToRemove_ && !availableNodes.empty(); i++)
    {

        int randomIndex = rng_.generateIndex(availableNodes.size());
        nodesToRemove.insert(availableNodes[randomIndex]);

        availableNodes[randomIndex] = availableNodes.back();
        availableNodes.pop_back();
    }

    tempGraph->updateGraphByRemovedNodes(nodesToRemove);

    return tempGraph;
}

Node DCNP_Graph::findBestNodeToRemove()
{

    int currentObjective = calculateKhopTreeSize();
    Node bestNode = INVALID_NODE;
    std::vector<Node> bestList;
    int maxImprovement = 0;

    for (int i = 0; i < numNodes_; i++)
    {
        if (!isNodeRemoved(i))
        {

            removeNode(i);
            int newObjective = calculateKhopTreeSize();

            int improvement = currentObjective - newObjective;

            if (improvement > maxImprovement)
            {
                maxImprovement = improvement;
                bestNode = i;
                bestList.clear();
                bestList.push_back(bestNode);
            }

            else if (improvement == maxImprovement)
            {
                bestList.push_back(i);
            }

            addNode(i);
        }
    }

    if (bestList.size() > 1)
    {
        bestNode = bestList[rng_.generateIndex(bestList.size())];
    }

    return bestNode;
}

Node DCNP_Graph::findBestNodeToAdd()
{

    NodeSet solution = getRemovedNodes();
    int currentObjective = calculateKhopTreeSize();
    Node bestNode = INVALID_NODE;
    std::vector<Node> bestList;
    int minDeterioration = std::numeric_limits<int>::max();

    for (Node node : solution)
    {

        addNode(node);
        int newObjective = calculateKhopTreeSize();

        int deterioration = newObjective - currentObjective;

        if (deterioration < minDeterioration)
        {
            minDeterioration = deterioration;
            bestNode = node;
            bestList.clear();
            bestList.push_back(bestNode);
        }

        else if (deterioration == minDeterioration)
        {
            bestList.push_back(node);
        }

        removeNode(node);
    }

    if (bestList.size() > 1)
    {
        bestNode = bestList[rng_.generateIndex(bestList.size())];
    }

    return bestNode;
}

Node DCNP_Graph::randomSelectNodeToRemove() const
{

    int randomIndex = rng_.generateIndex(numNodes_);
    while (isNodeRemoved(randomIndex))
    {
        randomIndex = rng_.generateIndex(numNodes_);
    }
    return randomIndex;
}

std::unique_ptr<DCNP_Graph> DCNP_Graph::clone() const
{
    return std::make_unique<DCNP_Graph>(*this);
}

void DCNP_Graph::setNodeAge(Node node, Age age)
{
    nodeAge_[node] = age;
}

bool DCNP_Graph::isNodeRemoved(Node node) const
{
    return removedNodes_.count(node) > 0;
}

const NodeSet& DCNP_Graph::getRemovedNodes() const
{
    return removedNodes_;
}

int DCNP_Graph::getNumNodes() const
{
    return numNodes_;
}

int DCNP_Graph::getObjectiveValue() const
{
    return calculateKhopTreeSize();
}
