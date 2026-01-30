#include "ProblemData.h"
#include "Graph/CNP_Graph.h"
#include "Graph/DCNP_Graph.h"
#include <cstring>

ProblemData::ProblemData(int num)
{
    numNodes_ = num;
    nodesSet_.reserve(num);
    adjList_.resize(num);
}

void ProblemData::addNode(Node node)
{
    nodesSet_.insert(node);
}

void ProblemData::addEdge(Node u, Node v)
{
    adjList_[u].insert(v);
    adjList_[v].insert(u);
}

ProblemData ProblemData::readFromAdjacencyListFile(const std::string &filename)
{
    std::ifstream file(filename);
    if (!file.is_open())
    {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    int numNodes;
    file >> numNodes;
    if (file.eof())
    {
        throw std::runtime_error("File format error: empty file");
    }

    ProblemData problemData(numNodes);

    for (int v1 = 0; v1 < numNodes; v1++)
    {
        int node;
        file >> node;

        problemData.nodesSet_.insert(node);

        char c;
        while ((c = file.get()) != ':' && std::isspace(c))
            ;
        bool nextLine = false;

        while (!file.eof() && !nextLine)
        {

            while (std::isspace(file.peek()))
            {
                nextLine = (file.get() == '\n');
            }
            if (!nextLine)
            {
                int node2;
                file >> node2;

                problemData.adjList_[node].insert(node2);
            }
        }
    }
    file.close();
    return problemData;
}

ProblemData ProblemData::readFromEdgeListFormat(const std::string &filename)
{
    std::ifstream file(filename);
    if (!file.is_open())
    {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    char bidon[50];
    char StrReading[100];
    file >> StrReading;

    if (file.eof())
    {
        throw std::runtime_error("File format error: empty file");
    }

    int numNodes = 0;
    int numEdges = 0;

    while (!file.eof())
    {
        if (strcmp(StrReading, "p") == 0)
        {

            file >> bidon >> numNodes >> numEdges;
            break;
        }
        file >> StrReading;
    }

    ProblemData problemData(numNodes);

    for (int i = 0; i < numNodes; i++)
    {
        problemData.nodesSet_.insert(i);
    }

    int x1, x2;
    int linecount = 0;

    while (!file.eof())
    {
        if (strcmp(StrReading, "e") == 0)
        {

            file >> x1 >> x2;
            linecount++;

            if (x1 < 0 || x2 < 0 || x1 >= numNodes || x2 >= numNodes)
            {
                throw std::runtime_error(
                    "Node index error: x1=" + std::to_string(x1)
                    + ", x2=" + std::to_string(x2)
                    + ", line number=" + std::to_string(linecount));
            }

            problemData.adjList_[x1].insert(x2);
            problemData.adjList_[x2].insert(x1);
        }
        file >> StrReading;
    }

    file.close();

    return problemData;
}

std::unique_ptr<Graph> ProblemData::createOriginalGraph(
    const std::string &problemType, int numToRemove, int seed, int hop_distance) const
{
    if (problemType == "CNP")
    {

        if (numToRemove > static_cast<int>(nodesSet_.size()))
        {
            throw std::runtime_error("The number of nodes to remove cannot be greater than the total number of nodes");
        }
        return std::make_unique<Graph>(
            std::make_unique<CNP_Graph>(nodesSet_, adjList_, numToRemove, seed));
    }
    else if (problemType == "DCNP")
    {

        if (numToRemove > static_cast<int>(nodesSet_.size()))
        {
            throw std::runtime_error("The number of nodes to remove cannot be greater than the total number of nodes");
        }
        return std::make_unique<Graph>(std::make_unique<DCNP_Graph>(
            nodesSet_, hop_distance, adjList_, numToRemove, seed));
    }
    else
    {
        throw std::runtime_error("Unknown problem type: " + problemType);
    }
}

int ProblemData::numNodes() const
{
    return numNodes_;
}

NodeSet ProblemData::getNodesSet() const
{
    return nodesSet_;
}

const std::vector<NodeSet> &ProblemData::getAdjList() const
{
    return adjList_;
}
