#ifndef DCNP_GRAPH_H
#define DCNP_GRAPH_H

#include "../RandomNumberGenerator.h"
#include "Types.h"
#include <algorithm>
#include <cstdint>
#include <list>
#include <memory>
#include <numeric>
#include <queue>
#include <stack>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

/**
 * DCNP_Graph
 *
 * Graph implementation for the Distance-Based Critical Node Problem (DCNP).
 *
 * Represents a graph where the objective is to maximize pairwise distance after node removal.
 */
class DCNP_Graph
{
private:
    int numNodes_;
    int kHops_;        ///< K-hop limit.
    int numToRemove_;
    NodeSet originalNodesSet_;  ///< Set storing all original nodes.
    NodeSet initialNodesSet_;   ///< Immutable snapshot of the original node set.
    std::vector<Age> nodeAge_;  ///< Stores the "age" of each node.

    std::vector<NodeSet> currentAdjList_;   ///< Current adjacency list.
    std::vector<NodeSet> originalAdjList_;  ///< Original adjacency list.
    std::vector<NodeSet> initialAdjList_;   ///< Immutable snapshot of the original adjacency list.

    /**
     * K-hop tree adjacency information (flattened).
     * `(v, u)` at `v * numNodes + u` is 1 if u is in v's K-hop tree, else 0.
     */
    std::vector<uint8_t> intree_;

    /**
     * K-hop tree sizes for each node.
     * `treeSize[v]` is total nodes reachable from `v` within K hops.
     */
    std::vector<int> treeSize_;
    NodeSet removedNodes_;  ///< Nodes currently removed.

    mutable RandomNumberGenerator rng_;
    int initialSeed_ = 0;
    int initialNumToRemove_ = 0;
    int initialKHops_ = 0;
    mutable std::vector<uint8_t> bfsVisited_;
    mutable std::vector<int> bfsLevel_;
    mutable std::vector<Node> bfsQueue_;

    // Helper: Builds K-hop tree for node v using BFS.
    void bfsKTree(Node v);

public:
    DCNP_Graph(NodeSet nodes,
               int K,
               std::vector<NodeSet> adjList,
               int numToRemove,
               int seed);

    DCNP_Graph() = default;

    /**
     * Updates the graph to reflect node removals for DCNP.
     *
     * Parameters
     * ----------
     * nodesToRemove : NodeSet
     *     Set of nodes that have been removed.
     */
    void updateGraphByRemovedNodes(const NodeSet &nodesToRemove);

    /**
     * Creates a reduced graph after node removal for DCNP.
     *
     * Parameters
     * ----------
     * nodesToRemove : NodeSet
     *     Set of nodes to remove.
     *
     * Returns
     * -------
     * DCNP_Graph
     *     The reduced graph.
     */
    void getReducedGraphByRemovedNodes(const NodeSet &nodesToRemove);

    /**
     * Removes a node from the DCNP graph.
     *
     * Parameters
     * ----------
     * node : Node
     *     The node to remove.
     */
    void removeNode(Node node);

    /**
     * Adds a node back to the DCNP graph.
     *
     * Parameters
     * ----------
     * node : Node
     *     The node to add.
     */
    void addNode(Node node);

    /**
     * Sets the age of a node in the DCNP graph.
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
     * Checks if a node has been removed from the DCNP graph.
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
     * Returns the set of removed nodes for DCNP.
     *
     * Returns
     * -------
     * NodeSet
     *     Set of nodes that have been removed.
     */
    const NodeSet& getRemovedNodes() const;

    /**
     * Returns the total number of nodes in the DCNP graph.
     *
     * Returns
     * -------
     * int
     *     Number of nodes.
     */
    int getNumNodes() const;

    /**
     * Calculates the objective value (pairwise distance) for DCNP.
     *
     * Returns
     * -------
     * int
     *     The pairwise distance after node removal.
     */
    int getObjectiveValue() const;

    // Generate a random feasible solution.
    std::unique_ptr<DCNP_Graph> getRandomFeasibleGraph() const;

    // Build/rebuild K-hop tree info for all unremoved nodes.
    void buildTree();

    // Calculate sum of K-hop tree sizes.
    int calculateKhopTreeSize() const;

    // Calculate betweenness centrality for active nodes.
    const std::vector<double> &calculateBetweennessCentrality() const;

    // Find best node to remove (heuristic).
    Node findBestNodeToRemove();

    // Find best node to add back (heuristic).
    Node findBestNodeToAdd();

    // Randomly select a node to remove.
    Node randomSelectNodeToRemove() const;

    // Create a deep copy.
    std::unique_ptr<DCNP_Graph> clone() const;
};

#endif  // DCNP_GRAPH_H
