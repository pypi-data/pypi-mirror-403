
// Auto-generated during compilation. Do not edit.

#define __EXPAND(x) x
#define __COUNT(_1, _2, _3, _4, _5, _6, _7, COUNT, ...) COUNT
#define __VA_SIZE(...) __EXPAND(__COUNT(__VA_ARGS__, 7, 6, 5, 4, 3, 2, 1, 0))
#define __CAT1(a, b) a ## b
#define __CAT2(a, b) __CAT1(a, b)
#define __DOC1(n1) PYCNP_doc_##n1
#define __DOC2(n1, n2) PYCNP_doc_##n1##_##n2
#define __DOC3(n1, n2, n3) PYCNP_doc_##n1##_##n2##_##n3
#define __DOC4(n1, n2, n3, n4) PYCNP_doc_##n1##_##n2##_##n3##_##n4
#define __DOC5(n1, n2, n3, n4, n5) PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5
#define __DOC6(n1, n2, n3, n4, n5, n6)     PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5##_##n6
#define __DOC7(n1, n2, n3, n4, n5, n6, n7)     PYCNP_doc_##n1##_##n2##_##n3##_##n4##_##n5##_##n6##_##n7
#define DOC(...)     __EXPAND(__EXPAND(__CAT2(__DOC, __VA_SIZE(__VA_ARGS__)))(__VA_ARGS__))
#define DOC_IMPL(...) DOC(__VA_ARGS__)

#if defined(__GNUG__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
#endif

static char const *PYCNP_doc_Population = R"doc(
Population

Manages population of solutions for memetic algorithm.

The Population class handles evolutionary operations:

- Initialization of diverse solutions using local search
- Parent selection via tournament selection
- Solution evaluation based on fitness (cost + diversity)
- Population updates maintaining quality and diversity
- Optional adaptive population sizing

Fitness is computed as a weighted combination of objective value and
Jaccard similarity to existing solutions, promoting both quality and
diversity in the population.

.. note::
    This class is designed for internal use by the memetic algorithm.
)doc";
static char const *PYCNP_doc_Population_Item = R"doc(
Item

Internal representation of an individual solution.

Each Item stores a solution, its objective value, fitness score,
unique identifier, and similarity values to all other solutions.

Attributes
----------
solution : Solution
    The solution (set of nodes to remove)
obj_value : int
    Objective value (connectivity after removal)
fitness : float
    Combined fitness score
id : int
    Unique identifier for this individual
similarity : List[Tuple[float, int]]
    Similarity values to other solutions
)doc";
static char const *PYCNP_doc_Population_removeWorstSolution_setSeed = R"doc(
Construct a Population instance.

Parameters
----------
originalGraph : Graph
    Reference to the graph problem
search : str
    Search strategy name (CBNS, CHNS, DLAS, or BCLS)
is_pop_variable : bool
    Whether adaptive population sizing is enabled
initial_pop_size : int
    Initial population size
max_pop_size : int
    Maximum population size
increase_pop_size : int
    Number of individuals to add when expanding
max_idle_gens : int
    Idle generations before triggering expansion
seed : int
    Random seed for reproducibility
)doc";
static char const *PYCNP_doc_Population_update = R"doc(
Update population with a new offspring solution.

Evaluates the new solution and updates the population if the solution
is sufficiently good or diverse. May expand population if enabled
and no progress has been made.

Parameters
----------
solution : Solution
    The offspring solution
objValue : int
    Objective value of the offspring
num_idle_generations : int
    Number of generations without improvement
verbose : bool, default=False
    Whether to print detailed information
)doc";
static char const *PYCNP_doc_Population_add = R"doc(
Add a solution directly to the population.

Parameters
----------
solution : Solution
    The solution to add
objValue : int
    Objective value of the solution
)doc";
static char const *PYCNP_doc_Population_tournamentSelectTwoSolutions = R"doc(
Select two parent solutions using tournament selection.

Performs k-ary tournament selection twice to choose two distinct parents.
Higher fitness solutions are more likely to be selected.

Parameters
----------
k : int, default=2
    Tournament size

Returns
-------
Tuple[Solution, Solution]
    Pair of (first parent, second parent) as solution sets
)doc";
static char const *PYCNP_doc_Population_getAllThreeSolutions = R"doc(
Get up to three prominent solutions from the population.

Returns the best solution and two diverse alternatives.
Used by the IRR crossover operator which requires three parents.

Returns
-------
Tuple[Solution, Solution, Solution]
    Tuple of (solution1, solution2, solution3)
)doc";
static char const *PYCNP_doc_Population_getBestItem = R"doc(
Get the best individual in the population.

Returns
-------
Item
    Const reference to the best Item
)doc";
static char const *PYCNP_doc_Population_isDuplicate = R"doc(
Check if a solution already exists in the population.

Parameters
----------
solution : Solution
    The solution to check

Returns
-------
bool
    True if an identical solution is in the population
)doc";
static char const *PYCNP_doc_Population_getSize = R"doc(
Get the current population size.

Returns
-------
int
    Number of solutions in the population
)doc";
static char const *PYCNP_doc_Population_generateNonDuplicateSolution = R"doc(
Generate a new solution that is not a duplicate.

Creates random solutions and checks for duplicates against the
existing population. Used during population initialization.

Returns
-------
Tuple[Solution, int]
    Pair of (new solution, its objective value)
)doc";
static char const *PYCNP_doc_Population_expand = R"doc(
Expand the population with new diverse solutions.

Adds new individuals when the population has stagnated.
Called automatically when variable population sizing is enabled
and no improvement is observed.
)doc";
static char const *PYCNP_doc_Population_rebuild = R"doc(
Rebuild the population from scratch.

Clears and reinitializes the population with new random solutions.
Used as a diversification mechanism when search is stuck.
)doc";
static char const *PYCNP_doc_SearchResult = R"doc(
SearchResult

Result container for search algorithms.

Stores the outcome of a search algorithm, including the found solution
and its objective value. Supports move semantics for efficiency.

Attributes
----------
solution
    Found solution, represented as a set of nodes.
obj_value
    Objective value of the solution.
)doc";
static char const *PYCNP_doc_RandomNumberGenerator = R"doc(
RandomNumberGenerator

Random number generator class wrapping a Mersenne Twister engine.

Provides methods to generate probability values, integers, indices and
boolean values, supplying high-quality randomness for the algorithms.
)doc";
static char const *PYCNP_doc_RandomNumberGenerator_RandomNumberGenerator_seed = R"doc(
Set the random seed.

Parameters
----------
seed
    Seed value used to initialize the random number generator.
)doc";
static char const *PYCNP_doc_RandomNumberGenerator_seed_dist = R"doc(
Generate a random probability value.

Returns
-------
double
    The generated random probability value.
)doc";
static char const *PYCNP_doc_RandomNumberGenerator_dist_dist_std_invalid_argument = R"doc(
Generate a random integer in range [min, max].

Parameters
----------
min : int
    The minimum value of the random integer (inclusive).
max : int
    The maximum value of the random integer (inclusive).

Returns
-------
int
    The generated random integer.

Raises
------
std::invalid_argument
    If min > max.
)doc";
static char const *PYCNP_doc_RandomNumberGenerator_dist_dist_std_invalid_argument_2 = R"doc(
Generate a random index in range [0, max-1].

Parameters
----------
max : int
    The upper budget for the index (exclusive). Must be positive.

Returns
-------
int
    The generated random index.

Throws
------
std::invalid_argument
    If max <= 0.
)doc";
static char const *PYCNP_doc_ProblemData = R"doc(
ProblemData

Stores the data for a graph problem instance.

Contains node information, adjacency list, and provides methods to create graph objects.
)doc";
static char const *PYCNP_doc_ProblemData_ProblemData = R"doc(
Creates a ProblemData instance with the specified number of nodes.

Parameters
----------
num : int
    The number of nodes.
)doc";
static char const *PYCNP_doc_ProblemData_readFromAdjacencyListFile = R"doc(
Reads problem data from an adjacency list format file.

Adjacency list format: each line represents a node and its neighbors.

Parameters
----------
filename : str
    Path to the adjacency list file.

Returns
-------
ProblemData
    The loaded problem data.
)doc";
static char const *PYCNP_doc_ProblemData_readFromEdgeListFormat = R"doc(
Reads problem data from an edge list format file.

Edge list format: contains a header line with node/edge counts,
followed by edge definitions.

Parameters
----------
filename : str
    Path to the edge list file.

Returns
-------
ProblemData
    The loaded problem data.
)doc";
static char const *PYCNP_doc_ProblemData_numNodes = R"doc(
Returns the number of nodes in the problem data.

Returns
-------
int
    Number of nodes.
)doc";
static char const *PYCNP_doc_ProblemData_getNodesSet = R"doc(
Returns the set of all nodes.

Returns
-------
NodeSet
    Set of node IDs.
)doc";
static char const *PYCNP_doc_ProblemData_getAdjList = R"doc(
Returns the adjacency list representation of the graph.

Returns
-------
vector<NodeSet>
    Adjacency list where each index contains the neighbors of that node.
)doc";
static char const *PYCNP_doc_ProblemData_addNode = R"doc(
Adds a node to the problem data.

Parameters
----------
node : Node
    The ID of the node to add.
)doc";
static char const *PYCNP_doc_ProblemData_addEdge = R"doc(
Adds an edge between two nodes.

Parameters
----------
u : Node
    The ID of the first node.
v : Node
    The ID of the second node.
)doc";
static char const *PYCNP_doc_ProblemData_createOriginalGraph = R"doc(
Creates an original graph from the problem data.

Parameters specify the problem type, number of nodes to remove, seed, and hop distance.

Parameters
----------
problemType : str
    The type of problem ("CNP" or "DCNP").
numToRemove : int
    The number of nodes to remove.
seed : int
    Random seed for reproducibility.
hop_distance : int
    Maximum hop distance for DCNP.

Returns
-------
Graph
    A unique pointer to the created graph.
)doc";
static char const *PYCNP_doc_Component = R"doc(
Represents a connected component in the graph.
)doc";
static char const *PYCNP_doc_Graph = R"doc(
Graph

Lightweight wrapper over concrete graph implementations (CNP_Graph / DCNP_Graph).
)doc";
static char const *PYCNP_doc_CNP_Graph = R"doc(
CNP_Graph

Graph implementation for the Critical Node Problem (CNP).

Represents a graph where the objective is to minimize connectivity after node removal.
)doc";
static char const *PYCNP_doc_CNP_Graph_clone = R"doc(
Creates a deep copy of the graph.

Returns
-------
CNP_Graph
    A new graph instance with the same structure.
)doc";
static char const *PYCNP_doc_CNP_Graph_updateGraphByRemovedNodes = R"doc(
Updates the graph to reflect node removals.

Parameters
----------
removedNodes : NodeSet
    Set of nodes that have been removed.
)doc";
static char const *PYCNP_doc_CNP_Graph_getReducedGraphByRemovedNodes = R"doc(
Creates a reduced graph after node removal.

Parameters
----------
nodesToRemove : NodeSet
    Set of nodes to remove.

Returns
-------
CNP_Graph
    The reduced graph.
)doc";
static char const *PYCNP_doc_CNP_Graph_addNode = R"doc(
Adds a node back to the graph.

Parameters
----------
node : Node
    The node to add.
)doc";
static char const *PYCNP_doc_CNP_Graph_removeNode = R"doc(
Removes a node from the graph.

Parameters
----------
node : Node
    The node to remove.
)doc";
static char const *PYCNP_doc_CNP_Graph_isNodeRemoved = R"doc(
Checks if a node has been removed.

Parameters
----------
node : Node
    The node to check.

Returns
-------
bool
    True if the node has been removed.
)doc";
static char const *PYCNP_doc_CNP_Graph_getNumNodes = R"doc(
Returns the total number of nodes in the graph.

Returns
-------
int
    Number of nodes.
)doc";
static char const *PYCNP_doc_CNP_Graph_getRemovedNodes = R"doc(
Returns the set of removed nodes.

Returns
-------
NodeSet
    Set of nodes that have been removed.
)doc";
static char const *PYCNP_doc_CNP_Graph_setNodeAge = R"doc(
Sets the age of a node.

Parameters
----------
node : Node
    The node.
age : Age
    The age value.
)doc";
static char const *PYCNP_doc_CNP_Graph_getObjectiveValue = R"doc(
Calculates the objective value (connectivity) of the graph.

Returns
-------
int
    The connectivity after node removal.
)doc";
static char const *PYCNP_doc_DCNP_Graph = R"doc(
DCNP_Graph

Graph implementation for the Distance-Based Critical Node Problem (DCNP).

Represents a graph where the objective is to maximize pairwise distance after node removal.
)doc";
static char const *PYCNP_doc_DCNP_Graph_bfsKTree = R"doc(
K-hop tree sizes for each node.
`treeSize[v]` is total nodes reachable from `v` within K hops.
)doc";
static char const *PYCNP_doc_DCNP_Graph_updateGraphByRemovedNodes = R"doc(
Updates the graph to reflect node removals for DCNP.

Parameters
----------
nodesToRemove : NodeSet
    Set of nodes that have been removed.
)doc";
static char const *PYCNP_doc_DCNP_Graph_getReducedGraphByRemovedNodes = R"doc(
Creates a reduced graph after node removal for DCNP.

Parameters
----------
nodesToRemove : NodeSet
    Set of nodes to remove.

Returns
-------
DCNP_Graph
    The reduced graph.
)doc";
static char const *PYCNP_doc_DCNP_Graph_removeNode = R"doc(
Removes a node from the DCNP graph.

Parameters
----------
node : Node
    The node to remove.
)doc";
static char const *PYCNP_doc_DCNP_Graph_addNode = R"doc(
Adds a node back to the DCNP graph.

Parameters
----------
node : Node
    The node to add.
)doc";
static char const *PYCNP_doc_DCNP_Graph_setNodeAge = R"doc(
Sets the age of a node in the DCNP graph.

Parameters
----------
node : Node
    The node.
age : Age
    The age value.
)doc";
static char const *PYCNP_doc_DCNP_Graph_isNodeRemoved = R"doc(
Checks if a node has been removed from the DCNP graph.

Parameters
----------
node : Node
    The node to check.

Returns
-------
bool
    True if the node has been removed.
)doc";
static char const *PYCNP_doc_DCNP_Graph_getRemovedNodes = R"doc(
Returns the set of removed nodes for DCNP.

Returns
-------
NodeSet
    Set of nodes that have been removed.
)doc";
static char const *PYCNP_doc_DCNP_Graph_getNumNodes = R"doc(
Returns the total number of nodes in the DCNP graph.

Returns
-------
int
    Number of nodes.
)doc";
static char const *PYCNP_doc_DCNP_Graph_getObjectiveValue = R"doc(
Calculates the objective value (pairwise distance) for DCNP.

Returns
-------
int
    The pairwise distance after node removal.
)doc";
static char const *PYCNP_doc_DLASStrategy = R"doc(
DLASStrategy

Diversified Late Acceptance Search strategy.

DLAS (Diversified Late Acceptance Search) strategy uses historical cost
acceptance criteria to search for optimal solutions.
)doc";
static char const *PYCNP_doc_DLASStrategy_DLASStrategy = R"doc(
Constructor.

Parameters
----------
graph
    Reference to the graph object.
params
    Algorithm parameters.
)doc";
static char const *PYCNP_doc_DLASStrategy_execute = R"doc(
Execute DLAS search algorithm.

Returns
-------
SearchResult
    Search result.
)doc";
static char const *PYCNP_doc_DLASStrategy_performMove = R"doc(
Perform a move operation.

Parameters
----------
currentGraph
    Current graph object.
currentObjValue
    Current objective function value, will be updated.
historyCost
    Historical cost array.
maxCost
    Maximum historical cost.
numMaxCost
    Number of occurrences of maximum cost.
numSteps
    Current step number.
)doc";
static char const *PYCNP_doc_SearchStrategy = R"doc(
SearchStrategy

Search strategy interface.

All concrete search algorithms need to implement this interface.
)doc";
static char const *PYCNP_doc_BCLSStrategy = R"doc(
BCLSStrategy

Betweenness centrality-based late-acceptance search strategy.

BCLS (Betweenness centrality-based late-acceptance search) strategy
uses node betweenness centrality to guide the search.
)doc";
static char const *PYCNP_doc_BCLSStrategy_BCLSStrategy = R"doc(
Constructor.

Parameters
----------
graph
    Reference to the graph object.
params
    Algorithm parameters.
)doc";
static char const *PYCNP_doc_BCLSStrategy_execute = R"doc(
Execute BCLS search algorithm.

Returns
-------
SearchResult
    Search result.
)doc";
static char const *PYCNP_doc_BCLSStrategy_performMove = R"doc(
Perform one move operation.

Parameters
----------
currentGraph
    Current graph object.
currentObjValue
    Current objective function value, will be updated.
candidateNodes
    List of candidate nodes.
it_5
    Iterator pointing to the 5th element in the candidate nodes list.
)doc";
static char const *PYCNP_doc_BCLSStrategy_updateIteratorTo5th = R"doc(
Update iterator pointing to the 5th (or last) candidate node.
)doc";
static char const *PYCNP_doc_CBNSStrategy = R"doc(
CBNSStrategy

Component-based Neighborhood Search strategy.

CBNS (Component-Based Neighborhood Search) strategy searches for optimal
solutions by operating on connected components of the graph.
)doc";
static char const *PYCNP_doc_CBNSStrategy_CBNSStrategy = R"doc(
Constructor.

Parameters
----------
graph
    Reference to the graph object.
params
    Algorithm parameters.
)doc";
static char const *PYCNP_doc_CBNSStrategy_execute = R"doc(
Execute CBNS search algorithm.

Returns
-------
SearchResult
    Search result.
)doc";
static char const *PYCNP_doc_CBNSStrategy_performMove = R"doc(
Perform one move operation.

Parameters
----------
currentGraph
    Current graph object.
currentObjValue
    Current objective function value, will be updated.
numSteps
    Current step count.
)doc";
static char const *PYCNP_doc_Search = R"doc(
Search

Manages and executes various search algorithms.

This class uses the strategy pattern to implement management and execution
of different search algorithms, supporting multiple search strategies such as
CBNS (Component-based Neighborhood Search), DLAS (Dynamic Late Acceptance Search),
CHNS (Component-based Hybrid Neighborhood Search), and BCLS (Betweenness
centrality-based Late-acceptance Search).
)doc";
static char const *PYCNP_doc_Search_Search = R"doc(
Constructor with seed.

Parameters
----------
graph
    Reference to the graph object for search algorithm computation.
seed
    Random number seed.
)doc";
static char const *PYCNP_doc_Search_Search_2 = R"doc(
Destructor.
)doc";
static char const *PYCNP_doc_Search_setStrategy = R"doc(
Set search strategy.

Parameters
----------
strategyName
    Strategy name, such as "CBNS", "DLAS", "CHNS", or "BCLS".

Throws
------
std::invalid_argument
    If strategy name does not exist.
)doc";
static char const *PYCNP_doc_Search_run = R"doc(
Run search algorithm.

Returns
-------
SearchResult
    Search result containing optimal solution and objective function value.

Throws
------
std::runtime_error
    If search strategy is not set.
)doc";
static char const *PYCNP_doc_Search_registerStrategies = R"doc(
Register all available search strategies.
)doc";
static char const *PYCNP_doc_CHNSStrategy = R"doc(
CHNSStrategy

Component-based Hybrid Neighborhood Search strategy.

CHNS (Component-Based Hybrid Neighborhood Search) strategy combines
two heuristic methods for search.
)doc";
static char const *PYCNP_doc_CHNSStrategy_CHNSStrategy = R"doc(
Constructor.

Parameters
----------
graph
    Reference to the graph object.
params
    Algorithm parameters.
)doc";
static char const *PYCNP_doc_CHNSStrategy_execute = R"doc(
Execute CHNS search algorithm.

Returns
-------
SearchResult
    Search result.
)doc";
static char const *PYCNP_doc_CHNSStrategy_performMove = R"doc(
Perform one move operation.

Parameters
----------
currentGraph
    Current graph object.
currentObjValue
    Current objective function value, will be updated.
numSteps
    Current step count.
)doc";
static char const *PYCNP_doc_inherit_repair_recombination = R"doc(
@brief Inherit-Repair-Recombination (IRR) crossover operator.

Uses three parents to create offspring through a process of inheritance
followed by repair operations to maintain feasibility.

@param originalGraph The original problem graph.
@param parents Tuple of three parent solutions.
@param seed Random seed for the operation.
@return Unique pointer to the new offspring graph.
)doc";
static char const *PYCNP_doc_doubleBackboneBasedCrossover = R"doc(
@brief Double Backbone Based (DBX) crossover operator.

Identifies common nodes between parent solutions (the "backbone") and
constructs an offspring by preserving these common nodes and probabilistically
inheriting others.

@param originalGraph The original problem graph.
@param parents Pair of parent solutions to cross over.
@param seed Random seed for the operation.
@return Unique pointer to the new offspring graph.
)doc";
static char const *PYCNP_doc_reduceSolveCombine = R"doc(
@brief Reduce-Solve-Combine (RSC) crossover operator.

Reduces common nodes between parents, solves the reduced subproblem
via local search, and combines the results to form an offspring.

@param originalGraph The original problem graph.
@param parents Pair of parent solutions.
@param search_strategy The local search strategy to use on the subproblem.
@param beta Parameter controlling the reduction intensity.
@param seed Random seed for the operation.
@return Unique pointer to the new offspring graph.
)doc";
static char const *PYCNP_doc_Population_initialize = R"doc(
initialize

Initializes the population with diverse solutions.

Generates initial solutions using local search with random starting points.

Returns
-------
Tuple[Solution, int]
    Pair of (best initial solution, its objective value)
)doc";

#if defined(__GNUG__)
#pragma GCC diagnostic pop
#endif

