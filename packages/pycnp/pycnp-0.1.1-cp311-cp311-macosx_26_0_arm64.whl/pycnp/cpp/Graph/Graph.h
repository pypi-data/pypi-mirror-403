#ifndef GRAPH_H
#define GRAPH_H

#include "Types.h"
#include "CNP_Graph.h"
#include "DCNP_Graph.h"

#include <memory>
#include <stdexcept>
#include <variant>
#include <vector>

/**
 * Graph
 *
 * Lightweight wrapper over concrete graph implementations (CNP_Graph / DCNP_Graph).
 */
class Graph
{
public:
    enum class Kind
    {
        CNP,
        DCNP
    };

    explicit Graph(std::unique_ptr<CNP_Graph> cnp);
    explicit Graph(std::unique_ptr<DCNP_Graph> dcnp);

    Graph(const Graph &other);
    Graph(Graph &&) noexcept = default;
    Graph &operator=(const Graph &other);
    Graph &operator=(Graph &&) noexcept = default;

    Kind kind() const noexcept { return kind_; }
    bool isCNP() const noexcept { return kind_ == Kind::CNP; }
    bool isDCNP() const noexcept { return kind_ == Kind::DCNP; }

    std::unique_ptr<Graph> clone() const;

    void updateGraphByRemovedNodes(const NodeSet &nodesToRemove);
    void getReducedGraphByRemovedNodes(const NodeSet &nodesToRemove);
    void removeNode(Node node);
    void addNode(Node node);
    void setNodeAge(Node node, Age age);
    int getObjectiveValue() const;
    std::unique_ptr<Graph> getRandomFeasibleGraph() const;
    bool isNodeRemoved(Node node) const;
    const NodeSet &getRemovedNodes() const;
    int getNumNodes() const;

    // CNP-oriented helpers
    ComponentIndex selectRemovedComponent() const;
    Node randomSelectNodeFromComponent(ComponentIndex componentIndex) const;
    Node impactSelectNodeFromComponent(ComponentIndex componentIndex) const;
    Node ageSelectNodeFromComponent(ComponentIndex componentIndex) const;
    Node greedySelectNodeToAdd() const;
    Node randomSelectNodeToRemove() const;
    int calculateConnectionGain(Node node) const;

    // DCNP-oriented helpers
    void buildTree();
    int calculateKhopTreeSize() const;
    const std::vector<double> &calculateBetweennessCentrality() const;
    Node findBestNodeToRemove();
    Node findBestNodeToAdd();

    CNP_Graph *asCNP();
    const CNP_Graph *asCNP() const;
    DCNP_Graph *asDCNP();
    const DCNP_Graph *asDCNP() const;

private:
    std::variant<std::unique_ptr<CNP_Graph>, std::unique_ptr<DCNP_Graph>> impl;
    Kind kind_;
};

#endif  // GRAPH_H
