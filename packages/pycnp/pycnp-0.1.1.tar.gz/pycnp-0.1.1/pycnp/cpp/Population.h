#pragma once
#include "RandomNumberGenerator.h"
#include "search/Search.h"
#include <chrono>
#include <functional>
#include <memory>
#include <vector>
class Graph;

/**
 * Population
 *
 * Manages population of solutions for memetic algorithm.
 *
 * The Population class handles evolutionary operations:
 *
 * - Initialization of diverse solutions using local search
 * - Parent selection via tournament selection
 * - Solution evaluation based on fitness (cost + diversity)
 * - Population updates maintaining quality and diversity
 * - Optional adaptive population sizing
 *
 * Fitness is computed as a weighted combination of objective value and
 * Jaccard similarity to existing solutions, promoting both quality and
 * diversity in the population.
 *
 * .. note::
 *     This class is designed for internal use by the memetic algorithm.
 */
class Population
{
private:
    /**
     * Item
     *
     * Internal representation of an individual solution.
     *
     * Each Item stores a solution, its objective value, fitness score,
     * unique identifier, and similarity values to all other solutions.
     */
    struct Item
    {
        Solution solution;           ///< The solution (set of nodes to remove)
        int objValue;                ///< Objective value (connectivity after removal)
        double fitness;              ///< Combined fitness score
        size_t id;                   ///< Unique identifier for this individual
        // Store similarity values and corresponding individual IDs to reduce memory usage
        using Similarity = std::vector<std::pair<double, size_t>>;
        Similarity similarity;       ///< Similarity values to other solutions

        Item(Solution sol, int obj, double fit, size_t item_id)
            : solution(std::move(sol)), objValue(obj), fitness(fit), id(item_id)
        {
            similarity.reserve(SIMILARITY_RESERVE_SIZE);  // Reserve initial capacity
        }

        Item(const Item&) = default;
        Item(Item&&) = default;
        Item& operator=(const Item&) = default;
        Item& operator=(Item&&) = default;
    };

    Graph &originalGraph_;                     ///< Reference to the original graph
    std::vector<Item> population_;             ///< Current population of solutions
    std::unique_ptr<RandomNumberGenerator> rng_;  ///< Random number generator
    int initPopSize_;                          ///< Initial population size
    bool isVariablePopulation_;                ///< Whether adaptive sizing is enabled
    std::string search_;                       ///< Search strategy name
    // Variable population parameters
    int maxPopSize_ = 20;                      ///< Maximum population size
    int increasePopSize_ = 3;                  ///< Number of individuals to add when expanding
    int maxIdleGens_ = 20;                     ///< Idle generations before triggering expansion
    mutable size_t nextItemId_ = 0;            ///< Unique ID counter for new individuals

    static constexpr double ALPHA = 0.60;     ///< Fitness weight: (1-α)*cost + α*diversity
    static constexpr size_t SIMILARITY_RESERVE_SIZE = 30;  ///< Preallocated similarity capacity

    /// Updates the fitness values of all individuals based on cost and diversity
    void updateFitness();

    /// Removes the worst solution from the population (typically lowest fitness)
    void removeWorstSolution();

    /**
     * Compute Jaccard similarity between two solutions.
     *
     * Parameters
     * ----------
     * sol1 : Solution
     *     First solution
     * sol2 : Solution
     *     Second solution
     *
     * Returns
     * -------
     * float
     *     Similarity value in [0, 1], calculated as |intersection| / |union|
     */
    double computeSimilarity(const Solution &sol1, const Solution &sol2) const
    {
        // Calculate Jaccard similarity between two solutions
        int intersection = 0;
        for (auto node : sol1)
        {
            if (sol2.find(node) != sol2.end())
            {
                intersection++;
            }
        }
        return static_cast<double>(intersection)
            / (sol1.size() + sol2.size() - intersection);
    }

public:
    /**
     * Construct a Population instance.
     *
     * Parameters
     * ----------
     * originalGraph : Graph
     *     Reference to the graph problem
     * search : str
     *     Search strategy name (CBNS, CHNS, DLAS, or BCLS)
     * is_pop_variable : bool
     *     Whether adaptive population sizing is enabled
     * initial_pop_size : int
     *     Initial population size
     * max_pop_size : int
     *     Maximum population size
     * increase_pop_size : int
     *     Number of individuals to add when expanding
     * max_idle_gens : int
     *     Idle generations before triggering expansion
     * seed : int
     *     Random seed for reproducibility
     */
    Population(Graph &originalGraph,
            const std::string &search,
            bool is_pop_variable,
            int initial_pop_size,
            int max_pop_size,
            int increase_pop_size,
            int max_idle_gens,
            int seed)
        : originalGraph_(originalGraph),
          rng_(std::make_unique<RandomNumberGenerator>()),
          maxPopSize_(max_pop_size),
          increasePopSize_(increase_pop_size),
          maxIdleGens_(max_idle_gens)
    {
        rng_->setSeed(seed);
        initPopSize_ = initial_pop_size;
        isVariablePopulation_ = is_pop_variable;
        search_ = search;
    }

    ~Population() = default;

    /**
     * Initialize the population with diverse solutions.
     *
     * Generates initial solutions using local search with random starting points.
     * Ensures diversity by rejecting duplicate solutions during initialization.
     *
     * Parameters
     * ----------
     * display : bool, default=False
     *     Whether to display progress information
     * stopping_criterion : Callable[[int], bool], optional
     *     Optional stopping criterion for initialization
     *
     * Returns
     * -------
     * Tuple[Solution, int]
     *     Pair of (best initial solution, its objective value)
     */
    std::pair<Solution, int>
    initialize(bool display = false,
            std::function<bool(int)> stopping_criterion = nullptr);

    /**
     * Update population with a new offspring solution.
     *
     * Evaluates the new solution and updates the population if the solution
     * is sufficiently good or diverse. May expand population if enabled
     * and no progress has been made.
     *
     * Parameters
     * ----------
     * solution : Solution
     *     The offspring solution
     * objValue : int
     *     Objective value of the offspring
     * num_idle_generations : int
     *     Number of generations without improvement
     * verbose : bool, default=False
     *     Whether to print detailed information
     */
    void update(const Solution &solution,
                int objValue,
                int num_idle_generations,
                bool verbose = false);

    /**
     * Add a solution directly to the population.
     *
     * Parameters
     * ----------
     * solution : Solution
     *     The solution to add
     * objValue : int
     *     Objective value of the solution
     */
    void add(const Solution &solution, int objValue);

    /**
     * Select two parent solutions using tournament selection.
     *
     * Performs k-ary tournament selection twice to choose two distinct parents.
     * Higher fitness solutions are more likely to be selected.
     *
     * Parameters
     * ----------
     * k : int, default=2
     *     Tournament size
     *
     * Returns
     * -------
     * Tuple[Solution, Solution]
     *     Pair of (first parent, second parent) as solution sets
     */
    std::pair<Solution, Solution> tournamentSelectTwoSolutions(int k = 2);

    /**
     * Get up to three prominent solutions from the population.
     *
     * Returns the best solution and two diverse alternatives.
     * Used by the IRR crossover operator which requires three parents.
     *
     * Returns
     * -------
     * Tuple[Solution, Solution, Solution]
     *     Tuple of (solution1, solution2, solution3)
     */
    std::tuple<Solution, Solution, Solution> getAllThreeSolutions() const;

    /**
     * Get the best individual in the population.
     *
     * Returns
     * -------
     * Item
     *     Const reference to the best Item
     */
    const Item &getBestItem() const;

    /**
     * Check if a solution already exists in the population.
     *
     * Parameters
     * ----------
     * solution : Solution
     *     The solution to check
     *
     * Returns
     * -------
     * bool
     *     True if an identical solution is in the population
     */
    bool isDuplicate(const Solution &solution) const;

    /**
     * Get the current population size.
     *
     * Returns
     * -------
     * int
     *     Number of solutions in the population
     */
    size_t getSize() const;

    /**
     * Generate a new solution that is not a duplicate.
     *
     * Creates random solutions and checks for duplicates against the
     * existing population. Used during population initialization.
     *
     * Returns
     * -------
     * Tuple[Solution, int]
     *     Pair of (new solution, its objective value)
     */
    std::pair<Solution, int> generateNonDuplicateSolution();

    /**
     * Expand the population with new diverse solutions.
     *
     * Adds new individuals when the population has stagnated.
     * Called automatically when variable population sizing is enabled
     * and no improvement is observed.
     */
    void expand();

    /**
     * Rebuild the population from scratch.
     *
     * Clears and reinitializes the population with new random solutions.
     * Used as a diversification mechanism when search is stuck.
     */
    void rebuild();
};
