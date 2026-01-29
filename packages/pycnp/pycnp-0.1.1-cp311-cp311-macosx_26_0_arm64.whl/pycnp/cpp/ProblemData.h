#ifndef PROBLEMDATA_H
#define PROBLEMDATA_H

#include <fstream>
#include "Graph/Graph.h"
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

/**
 * ProblemData
 *
 * Stores the data for a graph problem instance.
 *
 * Contains node information, adjacency list, and provides methods to create graph objects.
 */
class ProblemData
{
private:
    int numNodes_;
    NodeSet nodesSet_;
    std::vector<NodeSet> adjList_;

public:

    /**
     * Creates a ProblemData instance with the specified number of nodes.
     *
     * Parameters
     * ----------
     * num : int
     *     The number of nodes.
     */
    ProblemData(int num);

    /**
     * Reads problem data from an adjacency list format file.
     *
     * Adjacency list format: each line represents a node and its neighbors.
     *
     * Parameters
     * ----------
     * filename : str
     *     Path to the adjacency list file.
     *
     * Returns
     * -------
     * ProblemData
     *     The loaded problem data.
     */
    static ProblemData readFromAdjacencyListFile(const std::string &filename);

    /**
     * Reads problem data from an edge list format file.
     *
     * Edge list format: contains a header line with node/edge counts,
     * followed by edge definitions.
     *
     * Parameters
     * ----------
     * filename : str
     *     Path to the edge list file.
     *
     * Returns
     * -------
     * ProblemData
     *     The loaded problem data.
     */
    static ProblemData readFromEdgeListFormat(const std::string &filename);

    /**
     * Returns the number of nodes in the problem data.
     *
     * Returns
     * -------
     * int
     *     Number of nodes.
     */
    int numNodes() const;

    /**
     * Returns the set of all nodes.
     *
     * Returns
     * -------
     * NodeSet
     *     Set of node IDs.
     */
    NodeSet getNodesSet() const;

    /**
     * Returns the adjacency list representation of the graph.
     *
     * Returns
     * -------
     * vector<NodeSet>
     *     Adjacency list where each index contains the neighbors of that node.
     */
    const std::vector<NodeSet> &getAdjList() const;

    /**
     * Adds a node to the problem data.
     *
     * Parameters
     * ----------
     * node : Node
     *     The ID of the node to add.
     */
    void addNode(Node node);

    /**
     * Adds an edge between two nodes.
     *
     * Parameters
     * ----------
     * u : Node
     *     The ID of the first node.
     * v : Node
     *     The ID of the second node.
     */
    void addEdge(Node u, Node v);

    /**
     * Creates an original graph from the problem data.
     *
     * Parameters specify the problem type, number of nodes to remove, seed, and hop distance.
     *
     * Parameters
     * ----------
     * problemType : str
     *     The type of problem ("CNP" or "DCNP").
     * numToRemove : int
     *     The number of nodes to remove.
     * seed : int
     *     Random seed for reproducibility.
     * hop_distance : int
     *     Maximum hop distance for DCNP.
     *
     * Returns
     * -------
     * Graph
     *     A unique pointer to the created graph.
     */
    std::unique_ptr<Graph> createOriginalGraph(const std::string &problemType,
                                               int numToRemove,
                                               int seed,
                                               int hop_distance) const;
};

#endif  // PROBLEMDATA_H
