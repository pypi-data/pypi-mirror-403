#include "Population.h"
#include <algorithm>
#include <iostream>
#include <cstdio>
#include <limits>
#include <memory>
#include <numeric>
#include <stdexcept>

void Population::update(const Solution &newSolution,
                        int objValue,
                        int num_idle_generations,
                        bool verbose)
{
    // Create a new individual and assign a unique ID
    Item newItem(newSolution, objValue, 0.0, nextItemId_++);

    // Store only similarity values and IDs to reduce memory usage
    for (auto &item : population_)
    {
        double similarity = computeSimilarity(item.solution, newSolution);
        // The new individual records similarity with existing individuals
        newItem.similarity.push_back({similarity, item.id});
        // Existing individuals record similarity with the new individual
        item.similarity.push_back({similarity, newItem.id});
    }

    population_.push_back(newItem);
    removeWorstSolution();

    if (isVariablePopulation_
        && num_idle_generations > 0
        && num_idle_generations % maxIdleGens_ == 0
        && static_cast<int>(population_.size()) < maxPopSize_)
    {
        if (verbose)
        {
            std::cout << "----------------Expanding population due to idle "
                         "steps----------------"
                      << std::endl;
        }
        expand();
    }
    else if (isVariablePopulation_
             && num_idle_generations > 0
             && num_idle_generations % maxIdleGens_ == 0
             && static_cast<int>(population_.size()) >= maxPopSize_)
    {
        if (verbose)
        {
            std::cout << "----------------Rebuilding population due to size "
                         "limit----------------"
                      << std::endl;
        }
        rebuild();
    }
}

void Population::add(const Solution &newSolution, int objValue)
{
    Solution solution = newSolution;
    Item item(solution, objValue, 0.0, nextItemId_++);

    for (auto &otherItem : population_)
    {
        double similarity = computeSimilarity(item.solution, otherItem.solution);
        // Store only similarity values and IDs, not full Solution objects
        item.similarity.push_back({similarity, otherItem.id});
        otherItem.similarity.push_back({similarity, item.id});
    }

    population_.push_back(item);
}

void Population::removeWorstSolution()
{
    updateFitness();
    auto worstIt = std::max_element(population_.begin(),
                                    population_.end(),
                                    [](const Item &a, const Item &b)
                                    { return a.fitness < b.fitness; });

    // Get the ID of the individual being removed
    size_t worstId = worstIt->id;

    // Remove references to the removed individual from similarity vectors of all other individuals
    for (auto &item : population_)
    {
        if (item.id != worstId)
        {
            auto &similarity = item.similarity;
            // Remove similarity records by ID, which is more efficient than comparing Solution objects
            similarity.erase(
                std::remove_if(
                    similarity.begin(),
                    similarity.end(),
                    [worstId](const auto &pair)
                    { return pair.second == worstId; }),
                similarity.end());
        }
    }

    population_.erase(worstIt);
}

void Population::updateFitness()
{
    const size_t popSize = population_.size();
    if (popSize <= 1)
    {

        if (popSize == 1)
        {
            population_[0].fitness = 0.0;
        }
        return;
    }

    std::vector<double> costs(popSize);
    std::vector<double> diversityScores(popSize);

    for (size_t i = 0; i < popSize; i++)
    {

        costs[i] = population_[i].objValue;

        const auto &similarities = population_[i].similarity;

        if (!similarities.empty())
        {
            // Only need to process similarity values; no need to access Solution objects
            double sumSimilarity = 0.0;
            for (const auto &[similarity, _] : similarities)
            {
                sumSimilarity += similarity;
            }
            diversityScores[i] = sumSimilarity / similarities.size();
        }
        else
        {
            diversityScores[i] = 0.0;
        }
    }

    auto calculateRanks
        = [](const std::vector<double> &values) -> std::vector<int>
    {
        const size_t n = values.size();

        std::vector<size_t> indices(n);
        std::iota(indices.begin(), indices.end(), 0);

        std::stable_sort(indices.begin(),
                         indices.end(),
                         [&values](size_t i1, size_t i2)
                         {
                             if (values[i1] != values[i2])
                             {
                                 return values[i1] < values[i2];
                             }

                             return i1 < i2;
                         });

        std::vector<int> ranks(n);
        for (size_t i = 0; i < n; i++)
        {
            ranks[indices[i]] = static_cast<int>(i + 1);
        }
        return ranks;
    };

    std::vector<int> costRanks = calculateRanks(costs);
    std::vector<int> diversityRanks = calculateRanks(diversityScores);

    for (size_t i = 0; i < popSize; i++)
    {
        population_[i].fitness
            = ALPHA * costRanks[i] + (1.0 - ALPHA) * diversityRanks[i];
    }
}

bool Population::isDuplicate(const Solution &solution) const
{

    for (const auto &item : population_)
    {
        if (item.solution == solution)
        {
            return true;
        }
    }
    return false;
}

std::tuple<Solution, Solution, Solution>
Population::getAllThreeSolutions() const
{
    if (population_.size() != 3)
    {
        throw std::runtime_error("Population size must be 3 to return all three solutions");
    }

    return std::make_tuple(
        population_[0].solution, population_[1].solution, population_[2].solution);
}

const Population::Item &Population::getBestItem() const
{

    return *std::min_element(population_.begin(),
                            population_.end(),
                            [](const Item &a, const Item &b)
                            { return a.objValue < b.objValue; });
}

std::pair<Solution, int> Population::generateNonDuplicateSolution()
{

    static int seedCounter = 1000;
    int deterministicSeed = seedCounter++;

    auto newGraph = originalGraph_.getRandomFeasibleGraph();

    Search ls(*newGraph, deterministicSeed);

    ls.setStrategy(search_);

    SearchResult result = ls.run();

    int attempts = 0;
    const int MAX_ATTEMPTS = 10;

    while (isDuplicate(newGraph->getRemovedNodes()) && attempts < MAX_ATTEMPTS)
    {
        if (FILE* dbg = std::fopen("/tmp/pycnp_debug.log", "a")) { std::fprintf(dbg, "[DEBUG] duplicate solution detected in generateNonDuplicateSolution attempts=%d\n", attempts); std::fclose(dbg); }

        Node addedNode;
        if (originalGraph_.isDCNP())
        {
            addedNode = newGraph->findBestNodeToAdd();
        }
        else
        {
            addedNode = newGraph->greedySelectNodeToAdd();
        }
        newGraph->addNode(addedNode);

        auto removedNode = newGraph->randomSelectNodeToRemove();
        newGraph->removeNode(removedNode);
        attempts++;
    }

    Solution solution = newGraph->getRemovedNodes();
    int objValue = newGraph->getObjectiveValue();

    return std::make_pair(solution, objValue);
}

void Population::expand()
{
    const size_t newSize = population_.size() + increasePopSize_;
    population_.reserve(newSize);

    while (population_.size() < newSize)
    {
        auto [solution, objValue] = generateNonDuplicateSolution();
        add(solution, objValue);
    }
}

void Population::rebuild()
{
    // Use a reference to avoid copying, then create a new Item (assigning a new ID)
    const Item &bestItemRef = getBestItem();
    Item bestItem(bestItemRef.solution, bestItemRef.objValue, bestItemRef.fitness, nextItemId_++);
    // Do not copy the similarity vector; let it be rebuilt
    population_.clear();
    population_.reserve(initPopSize_);  // Reserve space for the initial population size
    population_.push_back(std::move(bestItem));
    population_[0].similarity.clear();

    auto [solution, objValue] = generateNonDuplicateSolution();
    add(solution, objValue);
}

std::pair<Solution, int>
Population::initialize(bool display,
                    std::function<bool(int)> stopping_criterion)
{
    population_.clear();

    for (int i = 0; i < initPopSize_; ++i)
    {
        auto [newSolution, objValue] = generateNonDuplicateSolution();

        if (stopping_criterion and stopping_criterion(objValue))
        {
            if (display)
            {
                std::cout << "Stopping criterion met during initialization."
                        << std::endl;
            }
            return {newSolution, objValue};
        }

        add(newSolution, objValue);
    }

    const auto &bestItem = getBestItem();
    return {bestItem.solution, bestItem.objValue};
}


std::pair<Solution, Solution> Population::tournamentSelectTwoSolutions(int k)
{

    k = std::min(k, static_cast<int>(population_.size()));
    if (FILE* dbg = std::fopen("/tmp/pycnp_debug.log", "a")) { std::fprintf(dbg, "[DEBUG] tournamentSelectTwoSolutions popSize=%zu k=%d\n", population_.size(), k); std::fclose(dbg); }

    updateFitness();

    size_t parent1Index = 0;
    {

        std::vector<size_t> candidates;
        candidates.reserve(k);

        for (int i = 0; i < k; ++i)
        {
            size_t candidateIndex = rng_->generateIndex(population_.size());
            candidates.push_back(candidateIndex);
        }

        parent1Index = *std::min_element(
            candidates.begin(),
            candidates.end(),
            [this](size_t i, size_t j)
            { return population_[i].fitness < population_[j].fitness; });
    }

    size_t parent2Index;
    {
        std::vector<size_t> candidates;
        candidates.reserve(k);

        for (int i = 0; i < k; ++i)
        {
            size_t candidateIndex;
            do
            {
                candidateIndex = rng_->generateIndex(population_.size());
            } while (candidateIndex == parent1Index);

            candidates.push_back(candidateIndex);
        }

        parent2Index = *std::min_element(
            candidates.begin(),
            candidates.end(),
            [this](size_t i, size_t j)
            { return population_[i].fitness < population_[j].fitness; });
    }

    return std::make_pair(population_[parent1Index].solution,
                        population_[parent2Index].solution);
}

size_t Population::getSize() const
{
    return population_.size();
}
