#include "Graph.h"

namespace {
    const std::vector<double> EMPTY_DOUBLE_VEC;
}

Graph::Graph(std::unique_ptr<CNP_Graph> cnp)
    : impl(std::move(cnp)), kind_(Kind::CNP)
{
}

Graph::Graph(std::unique_ptr<DCNP_Graph> dcnp)
    : impl(std::move(dcnp)), kind_(Kind::DCNP)
{
}

Graph::Graph(const Graph &other)
    : kind_(other.kind_)
{
    impl = std::visit(
        [](const auto &ptr) -> std::variant<std::unique_ptr<CNP_Graph>, std::unique_ptr<DCNP_Graph>> {
            using T = std::decay_t<decltype(ptr)>;
            return std::make_unique<typename T::element_type>(*ptr);
        },
        other.impl);
}

Graph &Graph::operator=(const Graph &other)
{
    if (this != &other)
    {
        kind_ = other.kind_;
        impl = std::visit(
            [](const auto &ptr) -> std::variant<std::unique_ptr<CNP_Graph>, std::unique_ptr<DCNP_Graph>> {
                using T = std::decay_t<decltype(ptr)>;
                return std::make_unique<typename T::element_type>(*ptr);
            },
            other.impl);
    }
    return *this;
}

std::unique_ptr<Graph> Graph::clone() const
{
    return std::make_unique<Graph>(*this);
}

void Graph::updateGraphByRemovedNodes(const NodeSet &nodesToRemove)
{
    std::visit(
        [&](auto &ptr) { ptr->updateGraphByRemovedNodes(nodesToRemove); },
        impl);
}

void Graph::getReducedGraphByRemovedNodes(const NodeSet &nodesToRemove)
{
    std::visit(
        [&](auto &ptr) { ptr->getReducedGraphByRemovedNodes(nodesToRemove); },
        impl);
}

void Graph::removeNode(Node node)
{
    std::visit([&](auto &ptr) { ptr->removeNode(node); }, impl);
}

void Graph::addNode(Node node)
{
    std::visit([&](auto &ptr) { ptr->addNode(node); }, impl);
}

void Graph::setNodeAge(Node node, Age age)
{
    std::visit([&](auto &ptr) { ptr->setNodeAge(node, age); }, impl);
}

int Graph::getObjectiveValue() const
{
    return std::visit([](const auto &ptr) { return ptr->getObjectiveValue(); }, impl);
}

std::unique_ptr<Graph> Graph::getRandomFeasibleGraph() const
{
    return std::visit(
        [](const auto &ptr) {
            auto cloned = ptr->getRandomFeasibleGraph();
            return std::make_unique<Graph>(std::move(cloned));
        },
        impl);
}

bool Graph::isNodeRemoved(Node node) const
{
    return std::visit([&](const auto &ptr) { return ptr->isNodeRemoved(node); }, impl);
}

const NodeSet &Graph::getRemovedNodes() const
{
    return std::visit([](const auto &ptr) -> const NodeSet & { return ptr->getRemovedNodes(); }, impl);
}

int Graph::getNumNodes() const
{
    return std::visit([](const auto &ptr) { return ptr->getNumNodes(); }, impl);
}

ComponentIndex Graph::selectRemovedComponent() const
{
    if (isDCNP())
    {
        throw std::runtime_error("selectRemovedComponent is only available for CNP graphs");
    }
    return std::get<std::unique_ptr<CNP_Graph>>(impl)->selectRemovedComponent();
}

Node Graph::randomSelectNodeFromComponent(ComponentIndex componentIndex) const
{
    if (isDCNP())
    {
        throw std::runtime_error("randomSelectNodeFromComponent is only available for CNP graphs");
    }
    return std::get<std::unique_ptr<CNP_Graph>>(impl)->randomSelectNodeFromComponent(componentIndex);
}

Node Graph::impactSelectNodeFromComponent(ComponentIndex componentIndex) const
{
    if (isDCNP())
    {
        throw std::runtime_error("impactSelectNodeFromComponent is only available for CNP graphs");
    }
    return std::get<std::unique_ptr<CNP_Graph>>(impl)->impactSelectNodeFromComponent(componentIndex);
}

Node Graph::ageSelectNodeFromComponent(ComponentIndex componentIndex) const
{
    if (isDCNP())
    {
        throw std::runtime_error("ageSelectNodeFromComponent is only available for CNP graphs");
    }
    return std::get<std::unique_ptr<CNP_Graph>>(impl)->ageSelectNodeFromComponent(componentIndex);
}

Node Graph::greedySelectNodeToAdd() const
{
    if (isDCNP())
    {
        // For DCNP, fallback to best-node heuristic if available
        return std::get<std::unique_ptr<DCNP_Graph>>(impl)->findBestNodeToAdd();
    }
    return std::get<std::unique_ptr<CNP_Graph>>(impl)->greedySelectNodeToAdd();
}

Node Graph::randomSelectNodeToRemove() const
{
    return std::visit([&](const auto &ptr) { return ptr->randomSelectNodeToRemove(); }, impl);
}

int Graph::calculateConnectionGain(Node node) const
{
    if (isDCNP())
    {
        return 0;
    }
    return std::get<std::unique_ptr<CNP_Graph>>(impl)->calculateConnectionGain(node);
}

void Graph::buildTree()
{
    if (isDCNP())
    {
        std::get<std::unique_ptr<DCNP_Graph>>(impl)->buildTree();
    }
}

int Graph::calculateKhopTreeSize() const
{
    if (isDCNP())
    {
        return std::get<std::unique_ptr<DCNP_Graph>>(impl)->calculateKhopTreeSize();
    }
    return 0;
}

const std::vector<double> &Graph::calculateBetweennessCentrality() const
{
    if (isDCNP())
    {
        return std::get<std::unique_ptr<DCNP_Graph>>(impl)->calculateBetweennessCentrality();
    }
    return EMPTY_DOUBLE_VEC;
}

Node Graph::findBestNodeToRemove()
{
    if (isDCNP())
    {
        return std::get<std::unique_ptr<DCNP_Graph>>(impl)->findBestNodeToRemove();
    }
    // For CNP fallback to random removal
    return randomSelectNodeToRemove();
}

Node Graph::findBestNodeToAdd()
{
    if (isDCNP())
    {
        return std::get<std::unique_ptr<DCNP_Graph>>(impl)->findBestNodeToAdd();
    }
    return greedySelectNodeToAdd();
}

CNP_Graph *Graph::asCNP()
{
    return isCNP() ? std::get<std::unique_ptr<CNP_Graph>>(impl).get() : nullptr;
}

const CNP_Graph *Graph::asCNP() const
{
    return isCNP() ? std::get<std::unique_ptr<CNP_Graph>>(impl).get() : nullptr;
}

DCNP_Graph *Graph::asDCNP()
{
    return isDCNP() ? std::get<std::unique_ptr<DCNP_Graph>>(impl).get() : nullptr;
}

const DCNP_Graph *Graph::asDCNP() const
{
    return isDCNP() ? std::get<std::unique_ptr<DCNP_Graph>>(impl).get() : nullptr;
}
