#ifndef GRAPH_TYPES_H
#define GRAPH_TYPES_H

#include <unordered_set>
#include <vector>

using Node = int;
using Age = int;
using NodeSet = std::unordered_set<Node>;
using ComponentIndex = int;
using Solution = NodeSet;

/**
 * Represents a connected component in the graph.
 */
struct Component
{
    size_t size;              ///< Number of nodes in this connected component.
    std::vector<Node> nodes;  ///< List of all nodes contained in this connected component.
    Component() noexcept : size(0) {}
};

using Components = std::vector<Component>;

constexpr Node INVALID_NODE = -1;

#endif  // GRAPH_TYPES_H
