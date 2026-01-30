#ifndef CNP_GRAPH_H
#define CNP_GRAPH_H

#include "../RandomNumberGenerator.h"
#include "Types.h"
#include <cctype>
#include <fstream>
#include <iostream>
#include <memory>
#include <queue>
#include <set>
#include <string>
#include <unordered_set>
#include <vector>

/**
 * CNP_Graph
 *
 * Graph implementation for the Critical Node Problem (CNP).
 *
 * Represents a graph where the objective is to minimize connectivity after node removal.
 */
class CNP_Graph
{
private:
    int numNodes_;              ///< Number of vertices
    NodeSet originalNodesSet_;  ///< Set of all existing nodes
    NodeSet initialNodesSet_;   ///< Snapshot of the original node set
    std::vector<Age> nodeAge_;  ///< Node "age"

    std::vector<NodeSet> currentAdjList_;   ///< Current adjacency list
    std::vector<NodeSet> originalAdjList_;  ///< Original adjacency list
    std::vector<NodeSet> initialAdjList_;   ///< Immutable copy of the original adjacency list

    int numToRemove_;
    int initialNumToRemove_ = 0;
    std::vector<ComponentIndex>
        nodeToComponentIndex_;  ///< Stores the component index for each vertex
    std::vector<Component> connectedComponents_;
    int connectedPairs_;
    mutable RandomNumberGenerator rng_;
    int initialSeed_ = 0;

    // Selects the larger component to remove.
    ComponentIndex selectRemovedLargerComponent() const;

    // Tarjan algorithm auxiliary variables
    mutable std::vector<int> dfn_;         ///< Node discovery time
    mutable std::vector<int> lowVec_;      ///< Minimum discovery time reachable by node
    mutable std::vector<int> stSizeVec_;   ///< Subtree size
    mutable std::vector<int> cutSizeVec_;  ///< Cut size
    mutable std::vector<int> impactVec_;   ///< Node impact
    mutable std::vector<int> flagVec_;     ///< Flag vector
    mutable std::vector<bool> isCutVec_;   ///< Whether node is a cut vertex
    mutable int timeStamp_;                ///< Timestamp
    mutable int nodeRoot_;                 ///< Root node
    mutable std::vector<char> componentVisited_;  ///< Scratch buffer for component marking
    mutable std::vector<int> dfsVisitEpoch_;      ///< Visit epochs for DFS
    mutable int dfsCurrentEpoch_ = 0;             ///< Current epoch id
    mutable std::vector<Node> dfsStack_;          ///< Reusable DFS stack

    // Implementation of Tarjan algorithm in connected component.
    void tarjanInComponent(ComponentIndex compIndex,
                        int nodeIdx,
                        const std::vector<int> &nodeToIdx) const;

public:
    NodeSet removedNodes;

    /**
     * Creates a deep copy of the graph.
     *
     * Returns
     * -------
     * CNP_Graph
     *     A new graph instance with the same structure.
     */
    std::unique_ptr<CNP_Graph> clone() const;

    CNP_Graph(NodeSet nodes, std::vector<NodeSet> adjList, int budget, int seed);

    CNP_Graph() {};

    /**
     * Updates the graph to reflect node removals.
     *
     * Parameters
     * ----------
     * removedNodes : NodeSet
     *     Set of nodes that have been removed.
     */
    void updateGraphByRemovedNodes(const NodeSet &removedNodes);

    /**
     * Creates a reduced graph after node removal.
     *
     * Parameters
     * ----------
     * nodesToRemove : NodeSet
     *     Set of nodes to remove.
     *
     * Returns
     * -------
     * CNP_Graph
     *     The reduced graph.
     */
    void getReducedGraphByRemovedNodes(const NodeSet &nodesToRemove);

    /**
     * Adds a node back to the graph.
     *
     * Parameters
     * ----------
     * node : Node
     *     The node to add.
     */
    void addNode(Node node);

    /**
     * Removes a node from the graph.
     *
     * Parameters
     * ----------
     * node : Node
     *     The node to remove.
     */
    void removeNode(Node node);

    /**
     * Checks if a node has been removed.
     *
     * Parameters
     * ----------
     * node : Node
     *     The node to check.
     *
     * Returns
     * -------
     * bool
     *     True if the node has been removed.
     */
    bool isNodeRemoved(Node node) const;

    /**
     * Returns the total number of nodes in the graph.
     *
     * Returns
     * -------
     * int
     *     Number of nodes.
     */
    int getNumNodes() const;

    /**
     * Returns the set of removed nodes.
     *
     * Returns
     * -------
     * NodeSet
     *     Set of nodes that have been removed.
     */
    const NodeSet& getRemovedNodes() const;

    /**
     * Sets the age of a node.
     *
     * Parameters
     * ----------
     * node : Node
     *     The node.
     * age : Age
     *     The age value.
     */
    void setNodeAge(Node node, Age age);

    /**
     * Calculates the objective value (connectivity) of the graph.
     *
     * Returns
     * -------
     * int
     *     The connectivity after node removal.
     */
    int getObjectiveValue() const;

    // Converts to random feasible solution.
    std::unique_ptr<CNP_Graph> getRandomFeasibleGraph() const;

    // Initializes components and node mapping.
    void initializeComponentsAndMapping();

    // Finds connected component using DFS.
    Component dfsFindComponent(Node startNode) const;

    // Selects component to remove.
    ComponentIndex selectRemovedComponent() const;

    // Randomly selects node to remove from specified component.
    Node randomSelectNodeFromComponent(ComponentIndex componentIndex) const;

    // Selects node to remove from component based on weight.
    Node ageSelectNodeFromComponent(ComponentIndex componentIndex) const;

    // Selects node with minimum impact to remove from component.
    Node impactSelectNodeFromComponent(ComponentIndex componentIndex) const;

    // Selects node to add back to graph.
    Node greedySelectNodeToAdd() const;

    // Randomly selects a node to remove.
    Node randomSelectNodeToRemove() const;

    // Calculates connection gain after adding a node.
    int calculateConnectionGain(Node node) const;
};

#endif
