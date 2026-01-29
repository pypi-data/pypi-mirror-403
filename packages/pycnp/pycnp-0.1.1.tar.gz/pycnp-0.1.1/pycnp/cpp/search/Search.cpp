#include "Search.h"
#include <stdexcept>

Search::Search(Graph &graph, int seed) : graph_(graph), seed_(seed)
{
    registerStrategies();
}

Search::~Search() = default;

void Search::registerStrategies()
{

    strategyFactory_["CBNS"]
        = [](Graph &g, const std::unordered_map<std::string, std::any> &params)
    { return std::make_unique<CBNSStrategy>(g, params); };

    strategyFactory_["DLAS"]
        = [](Graph &g, const std::unordered_map<std::string, std::any> &params)
    { return std::make_unique<DLASStrategy>(g, params); };

    strategyFactory_["CHNS"]
        = [](Graph &g, const std::unordered_map<std::string, std::any> &params)
    { return std::make_unique<CHNSStrategy>(g, params); };

    strategyFactory_["BCLS"]
        = [](Graph &g, const std::unordered_map<std::string, std::any> &params)
    { return std::make_unique<BCLSStrategy>(g, params); };
}

void Search::setStrategy(const std::string &strategyName)
{
    auto it = strategyFactory_.find(strategyName);
    if (it != strategyFactory_.end())
    {

        auto paramsWithSeed = params_;
        paramsWithSeed["seed"] = seed_;
        strategy_ = it->second(graph_, paramsWithSeed);
    }
    else
    {
        throw std::invalid_argument("unknown search strategy: " + strategyName);
    }
}

SearchResult Search::run()
{
    if (!strategy_)
    {
        throw std::runtime_error("search strategy is not set");
    }
    return strategy_->execute();
}